# RSS-Rechercheur

Eine **vollständig lokale, offline** Windows-Desktop-Anwendung zur automatisierten
RSS-Recherche, **Übersetzung**, Relevanz-Bewertung, Kategorisierung und
Zusammenfassung – die gesamte KI-Verarbeitung läuft über deine **lokale
Ollama-Instanz** (`http://localhost:11434`). Es werden **keine** externen
Cloud-APIs (OpenAI, Anthropic o. Ä.) verwendet.

Oberfläche: **PySide6 (Qt)**. Datenhaltung: **SQLite**. Export: **Excel (.xlsx)**.

---

## ⬇️ Fertige Anwendung herunterladen (kein Python nötig)

Du musst **keine** Python-Umgebung einrichten. Die fertige `.exe` und der
Installer werden automatisch auf einem Windows-Server gebaut (GitHub Actions).

1. Öffne im GitHub-Repository den Reiter **Actions**.
2. Wähle den letzten erfolgreichen Lauf von **„Build Windows-Installer“**.
3. Unter **Artifacts** findest du:
   - **`RSS-Rechercheur-Setup`** → klassischer Installer (`...-Setup-1.0.0.exe`).
   - **`RSS-Rechercheur-portable`** → portabler Ordner mit `RSS-Rechercheur.exe`
     (kein Installieren nötig, einfach starten).
4. Herunterladen, entpacken, **`Setup`-Datei** ausführen **oder** die
   `RSS-Rechercheur.exe` direkt starten.

> Hinweis: Der Build wird automatisch bei jedem Push auf den Branch ausgelöst.
> Alternativ kann er unter **Actions → Build Windows-Installer → „Run workflow“**
> manuell gestartet werden. Für ein versioniertes Release einen Tag `v1.0.0`
> pushen – dann wird der Installer zusätzlich unter **Releases** veröffentlicht.

---

## 🧠 Voraussetzung: Ollama

Die App benötigt eine laufende **Ollama**-Instanz auf demselben PC:

```text
1. Ollama installieren (https://ollama.com)
2. Modell laden, z. B.:   ollama pull qwen2.5-coder:32b
3. Ollama läuft danach unter http://localhost:11434
```

Der Modellname ist in der App unter **Einstellungen** frei wählbar
(Standard: `qwen2.5-coder:32b`).

---

## ✨ Funktionen

### 1. Einstellungen & Verwaltung
- **RSS-Feeds/Quellen** hinzufügen, bearbeiten, löschen.
- **Kategorien** und **Schwerpunkte** als dynamische Listen pflegen.
- **Ollama-Modellname** und **Ollama-URL** konfigurierbar (mit Verbindungstest
  und Auswahl der installierten Modelle).
- **Excel-Exportpfad** einstellbar.

### 2. 1-Klick-Recherche, Übersetzung & Analyse
- Button **„Recherche starten“** liest im Hintergrund alle Feeds aus.
- Jeder Beitrag wird an Ollama gesendet (natives `format: "json"`). Per
  System-Prompt führt das Modell strikt aus:
  - **Übersetzung** ins Deutsche (falls nötig),
  - **Relevanz-Score** 1–10,
  - **Kategorisierung** ausschließlich gegen deine UI-Kategorien,
  - **Schwerpunkt** (Kernfokus in wenigen Worten),
  - **Zusammenfassung** (präzise, deutsch).
- Bereits analysierte Beiträge werden anhand der GUID übersprungen.

### 3. Darstellungs- & Editier-UI
- Ergebnisse erscheinen in einer Liste; Auswahl öffnet ein **editierbares
  Formular** (Titel, Kategorie, Score, Schwerpunkt, Zusammenfassung).
- Jedes Feld ist manuell korrigierbar.
- Pro Beitrag gibt es ein großes Textfeld **„Eigenes Script“** für dein
  eigenes Copywriting.

### 4. Datenbank & Excel-Export
- Alles wird dauerhaft in **SQLite** gespeichert (inkl. deiner Scripte).
- **„In Excel speichern“** (und automatisch nach erfolgreicher Recherche)
  schreibt nach `X:\Projekte\YT\TEIN - TOW\Datenbank\File.xlsx`.
- Spalten: `Titel | Kategorie | Score | Schwerpunkt | Zusammenfassung | Eigenes_Script | Original_Beitrag`.
- **Fehlertoleranz**: fehlender Ordner wird angelegt; ist die Datei
  gesperrt/geöffnet, wird automatisch ein Backup `File_RECOVERY.xlsx`
  geschrieben statt abzustürzen.

---

## 🗂 Projektstruktur

```text
lesezeichen/
├─ run.py                      # Einstiegspunkt (Dev & PyInstaller)
├─ requirements.txt
├─ app/
│  ├─ config.py                # Standardwerte, Pfade, System-Prompt
│  ├─ database.py              # SQLite-Schicht
│  ├─ ollama_client.py         # Lokaler Ollama-HTTP-Client (format=json)
│  ├─ rss.py                   # Feed-Auslesung (feedparser)
│  ├─ analysis.py              # Reine Aufbereitung der Modell-Antwort
│  ├─ research.py              # Hintergrund-Worker (QThread)
│  ├─ excel_export.py          # Excel-Export inkl. Recovery
│  └─ ui/
│     ├─ main_window.py
│     ├─ research_tab.py       # 1-Klick-Recherche + Editier-Formular
│     └─ settings_tab.py       # Feeds/Kategorien/Schwerpunkte/Ollama
├─ packaging/
│  ├─ rss_rechercheur.spec     # PyInstaller-Spec (One-Folder, GUI)
│  ├─ installer.iss            # Inno-Setup-Installer
│  └─ version_info.txt         # Versionsangaben für die .exe
├─ tests/test_core.py          # Smoke-Tests der Kernlogik
└─ .github/workflows/build-windows.yml   # Baut .exe + Installer
```

---

## 🛠 Lokal aus dem Quellcode starten (optional, für Entwickler)

```bash
python -m venv .venv
. .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

Tests:

```bash
python tests/test_core.py
```

Selbst eine `.exe` bauen (auf Windows):

```bash
pyinstaller packaging/rss_rechercheur.spec --noconfirm
# -> dist/RSS-Rechercheur/RSS-Rechercheur.exe
```

---

## 🔒 Datenschutz

Sämtliche Verarbeitung erfolgt lokal. Die App kontaktiert ausschließlich deine
lokale Ollama-Instanz und die von dir eingetragenen RSS-Feed-URLs. Es findet
keinerlei Kommunikation mit Cloud-KI-Diensten statt.
