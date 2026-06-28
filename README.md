# OBS Modular Dashboard

Modulares Daten- & Grafik-System für OBS-Studio (HTML Browser Sources).
Alle Elemente haben einen **transparenten Hintergrund** und sind in OBS frei
positionier- und skalierbar. Standard-Design: Industrial-Orange (`#d35400`).

## Struktur

```
.
├── export_data.py            # Python-Utility: Excel -> dashboard_data.json (mit Dummy-Daten)
├── dashboard_data.json       # generierte Datenquelle für alle Module
├── customizer.html           # Live-Steuerung (Farben, Linienstärke, Speed, Glow, Rahmen)
├── shared/
│   ├── obs-core.css          # gemeinsame Basis-Styles + CSS-Variablen + Tech-Rahmen
│   └── obs-core.js           # Settings, Live-Update-Kanäle, Daten-Loader, SVG-Helfer
├── gauges/                   # 4 Gauge-Module
│   ├── orbital-core.html
│   ├── linear-accelerator.html
│   ├── target-scope.html
│   └── segmented-matrix.html
└── charts/                   # 14 Diagramm-Module
    ├── line-digital-grid.html      ├── line-stepped-pulse.html
    ├── bar-solid-neon.html         ├── bar-crosshatched.html
    ├── pie-tech-donut.html         ├── pie-exploded-segments.html
    ├── area-glow-fill.html         ├── area-scanlines.html
    ├── scatter-crosshair-dots.html ├── scatter-signal-matrix.html
    ├── radar-spider-web.html       ├── radar-sonar-scan.html
    └── combo-trend-analyzer.html   └── combo-minmax-cage.html
```

## 1. Daten erzeugen

```bash
# optional: pip install pandas openpyxl   (nur für echte Excel-Dateien nötig)
python3 export_data.py
```

- Pfad zur Excel-Datei in `export_data.py` über `EXCEL_PATH` setzen.
- Ohne Excel/pandas werden automatisch realistische **Dummy-Daten** geschrieben –
  das System ist also sofort testbar.
- Erwartete Tabellenblätter (generisch): `gauges`, `line`, `bar`, `pie`,
  `area`, `scatter`, `radar`, `combo`. Fehlende Blätter werden mit Dummy-Werten gefüllt.

## 2. In OBS einbinden

Jedes Modul ist eine eigenständige HTML-Datei. In OBS:
**Quellen → + → Browser** → *Lokale Datei* → eine der Modul-HTMLs wählen.
Breite/Höhe nach Bedarf (z. B. 400×260 für Charts, 300×300 für Gauges).
Der Hintergrund ist transparent – das Element lässt sich frei platzieren.

Wichtig: Die Module laden `shared/` und `dashboard_data.json` über relative
Pfade. Die Ordnerstruktur muss also erhalten bleiben (am einfachsten: das
ganze Verzeichnis aus einem lokalen Webserver oder per Datei-URL laden).

### Gauge-Auswahl

Gauges zeigen standardmäßig je einen Eintrag aus `dashboard_data.json`.
Andere Werte per URL-Parameter wählen:
`orbital-core.html?gauge=g3` oder `orbital-core.html?index=2`.

## 3. Live-Customizer

`customizer.html` im Browser öffnen. Über Schieberegler/Farbpicker lassen sich
**global** anpassen: Primär-/Akzent-/Textfarbe, Linienstärke, Animations­geschwindigkeit,
Glow und der Tech-Rahmen. Die Vorschau rechts zeigt alle 18 Module live.

Die Einstellungen werden auf drei Wegen verteilt:

1. **localStorage** – persistent; OBS-Sources im selben Browser-Profil lesen sie.
2. **BroadcastChannel** – live über alle Tabs/Sources einer Browser-Instanz.
3. **postMessage** – live in die Vorschau-iframes des Customizers.

Zusätzlich erzeugt der Customizer einen **URL-Parameter-String** (Button
„OBS-URL kopieren"), den man an jede Modul-URL anhängen kann, um ein Modul fest
zu konfigurieren – ideal, wenn OBS-Sources kein localStorage teilen:

```
gauges/orbital-core.html?primary=00aaff&accent=33ccff&lineWidth=3&speed=1.5&glow=10&frame=1
```

## Design-Architektur

- **Zentrale CSS-Variablen** in `shared/obs-core.css` (`--c-primary`, `--c-accent`,
  `--line-width`, `--speed`, `--glow`, …). Der Customizer überschreibt sie live,
  wodurch sich Farben/Linien/Glow ohne Neu-Rendern aktualisieren.
- **Animationsgeschwindigkeit** ist überall als `calc(<dauer> / var(--speed))`
  umgesetzt – ein Regler steuert alle Module.
- **Gauges** animieren dauerhaft dezent (rotierende Ringe, Scan, Flacker, Atem-Puls).
- **Diagramme** sind „ruhige" Standbilder mit nur **einer** In-Animation
  (Linie zeichnen / Balken aufsteigen / Segmente einwachsen).
- Jedes Modul bringt seinen eigenen `.tech-frame` (CSS) mit, damit es überall
  in OBS allein stehen kann.

## Lokaler Test

```bash
python3 export_data.py
python3 -m http.server 8000
# Browser: http://localhost:8000/customizer.html
```
