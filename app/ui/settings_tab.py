"""Einstellungen-Tab: RSS-Quellen, Kategorien, Schwerpunkte, Ollama-Modell."""

from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..database import Database
from ..ollama_client import OllamaClient, OllamaError


class _NamedListManager(QGroupBox):
    """Wiederverwendbarer Editor für einfache Namenslisten (Kategorien etc.)."""

    def __init__(self, title: str, loader, adder, deleter) -> None:
        super().__init__(title)
        self._loader = loader
        self._adder = adder
        self._deleter = deleter

        self.list_widget = QListWidget()
        self.input = QLineEdit()
        self.input.setPlaceholderText("Neuen Eintrag eingeben …")
        add_btn = QPushButton("Hinzufügen")
        del_btn = QPushButton("Löschen")
        add_btn.clicked.connect(self._on_add)
        del_btn.clicked.connect(self._on_delete)
        self.input.returnPressed.connect(self._on_add)

        row = QHBoxLayout()
        row.addWidget(self.input)
        row.addWidget(add_btn)
        row.addWidget(del_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self.list_widget)
        layout.addLayout(row)
        self.reload()

    def reload(self) -> None:
        self.list_widget.clear()
        for name in self._loader():
            self.list_widget.addItem(QListWidgetItem(name))

    def _on_add(self) -> None:
        name = self.input.text().strip()
        if name:
            self._adder(name)
            self.input.clear()
            self.reload()

    def _on_delete(self) -> None:
        item = self.list_widget.currentItem()
        if item:
            self._deleter(item.text())
            self.reload()


