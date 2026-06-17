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

## Bedienung

| Aktion | So geht's |
| --- | --- |
| Spalte umbenennen | In den Spaltennamen klicken und tippen |
| URL hinzufügen | `+ URL` in der Spalte (oder im geöffneten Verzeichnis) |
| Verzeichnis anlegen | `+ Verzeichnis` in der Spalte oder im Verzeichnis |
| Verzeichnis öffnen | Mit der Maus über den Verzeichnisnamen fahren |
| Eintrag bearbeiten | `✎` neben dem Eintrag |
| Eintrag löschen | `×` neben dem Eintrag |
