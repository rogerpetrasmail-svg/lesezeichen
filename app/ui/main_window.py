"""Hauptfenster mit Tabs für Recherche und Einstellungen."""

from __future__ import annotations

from PySide6.QtWidgets import QMainWindow, QTabWidget

from .. import APP_NAME, __version__
from ..database import Database
from .research_tab import ResearchTab
from .settings_tab import SettingsTab


class MainWindow(QMainWindow):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self.setWindowTitle(f"{APP_NAME} {__version__}  –  lokal & offline (Ollama)")
        self.resize(1100, 760)

        self.tabs = QTabWidget()
        self.research_tab = ResearchTab(db)
        self.settings_tab = SettingsTab(db)
        self.tabs.addTab(self.research_tab, "Recherche")
        self.tabs.addTab(self.settings_tab, "Einstellungen")
        self.tabs.currentChanged.connect(self._on_tab_changed)
        self.setCentralWidget(self.tabs)

        self.statusBar().showMessage("Bereit. Alle Verarbeitung erfolgt lokal.")

    def _on_tab_changed(self, index: int) -> None:
        # Beim Wechsel zur Recherche die Liste aktualisieren (Feeds/Kategorien
        # könnten geändert worden sein).
        if self.tabs.widget(index) is self.research_tab:
            self.research_tab.reload_articles()

    def closeEvent(self, event) -> None:  # noqa: N802 (Qt-Signatur)
        self.db.close()
        super().closeEvent(event)
