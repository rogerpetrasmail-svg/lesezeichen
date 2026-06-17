# Icon in .ico umwandeln

Die Datei `lesezeichen.svg` ist ein Vektor-Icon (Lesezeichen-Motiv mit 6 Spalten). 
Um es als `.ico` für die Taskleiste zu nutzen, muss es konvertiert werden.

## Option 1: Online-Tool (einfachste Variante)

1. Gehe zu **https://convertio.co/de/svg-ico/** oder **https://icoconvert.com/**
2. Lade `lesezeichen.svg` hoch
3. Konvertiere zu `.ico`
4. Speichere `lesezeichen.ico` im Projektordner

## Option 2: Mit ImageMagick (lokal)

Falls du ImageMagick installiert hast:

```bash
convert -background none -density 256x256 -resize 256x256 lesezeichen.svg lesezeichen.ico
```

## Option 3: Mit Inkscape

1. Öffne `lesezeichen.svg` in Inkscape
2. **Datei → Export als...** → Format: **Icon (.ico)**
3. Speichern

## Anschließend in der Verknüpfung nutzen

Rechtsklick auf die Verknüpfung **`Lesezeichen starten.vbs`** → **Eigenschaften** → 
**Anderes Symbol** → wähle `lesezeichen.ico` aus dem Projektordner.

Fertig!
