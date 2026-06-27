"""Zentrale Konfiguration, Standardwerte und Pfad-Verwaltung.

Alle Pfade werden so gewählt, dass die Anwendung vollständig lokal arbeitet.
Die SQLite-Datenbank und Einstellungen liegen im Benutzer-Anwendungsdatenordner,
damit sie auch in einer installierten (.exe) Version dauerhaft erhalten bleiben.
"""

from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "RSS-Rechercheur"
APP_VENDOR = "Lesezeichen"

# ---------------------------------------------------------------------------
# Standardwerte (können in der UI jederzeit geändert werden)
# ---------------------------------------------------------------------------
DEFAULT_OLLAMA_URL = "http://localhost:11434"
DEFAULT_OLLAMA_MODEL = "qwen2.5-coder:32b"

# Vom Nutzer gewünschter Standard-Exportpfad (Windows).
DEFAULT_EXCEL_PATH = r"X:\Projekte\YT\TEIN - TOW\Datenbank\File.xlsx"

# Vorausgefüllte Beispiel-Kategorien beim allerersten Start.
DEFAULT_CATEGORIES = [
    "Künstliche Intelligenz",
    "Technologie",
    "Wirtschaft",
    "Wissenschaft",
    "Politik",
]

# Vorausgefüllte Beispiel-Schwerpunkte beim allerersten Start.
DEFAULT_FOCUS_AREAS = [
    "Produktneuheiten",
    "Markttrends",
    "Praxisbeispiele",
]


def app_data_dir() -> Path:
    """Liefert das plattformabhängige Verzeichnis für persistente App-Daten."""
    if os.name == "nt":  # Windows
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:  # Linux / macOS (Entwicklung & Tests)
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(
            os.path.expanduser("~"), ".local", "share"
        )
    path = Path(base) / APP_NAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def database_path() -> Path:
    """Vollständiger Pfad zur SQLite-Datenbank."""
    return app_data_dir() / "rss_rechercheur.sqlite3"


# ---------------------------------------------------------------------------
# System-Prompt für das Ollama-Modell
# ---------------------------------------------------------------------------
def build_system_prompt(categories: list[str], focus_areas: list[str]) -> str:
    """Erzeugt den strikten System-Prompt für die JSON-Analyse.

    Die Kategorien und Schwerpunkte werden dynamisch aus der UI übergeben,
    damit das Modell ausschliesslich gegen die vom Nutzer gepflegten Listen
    abgleicht.
    """
    kategorien_liste = ", ".join(f'"{c}"' for c in categories) or '"Allgemein"'
    schwerpunkt_hinweis = ", ".join(focus_areas) if focus_areas else "frei wählbar"

    return (
        "Du bist ein präziser deutschsprachiger Recherche-Assistent. "
        "Du analysierst einen einzelnen Nachrichten-/Blog-Beitrag und gibst "
        "AUSSCHLIESSLICH ein gültiges JSON-Objekt zurück – ohne Markdown, ohne "
        "Erklärtext, ohne Codeblock.\n\n"
        "Führe folgende Schritte strikt aus:\n"
        "1. ÜBERSETZUNG: Falls der Beitrag nicht auf Deutsch ist, verarbeite "
        "ihn und formuliere ALLE Ausgaben vollständig auf Deutsch.\n"
        "2. RELEVANZ-SCORE: Bewerte die Relevanz des Beitrags auf einer "
        "Ganzzahl-Skala von 1 (irrelevant) bis 10 (höchst relevant).\n"
        f"3. KATEGORISIERUNG: Ordne den Beitrag EXAKT einer oder mehreren der "
        f"folgenden vom Nutzer definierten Kategorien zu: [{kategorien_liste}]. "
        "Erfinde keine neuen Kategorien. Gib sie als Liste von Strings zurück.\n"
        f"4. SCHWERPUNKT: Extrahiere den Kernfokus in wenigen prägnanten "
        f"Worten (Orientierung an: {schwerpunkt_hinweis}).\n"
        "5. ZUSAMMENFASSUNG: Schreibe eine präzise, informative deutsche "
        "Zusammenfassung des Inhalts (3-6 Sätze).\n\n"
        "Antworte exakt in diesem JSON-Schema:\n"
        "{\n"
        '  "titel": string,            // deutscher (ggf. übersetzter) Titel\n'
        '  "relevanz_score": number,   // Ganzzahl 1-10\n'
        '  "kategorien": string[],     // nur Werte aus der erlaubten Liste\n'
        '  "schwerpunkt": string,      // kurzer Kernfokus\n'
        '  "zusammenfassung": string   // deutsche Zusammenfassung\n'
        "}"
    )
