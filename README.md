# OBS Modular Dashboard

Modulares Daten- & Grafik-System für OBS-Studio (HTML Browser Sources).
Alle Elemente haben einen **transparenten Hintergrund** und sind in OBS frei
positionier- und skalierbar. Standard-Design: Industrial-Orange (`#d35400`).

Das System ist **Multi-Sheet / Multi-Datenreihen-fähig**: Jedes Tabellenblatt
der Excel-Datei wird zu einem Diagramm-Datensatz, der mehrere Datenreihen
(`Var 1`, `Var 2`, …) gleichzeitig enthalten kann. Es läuft komplett lokal
**ohne externe Bibliotheken** und **ohne Server** direkt über `file:///`.

## Struktur

```
.
├── export_data.py            # Excel-Matrix -> dashboard_data.json + .js (Dummy-Daten inkl.)
├── dashboard_data.json       # generierte Datenquelle (Kontrolle / Server)
├── dashboard_data.js         # generierte Datenquelle als window.OBS_DATA (file://-tauglich)
├── customizer.html           # Live-Steuerung + Sheet-Auswahl + OBS-URL-Generator
├── shared/
│   ├── obs-core.css          # Basis-Styles + CSS-Variablen + Tech-Rahmen
│   └── obs-core.js           # Settings, Live-Update, Daten-Loader, Sheet-/Serien-Helfer
├── gauges/                   # 4 Gauge-Module
└── charts/                   # 14 Diagramm-Module (7 Typen × 2 Varianten)
```

## 1. Datenstruktur

`dashboard_data.json` / `dashboard_data.js`:

```json
{
  "meta": { "source": "dashboard.xlsx", "sheets_found": ["Umsatz", "Profil"] },
  "sheets": {
    "Umsatz": {
      "labels":   ["Jan", "Feb", "Mrz", "..."],
      "datasets": {
        "Var 1": [200, 300, 350, "..."],
        "Var 2": [50,  60,  70,  "..."]
      }
    }
  }
}
```

- **Ein Sheet = ein Diagramm-Datensatz.** 1. Spalte der Excel-Tabelle = `labels`
  (X-Achse/Kategorien), jede weitere Spalte = eine Datenreihe (Spaltenkopf = Name).
- Jedes Diagramm-Modul kann **jedes** Sheet rendern – der Visualstil steckt im Modul,
  die Daten kommen über `?sheet=`.

## 2. Daten erzeugen

```bash
# optional: pip install pandas openpyxl   (nur für echte Excel-Dateien nötig)
python3 export_data.py
```

- Pfad zur Excel-Datei in `export_data.py` über `EXCEL_PATH` setzen.
- Erzeugt **zwei** Dateien mit gleichem Inhalt: `dashboard_data.json` und
  `dashboard_data.js` (`window.OBS_DATA = {...}`).
- Ohne Excel/pandas werden realistische **Dummy-Daten** mit mehreren Sheets und
  mehreren Datenreihen geschrieben – sofort testbar.

## 3. Datenzugriff & `file://` (kein CORS)

`OBS.loadData()` lädt in dieser Reihenfolge:

1. bereits per `<script>` gesetztes `window.OBS_DATA`,
2. sonst dynamisch nachgeladenes `dashboard_data.js` (Script-Tag — funktioniert
   über `file:///` **ohne CORS-Fehler**, anders als `fetch`),
3. als Server-Fallback `fetch('dashboard_data.json')`.

Damit laufen die Module per Doppelklick (`file://`) **und** über `http://`.

## 4. In OBS einbinden

**Quellen → + → Browser** → *Lokale Datei* → eine Modul-HTML wählen, oder eine
fertige URL aus dem Customizer einfügen. Die Ordnerstruktur muss erhalten bleiben
(Module laden `shared/` und `dashboard_data.js` über relative Pfade).

### URL-Parameter pro Modul

| Parameter | Wirkung | Beispiel |
|-----------|---------|----------|
| `sheet` | aktives Tabellenblatt (sonst erstes) | `?sheet=Umsatz` |
| `dataset` | (Gauges/Pie) Datenreihe wählen | `&dataset=Var 2` |
| `agg` | (Gauges) `last`·`max`·`min`·`avg`·`sum`·`first` | `&agg=max` |
| `min` `max` `unit` `label` | (Gauges) Skala/Beschriftung | `&max=1000&unit=€` |
| `primary` `accent` `text` | Farben (ohne `#`) | `&primary=00c8ff` |
| `lineWidth` `speed` `glow` `frameOpacity` `frame` | Design | `&speed=1.5&frame=0` |

Beispiel:
`charts/line-digital-grid.html?sheet=Umsatz&primary=00c8ff&accent=33ccff&speed=1.5`

## 5. Live-Customizer

`customizer.html` öffnen. Funktionen:

- **Datenblatt-Auswahl** – legt fest, welches Sheet (`?sheet=`) alle Vorschau-Module zeigen.
- **Live-Design** – Farben, Linienstärke, Speed, Glow, Rahmen wirken sofort auf
  die Vorschau und alle OBS-Sources im selben Browser/Profil
  (localStorage + BroadcastChannel + postMessage).
- **Pro Kachel:** „↗" öffnet das Modul in neuem Tab, „⧉" kopiert die **vollständige
  OBS-URL** inkl. `?sheet=` und aller Design-Parameter zum Einfügen in OBS.

> Hinweis: Die Vorschau-iframes bekommen bewusst **nur** `?sheet=`/`?dataset=` im
> URL (kein Design), damit die Live-Kanäle das Design steuern können. Die kopierte
> URL enthält dagegen das volle Design – für den eigenständigen OBS-Betrieb, wo
> kein Live-Customizer läuft.

## 6. Multi-Serien-Architektur (Diagramme)

- `OBS.normalizeSheet(data)` liefert `{ name, labels, series:[{name,values}], min, max }`.
  Min/Max werden **global über alle Datenreihen** ermittelt → **gemeinsame
  Y-Skala**, keine Linie bricht aus dem Grid.
- `OBS.seriesStyle(i)` koppelt die Reihen an die CSS-Variablen:
  Reihe 0 → `var(--c-primary)`, 1 → `var(--c-accent)`, 2 → `var(--c-text)`;
  ab Reihe 3 wiederholen sich die Farben mit Strich-Muster (optisch getrennt,
  aber weiter live umfärbbar).
- Jedes Modul iteriert über `sheet.series` und erzeugt pro Reihe eigene
  `<path>`/`<rect>`/`<polygon>`-Elemente.

## 7. Gauges

Gauges ziehen einen Einzelwert aus einem Sheet via
`OBS.gaugeFromSheet(data)` – gesteuert über `?sheet=`, `?dataset=`, `?agg=`
(Standard `last`), optional `?min/?max/?unit/?label`.

## Lokaler Test

```bash
python3 export_data.py
# Variante A: direkt per Doppelklick (file://) öffnen
# Variante B: Server
python3 -m http.server 8000   # -> http://localhost:8000/customizer.html
```
