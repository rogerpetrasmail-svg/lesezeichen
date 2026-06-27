"""SQLite-Datenzugriffsschicht.

Speichert dauerhaft: RSS-Quellen, Kategorien, Schwerpunkte, Einstellungen
und die analysierten Artikel inklusive der vom Nutzer geschriebenen Scripte.

Die Klasse ist bewusst threadsicher gehalten (eigene Verbindung pro Aufruf
bzw. check_same_thread=False mit Lock), da Hintergrund-Threads schreiben.
"""

from __future__ import annotations

import sqlite3
import threading
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from . import config


class Database:
    def __init__(self, path: Optional[Path] = None) -> None:
        self.path = Path(path) if path else config.database_path()
        self._lock = threading.RLock()
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL;")
        self._conn.execute("PRAGMA foreign_keys=ON;")
        self._create_schema()
        self._seed_defaults()

    # ------------------------------------------------------------------ schema
    def _create_schema(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            cur.executescript(
                """
                CREATE TABLE IF NOT EXISTS settings (
                    key   TEXT PRIMARY KEY,
                    value TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS feeds (
                    id    INTEGER PRIMARY KEY AUTOINCREMENT,
                    url   TEXT NOT NULL UNIQUE,
                    title TEXT NOT NULL DEFAULT ''
                );

                CREATE TABLE IF NOT EXISTS categories (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS focus_areas (
                    id   INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE
                );

                CREATE TABLE IF NOT EXISTS articles (
                    id               INTEGER PRIMARY KEY AUTOINCREMENT,
                    guid             TEXT UNIQUE,
                    titel            TEXT NOT NULL DEFAULT '',
                    kategorie        TEXT NOT NULL DEFAULT '',
                    score            INTEGER NOT NULL DEFAULT 0,
                    schwerpunkt      TEXT NOT NULL DEFAULT '',
                    zusammenfassung  TEXT NOT NULL DEFAULT '',
                    eigenes_script   TEXT NOT NULL DEFAULT '',
                    original_beitrag TEXT NOT NULL DEFAULT '',
                    quelle_url       TEXT NOT NULL DEFAULT '',
                    link             TEXT NOT NULL DEFAULT '',
                    erstellt_am      TEXT NOT NULL DEFAULT ''
                );
                """
            )
            self._conn.commit()

    def _seed_defaults(self) -> None:
        with self._lock:
            cur = self._conn.cursor()
            # Einstellungen
            defaults = {
                "ollama_url": config.DEFAULT_OLLAMA_URL,
                "ollama_model": config.DEFAULT_OLLAMA_MODEL,
                "excel_path": config.DEFAULT_EXCEL_PATH,
                "min_score": "1",
            }
            for k, v in defaults.items():
                cur.execute(
                    "INSERT OR IGNORE INTO settings(key, value) VALUES (?, ?)",
                    (k, v),
                )
            # Kategorien / Schwerpunkte nur befüllen, wenn Tabellen leer sind
            if cur.execute("SELECT COUNT(*) FROM categories").fetchone()[0] == 0:
                for name in config.DEFAULT_CATEGORIES:
                    cur.execute(
                        "INSERT OR IGNORE INTO categories(name) VALUES (?)", (name,)
                    )
            if cur.execute("SELECT COUNT(*) FROM focus_areas").fetchone()[0] == 0:
                for name in config.DEFAULT_FOCUS_AREAS:
                    cur.execute(
                        "INSERT OR IGNORE INTO focus_areas(name) VALUES (?)", (name,)
                    )
            self._conn.commit()

    # ---------------------------------------------------------------- settings
    def get_setting(self, key: str, default: str = "") -> str:
        with self._lock:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        with self._lock:
            self._conn.execute(
                "INSERT INTO settings(key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (key, str(value)),
            )
            self._conn.commit()

    # ------------------------------------------------------------------- feeds
    def list_feeds(self) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(
                "SELECT id, url, title FROM feeds ORDER BY id"
            ).fetchall()

    def add_feed(self, url: str, title: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO feeds(url, title) VALUES (?, ?)",
                (url.strip(), title.strip()),
            )
            self._conn.commit()

    def update_feed(self, feed_id: int, url: str, title: str = "") -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE feeds SET url = ?, title = ? WHERE id = ?",
                (url.strip(), title.strip(), feed_id),
            )
            self._conn.commit()

    def delete_feed(self, feed_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM feeds WHERE id = ?", (feed_id,))
            self._conn.commit()

    # -------------------------------------------------- categories / focus
    def _list_named(self, table: str) -> list[str]:
        with self._lock:
            rows = self._conn.execute(
                f"SELECT name FROM {table} ORDER BY name COLLATE NOCASE"
            ).fetchall()
            return [r["name"] for r in rows]

    def _add_named(self, table: str, name: str) -> None:
        name = name.strip()
        if not name:
            return
        with self._lock:
            self._conn.execute(
                f"INSERT OR IGNORE INTO {table}(name) VALUES (?)", (name,)
            )
            self._conn.commit()

    def _delete_named(self, table: str, name: str) -> None:
        with self._lock:
            self._conn.execute(f"DELETE FROM {table} WHERE name = ?", (name,))
            self._conn.commit()

    def list_categories(self) -> list[str]:
        return self._list_named("categories")

    def add_category(self, name: str) -> None:
        self._add_named("categories", name)

    def delete_category(self, name: str) -> None:
        self._delete_named("categories", name)

    def list_focus_areas(self) -> list[str]:
        return self._list_named("focus_areas")

    def add_focus_area(self, name: str) -> None:
        self._add_named("focus_areas", name)

    def delete_focus_area(self, name: str) -> None:
        self._delete_named("focus_areas", name)

    # ---------------------------------------------------------------- articles
    def article_exists(self, guid: str) -> bool:
        if not guid:
            return False
        with self._lock:
            return (
                self._conn.execute(
                    "SELECT 1 FROM articles WHERE guid = ?", (guid,)
                ).fetchone()
                is not None
            )

    def upsert_article(self, data: dict[str, Any]) -> int:
        """Fügt einen Artikel ein oder aktualisiert ihn (per guid).

        Gibt die Datensatz-ID zurück.
        """
        guid = data.get("guid") or ""
        with self._lock:
            existing = None
            if guid:
                existing = self._conn.execute(
                    "SELECT id FROM articles WHERE guid = ?", (guid,)
                ).fetchone()
            fields = (
                guid,
                data.get("titel", ""),
                data.get("kategorie", ""),
                int(data.get("score", 0) or 0),
                data.get("schwerpunkt", ""),
                data.get("zusammenfassung", ""),
                data.get("eigenes_script", ""),
                data.get("original_beitrag", ""),
                data.get("quelle_url", ""),
                data.get("link", ""),
                data.get("erstellt_am") or datetime.now().isoformat(timespec="seconds"),
            )
            if existing:
                self._conn.execute(
                    """UPDATE articles SET
                        titel = ?, kategorie = ?, score = ?, schwerpunkt = ?,
                        zusammenfassung = ?, original_beitrag = ?, quelle_url = ?,
                        link = ?
                       WHERE id = ?""",
                    (
                        fields[1], fields[2], fields[3], fields[4],
                        fields[5], fields[7], fields[8], fields[9],
                        existing["id"],
                    ),
                )
                self._conn.commit()
                return int(existing["id"])
            cur = self._conn.execute(
                """INSERT INTO articles
                   (guid, titel, kategorie, score, schwerpunkt, zusammenfassung,
                    eigenes_script, original_beitrag, quelle_url, link, erstellt_am)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                fields,
            )
            self._conn.commit()
            return int(cur.lastrowid)

    def update_article_fields(self, article_id: int, **fields: Any) -> None:
        """Aktualisiert beliebige editierbare Felder eines Artikels."""
        allowed = {
            "titel", "kategorie", "score", "schwerpunkt",
            "zusammenfassung", "eigenes_script", "original_beitrag",
        }
        sets, values = [], []
        for key, val in fields.items():
            if key in allowed:
                sets.append(f"{key} = ?")
                values.append(val)
        if not sets:
            return
        values.append(article_id)
        with self._lock:
            self._conn.execute(
                f"UPDATE articles SET {', '.join(sets)} WHERE id = ?", values
            )
            self._conn.commit()

    def list_articles(self) -> list[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(
                "SELECT * FROM articles ORDER BY score DESC, id DESC"
            ).fetchall()

    def get_article(self, article_id: int) -> Optional[sqlite3.Row]:
        with self._lock:
            return self._conn.execute(
                "SELECT * FROM articles WHERE id = ?", (article_id,)
            ).fetchone()

    def delete_article(self, article_id: int) -> None:
        with self._lock:
            self._conn.execute("DELETE FROM articles WHERE id = ?", (article_id,))
            self._conn.commit()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
