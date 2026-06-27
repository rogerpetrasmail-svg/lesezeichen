"""Recherche-Tab: 1-Klick-Recherche, Ergebnisliste und editierbares Formular."""

from __future__ import annotations

from PySide6.QtCore import Qt, QThread
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPlainTextEdit,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from ..database import Database
from ..excel_export import export_to_excel
from ..research import ResearchWorker


class ResearchTab(QWidget):
    def __init__(self, db: Database) -> None:
        super().__init__()
        self.db = db
        self._thread: QThread | None = None
        self._worker: ResearchWorker | None = None
        self._current_id: int | None = None
        self._build_ui()
        self.reload_articles()

    # --------------------------------------------------------------- UI-Aufbau
    def _build_ui(self) -> None:
        root = QVBoxLayout(self)

        # Steuerleiste
        top = QHBoxLayout()
        self.start_btn = QPushButton("▶  Recherche starten")
        self.start_btn.setMinimumHeight(38)
        self.start_btn.clicked.connect(self._start_research)
        self.excel_btn = QPushButton("📊  In Excel speichern")
        self.excel_btn.clicked.connect(self._export_excel)
        top.addWidget(self.start_btn)
        top.addWidget(self.excel_btn)
        top.addStretch(1)
        root.addLayout(top)

        self.progress = QProgressBar()
        self.progress.setVisible(False)
        root.addWidget(self.progress)
        self.status_label = QLabel("")
        root.addWidget(self.status_label)

        # Liste links, Formular rechts
        splitter = QSplitter(Qt.Orientation.Horizontal)

        self.article_list = QListWidget()
        self.article_list.currentItemChanged.connect(self._on_select)
        splitter.addWidget(self.article_list)

        self.form_widget = self._build_form()
        splitter.addWidget(self.form_widget)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        root.addWidget(splitter, stretch=1)

    def _build_form(self) -> QWidget:
        container = QWidget()
        outer = QVBoxLayout(container)
        form = QFormLayout()

        self.f_titel = QLineEdit()
        self.f_kategorie = QLineEdit()
        self.f_score = QSpinBox()
        self.f_score.setRange(0, 10)
        self.f_schwerpunkt = QLineEdit()
        self.f_zusammenfassung = QPlainTextEdit()
        self.f_zusammenfassung.setMinimumHeight(110)
        self.f_eigenes_script = QPlainTextEdit()
        self.f_eigenes_script.setMinimumHeight(160)
        self.f_eigenes_script.setPlaceholderText(
            "Hier dein eigenes Script / Copywriting eintragen …"
        )
        self.f_original = QPlainTextEdit()
        self.f_original.setMinimumHeight(110)

        form.addRow("Titel:", self.f_titel)
        form.addRow("Kategorie:", self.f_kategorie)
        form.addRow("Score (1–10):", self.f_score)
        form.addRow("Schwerpunkt:", self.f_schwerpunkt)
        form.addRow("Zusammenfassung:", self.f_zusammenfassung)
        form.addRow("Eigenes Script:", self.f_eigenes_script)
        form.addRow("Original-Beitrag:", self.f_original)
        outer.addLayout(form)

        btn_row = QHBoxLayout()
        self.save_btn = QPushButton("💾  Änderungen speichern")
        self.save_btn.clicked.connect(self._save_current)
        self.delete_btn = QPushButton("🗑  Eintrag löschen")
        self.delete_btn.clicked.connect(self._delete_current)
        btn_row.addStretch(1)
        btn_row.addWidget(self.delete_btn)
        btn_row.addWidget(self.save_btn)
        outer.addLayout(btn_row)

        self._set_form_enabled(False)
        return container

    def _set_form_enabled(self, enabled: bool) -> None:
        for w in (
            self.f_titel, self.f_kategorie, self.f_score, self.f_schwerpunkt,
            self.f_zusammenfassung, self.f_eigenes_script, self.f_original,
            self.save_btn, self.delete_btn,
        ):
            w.setEnabled(enabled)

    # ----------------------------------------------------------- Listenlogik
    def reload_articles(self) -> None:
        self.article_list.blockSignals(True)
        self.article_list.clear()
        for art in self.db.list_articles():
            label = f"[{art['score']}] {art['titel']}"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, art["id"])
            self.article_list.addItem(item)
        self.article_list.blockSignals(False)
        if self.article_list.count() and self._current_id is None:
            self.article_list.setCurrentRow(0)

    def _on_select(self, current: QListWidgetItem | None, _prev=None) -> None:
        if current is None:
            self._set_form_enabled(False)
            self._current_id = None
            return
        article_id = current.data(Qt.ItemDataRole.UserRole)
        art = self.db.get_article(article_id)
        if not art:
            return
        self._current_id = article_id
        self._set_form_enabled(True)
        self.f_titel.setText(art["titel"])
        self.f_kategorie.setText(art["kategorie"])
        self.f_score.setValue(int(art["score"] or 0))
        self.f_schwerpunkt.setText(art["schwerpunkt"])
        self.f_zusammenfassung.setPlainText(art["zusammenfassung"])
        self.f_eigenes_script.setPlainText(art["eigenes_script"])
        self.f_original.setPlainText(art["original_beitrag"])

    def _save_current(self) -> None:
        if self._current_id is None:
            return
        self.db.update_article_fields(
            self._current_id,
            titel=self.f_titel.text(),
            kategorie=self.f_kategorie.text(),
            score=self.f_score.value(),
            schwerpunkt=self.f_schwerpunkt.text(),
            zusammenfassung=self.f_zusammenfassung.toPlainText(),
            eigenes_script=self.f_eigenes_script.toPlainText(),
            original_beitrag=self.f_original.toPlainText(),
        )
        self.reload_articles()
        self.status_label.setText("Änderungen gespeichert.")

    def _delete_current(self) -> None:
        if self._current_id is None:
            return
        confirm = QMessageBox.question(
            self, "Löschen", "Diesen Eintrag wirklich löschen?"
        )
        if confirm == QMessageBox.StandardButton.Yes:
            self.db.delete_article(self._current_id)
            self._current_id = None
            self.reload_articles()

    # ----------------------------------------------------------- Recherche
    def _start_research(self) -> None:
        if self._thread is not None:
            return
        if not self.db.list_feeds():
            QMessageBox.warning(
                self, "Keine Feeds",
                "Bitte zuerst im Tab 'Einstellungen' RSS-Feeds hinzufügen.",
            )
            return
        self.start_btn.setEnabled(False)
        self.progress.setVisible(True)
        self.progress.setRange(0, 0)  # unbestimmt bis erste Meldung
        self.status_label.setText("Recherche läuft …")

        self._thread = QThread()
        self._worker = ResearchWorker(self.db)
        self._worker.moveToThread(self._thread)
        self._thread.started.connect(self._worker.run)
        self._worker.progress.connect(self._on_progress)
        self._worker.article_done.connect(self._on_article_done)
        self._worker.log.connect(self._on_log)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.start()

    def _on_progress(self, current: int, total: int, text: str) -> None:
        if total > 0:
            self.progress.setRange(0, total)
            self.progress.setValue(current)
        self.status_label.setText(text)

    def _on_article_done(self, _article_id: int) -> None:
        self.reload_articles()

    def _on_log(self, message: str) -> None:
        self.status_label.setText(message)

    def _on_finished(self, processed: int, skipped: int) -> None:
        self.progress.setVisible(False)
        self.start_btn.setEnabled(True)
        self.status_label.setText(
            f"Fertig. {processed} neue Beiträge analysiert, {skipped} übersprungen."
        )
        if self._thread:
            self._thread.wait()
        self._thread = None
        self._worker = None
        self.reload_articles()
        # Automatischer Excel-Export nach erfolgreicher Recherche
        if processed > 0:
            self._export_excel(silent=True)

    # ----------------------------------------------------------- Excel-Export
    def _export_excel(self, silent: bool = False) -> None:
        path = self.db.get_setting("excel_path")
        rows = [dict(r) for r in self.db.list_articles()]
        result = export_to_excel(path, rows)
        if result.recovered:
            QMessageBox.warning(self, "Excel-Export", result.message)
        elif not silent:
            QMessageBox.information(self, "Excel-Export", result.message)
        self.status_label.setText(result.message)
