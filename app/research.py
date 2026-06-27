"""Hintergrund-Worker für die 1-Klick-Recherche.

Liest alle Feeds, schickt jeden neuen Beitrag an Ollama, parst das JSON und
speichert das Ergebnis in der Datenbank. Läuft in einem QThread, damit die
GUI nicht blockiert. Fortschritt und Ergebnisse werden über Qt-Signale
gemeldet.
"""

from __future__ import annotations

from PySide6.QtCore import QObject, QThread, Signal

from . import config, rss
from .analysis import normalize_result
from .database import Database
from .ollama_client import OllamaClient, OllamaError


class ResearchWorker(QObject):
    """Führt die Recherche aus. In einen QThread verschieben und ``run`` starten."""

    progress = Signal(int, int, str)      # (aktuell, gesamt, statustext)
    article_done = Signal(int)            # Datenbank-ID des neuen Artikels
    log = Signal(str)                     # Log-/Fehlermeldung
    finished = Signal(int, int)           # (verarbeitet, übersprungen)

    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._cancel = False

    def cancel(self) -> None:
        self._cancel = True

    def run(self) -> None:
        processed = 0
        skipped = 0
        try:
            feeds = self.db.list_feeds()
            categories = self.db.list_categories()
            focus_areas = self.db.list_focus_areas()
            model = self.db.get_setting("ollama_model", config.DEFAULT_OLLAMA_MODEL)
            url = self.db.get_setting("ollama_url", config.DEFAULT_OLLAMA_URL)

            client = OllamaClient(base_url=url, model=model)
            if not client.is_available():
                self.log.emit(
                    f"FEHLER: Ollama ist unter {url} nicht erreichbar. "
                    "Läuft die Ollama-Instanz?"
                )
                self.finished.emit(0, 0)
                return

            system_prompt = config.build_system_prompt(categories, focus_areas)

            # Alle Beiträge sammeln
            all_items: list[rss.FeedItem] = []
            for feed in feeds:
                if self._cancel:
                    break
                self.log.emit(f"Lese Feed: {feed['url']}")
                try:
                    items = rss.fetch_feed(feed["url"])
                    all_items.extend(items)
                except Exception as exc:  # noqa: BLE001
                    self.log.emit(f"  Feed-Fehler ({feed['url']}): {exc}")

            # Bereits vorhandene überspringen
            new_items = [i for i in all_items if not self.db.article_exists(i.guid)]
            skipped = len(all_items) - len(new_items)
            total = len(new_items)
            self.log.emit(
                f"{len(all_items)} Beiträge gefunden, {total} neu, "
                f"{skipped} bereits vorhanden."
            )

            for idx, item in enumerate(new_items, start=1):
                if self._cancel:
                    self.log.emit("Recherche abgebrochen.")
                    break
                self.progress.emit(idx, total, f"Analysiere: {item.title[:60]}")
                user_content = (
                    f"TITEL: {item.title}\n\n"
                    f"QUELLE: {item.source_url}\n\n"
                    f"INHALT:\n{item.content[:8000]}"
                )
                try:
                    raw = client.analyze(system_prompt, user_content)
                    result = normalize_result(raw, item)
                    article_id = self.db.upsert_article(result)
                    processed += 1
                    self.article_done.emit(article_id)
                except OllamaError as exc:
                    self.log.emit(f"  KI-Fehler bei '{item.title[:50]}': {exc}")
                except Exception as exc:  # noqa: BLE001
                    self.log.emit(f"  Unerwarteter Fehler: {exc}")

        except Exception as exc:  # noqa: BLE001
            self.log.emit(f"Schwerwiegender Fehler: {exc}")
        finally:
            self.finished.emit(processed, skipped)


def start_research(db: Database) -> tuple[QThread, ResearchWorker]:
    """Erzeugt Thread + Worker und startet die Recherche.

    Der Aufrufer muss Thread und Worker referenzieren, bis ``finished`` kommt.
    """
    thread = QThread()
    worker = ResearchWorker(db)
    worker.moveToThread(thread)
    thread.started.connect(worker.run)
    worker.finished.connect(thread.quit)
    thread.start()
    return thread, worker
