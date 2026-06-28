#!/usr/bin/env python3
# =====================================================================
# OBS MODULAR DASHBOARD  ·  export_data.py
# ---------------------------------------------------------------------
# Utility-Skript: liest Werte aus einer beliebigen Excel-Datei und
# exportiert sie in eine lokale "dashboard_data.json", die von allen
# HTML/SVG-Modulen gelesen wird.
#
# - EXCEL_PATH unten anpassen.
# - Fehlt die Datei (oder pandas/openpyxl), werden automatisch die
#   eingebauten DUMMY_DATA geschrieben -> sofort testbar, ganz ohne Excel.
#
# Erwartete (generische) Tabellenblätter in der Excel-Datei:
#   * "gauges" : Spalten  id | label | value | min | max | unit
#   * "line"   : Spalten  x | y
#   * "bar"    : Spalten  label | y
#   * "pie"    : Spalten  label | y
#   * "area"   : Spalten  x | y
#   * "scatter": Spalten  x | y
#   * "radar"  : Spalten  label | y
#   * "combo"  : Spalten  label | bar | line
# Nicht vorhandene Blätter werden einfach mit Dummy-Werten gefüllt.
# =====================================================================

import json
import os

# --- HIER anpassen: Pfad zur Excel-Datei ----------------------------
EXCEL_PATH = "dashboard.xlsx"
OUTPUT_PATH = "dashboard_data.json"

# ---------------------------------------------------------------------
# Eingebaute, realistische Dummy-Daten (Fallback + Sofort-Test)
# ---------------------------------------------------------------------
DUMMY_DATA = {
    "meta": {"source": "dummy", "generated": "built-in sample"},
    "gauges": [
        {"id": "g1", "label": "POWER OUTPUT", "value": 72,  "min": 0, "max": 100, "unit": "%"},
        {"id": "g2", "label": "CORE TEMP",    "value": 64,  "min": 0, "max": 120, "unit": "°C"},
        {"id": "g3", "label": "VELOCITY",     "value": 340, "min": 0, "max": 500, "unit": "km/h"},
        {"id": "g4", "label": "SIGNAL",       "value": 88,  "min": 0, "max": 100, "unit": "%"},
    ],
    "series": {
        "line": {
            "label": "SIGNAL FLUX",
            "points": [
                {"x": "00:00", "y": 42}, {"x": "01:00", "y": 55},
                {"x": "02:00", "y": 48}, {"x": "03:00", "y": 71},
                {"x": "04:00", "y": 63}, {"x": "05:00", "y": 80},
                {"x": "06:00", "y": 74}, {"x": "07:00", "y": 92},
            ],
        },
        "bar": {
            "label": "THROUGHPUT",
            "points": [
                {"label": "ALPHA", "y": 40}, {"label": "BRAVO", "y": 65},
                {"label": "DELTA", "y": 52}, {"label": "ECHO",  "y": 78},
                {"label": "FOXT",  "y": 60}, {"label": "GOLF",  "y": 47},
            ],
        },
        "pie": {
            "label": "DISTRIBUTION",
            "points": [
                {"label": "CORE", "y": 35}, {"label": "AUX", "y": 25},
                {"label": "NET",  "y": 22}, {"label": "RES", "y": 18},
            ],
        },
        "area": {
            "label": "SYSTEM LOAD",
            "points": [
                {"x": "00:00", "y": 30}, {"x": "01:00", "y": 45},
                {"x": "02:00", "y": 40}, {"x": "03:00", "y": 60},
                {"x": "04:00", "y": 55}, {"x": "05:00", "y": 72},
                {"x": "06:00", "y": 68}, {"x": "07:00", "y": 85},
            ],
        },
        "scatter": {
            "label": "SAMPLE FIELD",
            "points": [
                {"x": 12, "y": 22}, {"x": 28, "y": 41}, {"x": 35, "y": 18},
                {"x": 44, "y": 63}, {"x": 51, "y": 47}, {"x": 58, "y": 72},
                {"x": 63, "y": 35}, {"x": 70, "y": 58}, {"x": 77, "y": 80},
                {"x": 82, "y": 44}, {"x": 88, "y": 66}, {"x": 95, "y": 52},
                {"x": 18, "y": 55}, {"x": 33, "y": 77}, {"x": 47, "y": 29},
                {"x": 60, "y": 90}, {"x": 73, "y": 12}, {"x": 86, "y": 38},
            ],
        },
        "radar": {
            "label": "PERFORMANCE",
            "axes": [
                {"label": "SPD", "y": 80}, {"label": "PWR", "y": 65},
                {"label": "DEF", "y": 50}, {"label": "ACC", "y": 72},
                {"label": "EFF", "y": 60},
            ],
        },
        "combo": {
            "label": "TREND ANALYSIS",
            "points": [
                {"label": "Q1", "bar": 40, "line": 30},
                {"label": "Q2", "bar": 55, "line": 48},
                {"label": "Q3", "bar": 50, "line": 62},
                {"label": "Q4", "bar": 72, "line": 70},
                {"label": "Q5", "bar": 66, "line": 81},
            ],
        },
    },
}


