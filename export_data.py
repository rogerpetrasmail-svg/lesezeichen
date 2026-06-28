#!/usr/bin/env python3
# =====================================================================
# OBS MODULAR DASHBOARD  ·  export_data.py   (Multi-Sheet / Multi-Series)
# ---------------------------------------------------------------------
# Liest eine Excel-MATRIX und exportiert sie in eine flexible Datenbasis.
#
# NEUE LOGIK:
#   * Jedes Tabellenblatt (Sheet) der Excel-Datei = EIN Diagramm-Datensatz.
#   * Innerhalb eines Sheets:
#       - 1. Spalte  = labels (X-Achse / Kategorien)
#       - alle weiteren Spalten = je eine Datenreihe (dataset),
#         der Spaltenkopf ist der Reihenname (z.B. "Var 1", "Var 2", ...)
#
# AUSGABE (zwei Dateien, gleicher Inhalt):
#   * dashboard_data.json  -> klassisch (Server / Tools / Kontrolle)
#   * dashboard_data.js    -> setzt window.OBS_DATA = {...}
#                             => per <script> einbindbar, läuft über das
#                                file://-Protokoll OHNE CORS-Fehler.
#
# Ohne Excel/pandas werden eingebaute DUMMY_DATA geschrieben -> sofort testbar.
# =====================================================================

import json
import os

# --- HIER anpassen: Pfad zur Excel-Datei ----------------------------
EXCEL_PATH = "dashboard.xlsx"
OUTPUT_JSON = "dashboard_data.json"
OUTPUT_JS = "dashboard_data.js"

# ---------------------------------------------------------------------
# Eingebaute Dummy-Daten in der NEUEN sheets/datasets-Struktur
# (deckt mehrere Diagrammtypen ab: Zeitreihen, Radar, Anteile)
# ---------------------------------------------------------------------
_MONTHS = ["Jan", "Feb", "Mrz", "Apr", "Mai", "Jun",
           "Jul", "Aug", "Sep", "Okt", "Nov", "Dez"]

DUMMY_DATA = {
    "meta": {"source": "dummy", "sheets_found": ["Umsatz", "Auslastung", "Profil", "Anteile"]},
    "sheets": {
        # Zeitreihe mit 4 Datenreihen -> ideal für Line / Area / Bar / Scatter / Combo
        "Umsatz": {
            "labels": _MONTHS,
            "datasets": {
                "Var 1": [200, 300, 350, 450, 480, 499, 520, 599, 700, 820, 920, 1000],
                "Var 2": [50, 60, 70, 60, 80, 60, 80, 90, 50, 30, 50, 60],
                "Var 3": [350, 320, 300, 250, 220, 180, 190, 200, 230, 210, 200, 225],
                "Var 4": [278, 299, 350, 200, 220, 180, 250, 230, 210, 190, 240, 220],
            },
        },
        # Zwei Reihen -> gut für Verbund (Combo: Var1=Balken, Var2=Linie)
        "Auslastung": {
            "labels": _MONTHS,
            "datasets": {
                "Var 1": [40, 65, 52, 78, 60, 47, 70, 82, 75, 90, 66, 80],
                "Var 2": [30, 48, 62, 70, 81, 55, 60, 72, 68, 85, 59, 74],
            },
        },
        # Wenige Achsen -> ideal für Radar
        "Profil": {
            "labels": ["SPD", "PWR", "DEF", "ACC", "EFF", "RES"],
            "datasets": {
                "Var 1": [80, 65, 50, 72, 60, 45],
                "Var 2": [55, 70, 62, 48, 75, 58],
            },
        },
        # Wenige Kategorien -> ideal für Kreisdiagramme
        "Anteile": {
            "labels": ["CORE", "AUX", "NET", "RES"],
            "datasets": {
                "Var 1": [35, 25, 22, 18],
            },
        },
    },
}


# ---------------------------------------------------------------------
# Excel-Auslese (generisch: pro Sheet 1 Label-Spalte + N Datenreihen)
# ---------------------------------------------------------------------
def read_excel(path):
    """Liest jede Tabelle der Excel-Datei in die sheets/datasets-Struktur.
    Gibt None zurück, wenn pandas fehlt oder die Datei nicht existiert."""
    try:
        import pandas as pd
    except ImportError:
        print("[i] pandas nicht installiert -> nutze Dummy-Daten "
              "(pip install pandas openpyxl)")
        return None

    if not os.path.exists(path):
        print(f"[i] Excel '{path}' nicht gefunden -> nutze Dummy-Daten")
        return None

    print(f"[+] Lese Excel-Matrix: {path}")
    xls = pd.ExcelFile(path)
    sheets = {}

    for name in xls.sheet_names:
        df = xls.parse(name)
        if df.empty or len(df.columns) < 2:
            print(f"    - überspringe leeres/zu schmales Blatt '{name}'")
            continue

        cols = list(df.columns)
        label_col = cols[0]
        labels = ["" if pd.isna(v) else str(v) for v in df[label_col].tolist()]

        datasets = {}
        for c in cols[1:]:
            datasets[str(c)] = [float(x) if pd.notna(x) else 0.0 for x in df[c].tolist()]

        sheets[str(name)] = {"labels": labels, "datasets": datasets}
        print(f"    - '{name}': {len(labels)} Labels, "
              f"{len(datasets)} Datenreihe(n) ({', '.join(datasets.keys())})")

    if not sheets:
        print("[i] keine brauchbaren Blätter gefunden -> nutze Dummy-Daten")
        return None

    return {"meta": {"source": path, "sheets_found": list(sheets.keys())},
            "sheets": sheets}


# ---------------------------------------------------------------------
# Schreiben: JSON + JS (window.OBS_DATA)
# ---------------------------------------------------------------------
def write_outputs(data):
    payload = json.dumps(data, ensure_ascii=False, indent=2)

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        f.write(payload)

    # Die JS-Variante umgeht das file://-CORS-Problem: einfach per
    # <script src="dashboard_data.js"></script> einbinden.
    with open(OUTPUT_JS, "w", encoding="utf-8") as f:
        f.write("/* Auto-generiert von export_data.py – nicht von Hand ändern. */\n")
        f.write("window.OBS_DATA = ")
        f.write(payload)
        f.write(";\n")

    sheets = data.get("sheets", {})
    print(f"[✓] Geschrieben: {OUTPUT_JSON} + {OUTPUT_JS}  "
          f"({len(sheets)} Sheet(s): {', '.join(sheets.keys())})")


def main():
    data = read_excel(EXCEL_PATH)
    if data is None:
        data = DUMMY_DATA
    write_outputs(data)


if __name__ == "__main__":
    main()