class SettingsTab(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._build_ui()

    # --------------------------------------------------------------- UI-Aufbau
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # --- Ollama-Konfiguration -----------------------------------------
        ollama_box = QGroupBox("Ollama (lokale KI)")
        ob = QVBoxLayout(ollama_box)

        self.url_input = QLineEdit(self.db.get_setting("ollama_url"))
        self.model_input = QLineEdit(self.db.get_setting("ollama_model"))
        self.excel_input = QLineEdit(self.db.get_setting("excel_path"))

        url_row = QHBoxLayout()
        url_row.addWidget(QLabel("Ollama-URL:"))
        url_row.addWidget(self.url_input)
        test_btn = QPushButton("Verbindung testen")
        test_btn.clicked.connect(self._test_connection)
        url_row.addWidget(test_btn)
        ob.addLayout(url_row)

        model_row = QHBoxLayout()
        model_row.addWidget(QLabel("Modellname:"))
        model_row.addWidget(self.model_input)
        pick_btn = QPushButton("Installierte Modelle …")
        pick_btn.clicked.connect(self._pick_model)
        model_row.addWidget(pick_btn)
        ob.addLayout(model_row)

        excel_row = QHBoxLayout()
        excel_row.addWidget(QLabel("Excel-Exportpfad:"))
        excel_row.addWidget(self.excel_input)
        browse_btn = QPushButton("Durchsuchen …")
        browse_btn.clicked.connect(self._browse_excel)
        excel_row.addWidget(browse_btn)
        ob.addLayout(excel_row)

        save_btn = QPushButton("Einstellungen speichern")
        save_btn.clicked.connect(self._save_settings)
        ob.addWidget(save_btn, alignment=Qt.AlignmentFlag.AlignRight)

        root.addWidget(ollama_box)

        # --- RSS-Feeds -----------------------------------------------------
        self.feeds_box = QGroupBox("RSS-Feeds / Quellen")
        fb = QVBoxLayout(self.feeds_box)
        self.feed_list = QListWidget()
        fb.addWidget(self.feed_list)

        self.feed_input = QLineEdit()
        self.feed_input.setPlaceholderText("https://beispiel.de/feed.xml")
        self.feed_input.returnPressed.connect(self._add_feed)
        feed_btns = QHBoxLayout()
        add_feed_btn = QPushButton("Hinzufügen")
        edit_feed_btn = QPushButton("Bearbeiten")
        del_feed_btn = QPushButton("Löschen")
        add_feed_btn.clicked.connect(self._add_feed)
        edit_feed_btn.clicked.connect(self._edit_feed)
        del_feed_btn.clicked.connect(self._delete_feed)
        feed_btns.addWidget(self.feed_input)
        feed_btns.addWidget(add_feed_btn)
        feed_btns.addWidget(edit_feed_btn)
        feed_btns.addWidget(del_feed_btn)
        fb.addLayout(feed_btns)
        root.addWidget(self.feeds_box)
        self._reload_feeds()

        # --- Kategorien & Schwerpunkte ------------------------------------
        lists_row = QHBoxLayout()
        self.cat_manager = _NamedListManager(
            "Kategorien",
            self.db.list_categories,
            self.db.add_category,
            self.db.delete_category,
        )
        self.focus_manager = _NamedListManager(
            "Schwerpunkte",
            self.db.list_focus_areas,
            self.db.add_focus_area,
            self.db.delete_focus_area,
        )
        lists_row.addWidget(self.cat_manager)
        lists_row.addWidget(self.focus_manager)
        root.addLayout(lists_row)

    # ----------------------------------------------------------- Feed-Aktionen
    def _reload_feeds(self) -> None:
        self.feed_list.clear()
        for feed in self.db.list_feeds():
            label = feed["url"]
            if feed["title"]:
                label = f"{feed['title']}  —  {feed['url']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, feed["id"])
            self.feed_list.addItem(item)

    def _add_feed(self) -> None:
        url = self.feed_input.text().strip()
        if not url:
            return
        if not url.lower().startswith(("http://", "https://")):
            QMessageBox.warning(self, "Ungültige URL", "Bitte eine http(s)-URL angeben.")
            return
        self.db.add_feed(url)
        self.feed_input.clear()
        self._reload_feeds()

    def _edit_feed(self) -> None:
        item = self.feed_list.currentItem()
        if not item:
            return
        feed_id = item.data(Qt.ItemDataRole.UserRole)
        current = next((f for f in self.db.list_feeds() if f["id"] == feed_id), None)
        if not current:
            return
        new_url, ok = QInputDialog.getText(
            self, "Feed bearbeiten", "URL:", text=current["url"]
        )
        if ok and new_url.strip():
            self.db.update_feed(feed_id, new_url.strip(), current["title"])
            self._reload_feeds()

    def _delete_feed(self) -> None:
        item = self.feed_list.currentItem()
        if not item:
            return
        feed_id = item.data(Qt.ItemDataRole.UserRole)
        self.db.delete_feed(feed_id)
        self._reload_feeds()

    # --------------------------------------------------------- Ollama-Aktionen
    def _current_client(self) -> OllamaClient:
        return OllamaClient(self.url_input.text().strip(), self.model_input.text().strip())

    def _test_connection(self) -> None:
        client = self._current_client()
        if client.is_available():
            QMessageBox.information(
                self, "Verbindung", "Ollama ist erreichbar. ✅"
            )
        else:
            QMessageBox.warning(
                self,
                "Verbindung",
                f"Ollama unter {client.base_url} NICHT erreichbar.\n"
                "Bitte sicherstellen, dass Ollama läuft.",
            )

    def _pick_model(self) -> None:
        client = self._current_client()
        try:
            models = client.list_models()
        except OllamaError as exc:
            QMessageBox.warning(self, "Fehler", str(exc))
            return
        if not models:
            QMessageBox.information(self, "Modelle", "Keine Modelle gefunden.")
            return
        name, ok = QInputDialog.getItem(
            self, "Modell wählen", "Installierte Modelle:", models, 0, False
        )
        if ok and name:
            self.model_input.setText(name)

    def _browse_excel(self) -> None:
        path, _ = QFileDialog.getSaveFileName(
            self, "Excel-Datei wählen", self.excel_input.text(),
            "Excel-Dateien (*.xlsx)",
        )
        if path:
            self.excel_input.setText(path)

    def _save_settings(self) -> None:
        self.db.set_setting("ollama_url", self.url_input.text().strip())
        self.db.set_setting("ollama_model", self.model_input.text().strip())
        self.db.set_setting("excel_path", self.excel_input.text().strip())
        QMessageBox.information(self, "Gespeichert", "Einstellungen wurden gespeichert.")