# ---------------------------------------------------------------------
# Excel-Auslese-Logik (generisch, pro Tabellenblatt)
# ---------------------------------------------------------------------
def read_excel(path):
    """Liest die Excel-Datei und baut das Datenmodell. Gibt None zurück,
    wenn pandas fehlt oder die Datei nicht existiert."""
    try:
        import pandas as pd  # nur importieren, wenn wirklich gebraucht
    except ImportError:
        print("[i] pandas nicht installiert -> nutze Dummy-Daten "
              "(pip install pandas openpyxl)")
        return None

    if not os.path.exists(path):
        print(f"[i] Excel '{path}' nicht gefunden -> nutze Dummy-Daten")
        return None

    print(f"[+] Lese Excel: {path}")
    xls = pd.ExcelFile(path)
    sheets = {name.lower(): name for name in xls.sheet_names}
    data = {"meta": {"source": path}, "gauges": [], "series": {}}

    def sheet(name):
        """Tabellenblatt als Liste von dicts, oder None."""
        if name in sheets:
            df = xls.parse(sheets[name]).fillna(0)
            return df.to_dict(orient="records")
        return None

    # --- Gauges -----------------------------------------------------
    gauges = sheet("gauges")
    if gauges:
        for i, row in enumerate(gauges):
            data["gauges"].append({
                "id":    str(row.get("id", f"g{i+1}")),
                "label": str(row.get("label", f"GAUGE {i+1}")),
                "value": float(row.get("value", 0)),
                "min":   float(row.get("min", 0)),
                "max":   float(row.get("max", 100)),
                "unit":  str(row.get("unit", "")),
            })
    else:
        data["gauges"] = DUMMY_DATA["gauges"]

    # --- XY-Serien (line / area / scatter) --------------------------
    for key in ("line", "area", "scatter"):
        rows = sheet(key)
        if rows:
            data["series"][key] = {
                "label": key.upper(),
                "points": [{"x": r.get("x", j), "y": float(r.get("y", 0))}
                           for j, r in enumerate(rows)],
            }
        else:
            data["series"][key] = DUMMY_DATA["series"][key]

    # --- Kategorie-Serien (bar / pie / radar) -----------------------
    for key in ("bar", "pie", "radar"):
        rows = sheet(key)
        if rows:
            field = "axes" if key == "radar" else "points"
            data["series"][key] = {
                "label": key.upper(),
                field: [{"label": str(r.get("label", j)), "y": float(r.get("y", 0))}
                        for j, r in enumerate(rows)],
            }
        else:
            data["series"][key] = DUMMY_DATA["series"][key]

    # --- Combo (bar + line) -----------------------------------------
    rows = sheet("combo")
    if rows:
        data["series"]["combo"] = {
            "label": "COMBO",
            "points": [{"label": str(r.get("label", j)),
                        "bar": float(r.get("bar", 0)),
                        "line": float(r.get("line", 0))}
                       for j, r in enumerate(rows)],
        }
    else:
        data["series"]["combo"] = DUMMY_DATA["series"]["combo"]

    return data


# ---------------------------------------------------------------------
# Hauptprogramm
# ---------------------------------------------------------------------
def main():
    data = read_excel(EXCEL_PATH)
    if data is None:
        data = DUMMY_DATA

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"[✓] Geschrieben: {OUTPUT_PATH}  "
          f"({len(data.get('gauges', []))} Gauges, "
          f"{len(data.get('series', {}))} Serien)")


if __name__ == "__main__":
    main()
