# Lesezeichen-Verzeichnis

Eine lokale HTML-Seite, die wie ein Lesezeichen-Verzeichnis funktioniert –
für den Desktop in **6 Spalten** dargestellt.

## Funktionen

- **6 Spalten**, deren Namen frei vergeben werden können (in den Spaltenkopf klicken).
- In jeder Spalte lassen sich **URLs** speichern sowie **benennbare Verzeichnisse
  und Unterverzeichnisse** (beliebig tief verschachtelt) anlegen, die wiederum URLs enthalten.
- Verzeichnisse **öffnen sich beim Überfahren mit der Maus**. Die Anzeige nutzt
  die **gesamte Bildschirmhöhe** und klappt verschachtelte Ebenen seitlich aus.
- **Löschfunktion** für URLs, Verzeichnisse und Unterverzeichnisse
  (jeweils das `×` am Eintrag), inklusive **Bearbeiten** (`✎`).
- **Export / Import** der gesamten Sammlung als JSON-Datei sowie **Zurücksetzen**.
- Die Daten werden lokal im Browser (`localStorage`) gespeichert – keine Cloud,
  kein Konto nötig.

## Starten

Voraussetzung: Node.js ist installiert.

```bash
node server.js
```

Anschließend im Browser öffnen: <http://localhost:3000>

> Alternativ kann `index.html` auch direkt per Doppelklick im Browser geöffnet
> werden. Der Node-Server wird nur benötigt, um die Seite über `http://` auszuliefern
> (z. B. für korrekte Favicon-Anzeige).

Den Port kann man per Umgebungsvariable ändern: `PORT=8080 node server.js`.

## Per Datei / Taskleiste starten (Windows)

Statt jedes Mal `node server.js` zu tippen, liegen fertige Starter bei:

- **`Lesezeichen starten.bat`** – Doppelklick: öffnet ein kleines Konsolenfenster
  (= der laufende Server) und ruft die Seite im Browser auf. Das Fenster schließen
  beendet den Server.
- **`Lesezeichen starten.vbs`** – startet den Server **ohne sichtbares Fenster** im
  Hintergrund und öffnet den Browser. Am besten zum Anheften an die Taskleiste.
- **`Lesezeichen stoppen.bat`** – beendet einen im Hintergrund laufenden Server
  (nur nötig, wenn per `.vbs` gestartet).

### An die Taskleiste anheften

1. Rechtsklick auf **`Lesezeichen starten.vbs`** → **Verknüpfung erstellen**.
2. Falls beim Rechtsklick auf die Verknüpfung **„An Taskleiste anheften“** fehlt:
   Rechtsklick auf die Verknüpfung → **Eigenschaften** → Feld **Ziel** voranstellen mit
   `wscript.exe ` (also z. B. `wscript.exe "C:\Pfad\zu\Lesezeichen starten.vbs"`).
   Danach erscheint die Option.
3. Optional unter **Eigenschaften → Anderes Symbol** ein eigenes Icon wählen.
4. Verknüpfung an die Taskleiste ziehen bzw. **An Taskleiste anheften**.

> Hinweis: Node.js muss installiert und im `PATH` sein (Test: `node -v` in der
> Eingabeaufforderung). Liegt das Projekt in einem Pfad mit Leerzeichen, sind die
> mitgelieferten Starter bereits darauf vorbereitet.

### macOS / Linux

Eine ausführbare Startdatei anlegen, z. B. `start.command` (macOS) bzw. `start.sh`:

```bash
#!/bin/bash
cd "$(dirname "$0")"
node server.js &
sleep 1
open http://localhost:3000   # macOS; unter Linux: xdg-open http://localhost:3000
```

Danach `chmod +x start.command` ausführen – Doppelklick startet den Server.

## Bedienung

| Aktion | So geht's |
| --- | --- |
| Spalte umbenennen | In den Spaltennamen klicken und tippen |
| URL hinzufügen | `+ URL` in der Spalte (oder im geöffneten Verzeichnis) |
| Verzeichnis anlegen | `+ Verzeichnis` in der Spalte oder im Verzeichnis |
| Verzeichnis öffnen | Mit der Maus über den Verzeichnisnamen fahren |
| Eintrag bearbeiten | `✎` neben dem Eintrag |
| Eintrag löschen | `×` neben dem Eintrag |
