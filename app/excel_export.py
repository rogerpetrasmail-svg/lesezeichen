"""Excel-Export mit hoher Fehlertoleranz.

Spaltenstruktur (exakt wie gefordert):
    Titel | Kategorie | Score | Schwerpunkt | Zusammenfassung |
    Eigenes_Script | Original_Beitrag

- Fehlende Zielordner werden automatisch angelegt.
- Ist die Zieldatei geöffnet/gesperrt, wird statt eines Absturzes ein
  Recovery-Backup (z. B. ``File_RECOVERY.xlsx``) geschrieben.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

COLUMNS = [
    ("Titel", "titel", 40),
    ("Kategorie", "kategorie", 22),
    ("Score", "score", 8),
    ("Schwerpunkt", "schwerpunkt", 30),
    ("Zusammenfassung", "zusammenfassung", 60),
    ("Eigenes_Script", "eigenes_script", 60),
    ("Original_Beitrag", "original_beitrag", 60),
]


class ExcelExportResult:
    def __init__(self, path: Path, recovered: bool, message: str) -> None:
        self.path = path
        self.recovered = recovered
        self.message = message


def _build_workbook(rows: Iterable[Mapping]) -> Workbook:
    wb = Workbook()
    ws = wb.active
    ws.title = "Recherche"

    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill("solid", fgColor="2F5597")
    wrap = Alignment(vertical="top", wrap_text=True)

    for col_idx, (header, _key, width) in enumerate(COLUMNS, start=1):
        cell = ws.cell(row=1, column=col_idx, value=header)
        cell.font = header_font
        cell.fill = header_fill
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    for r_idx, row in enumerate(rows, start=2):
        for c_idx, (_header, key, _width) in enumerate(COLUMNS, start=1):
            value = row.get(key, "")
            if key == "score":
                try:
                    value = int(value or 0)
                except (TypeError, ValueError):
                    value = 0
            cell = ws.cell(row=r_idx, column=c_idx, value=value)
            cell.alignment = wrap

    ws.freeze_panes = "A2"
    return wb


def _recovery_path(path: Path) -> Path:
    return path.with_name(f"{path.stem}_RECOVERY{path.suffix}")


def export_to_excel(target_path: str | Path, rows: Iterable[Mapping]) -> ExcelExportResult:
    """Schreibt die Daten nach Excel; weicht bei Sperre auf Recovery-Datei aus.

    Gibt ein ExcelExportResult mit tatsächlich genutztem Pfad zurück.
    """
    path = Path(target_path)
    rows = list(rows)

    # 1) Zielordner sicherstellen
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        # z. B. Laufwerk X:\ existiert gar nicht -> Recovery neben DB/Home
        fallback = Path.home() / f"{path.stem}_RECOVERY{path.suffix}"
        wb = _build_workbook(rows)
        wb.save(str(fallback))
        return ExcelExportResult(
            fallback,
            recovered=True,
            message=(
                f"Zielordner '{path.parent}' nicht verfügbar ({exc}). "
                f"Backup gespeichert unter: {fallback}"
            ),
        )

    wb = _build_workbook(rows)

    # 2) Versuch, direkt zu speichern
    try:
        wb.save(str(path))
        return ExcelExportResult(path, recovered=False, message=f"Gespeichert: {path}")
    except (PermissionError, OSError) as exc:
        # Datei geöffnet/gesperrt -> Recovery-Backup
        recovery = _recovery_path(path)
        try:
            wb.save(str(recovery))
            return ExcelExportResult(
                recovery,
                recovered=True,
                message=(
                    f"'{path.name}' war gesperrt/geöffnet ({exc}). "
                    f"Backup gespeichert: {recovery}"
                ),
            )
        except (PermissionError, OSError) as exc2:
            # Auch Recovery gesperrt -> in Home-Verzeichnis ausweichen
            home_recovery = Path.home() / recovery.name
            wb.save(str(home_recovery))
            return ExcelExportResult(
                home_recovery,
                recovered=True,
                message=(
                    f"Ziel und Recovery gesperrt ({exc2}). "
                    f"Backup gespeichert: {home_recovery}"
                ),
            )
