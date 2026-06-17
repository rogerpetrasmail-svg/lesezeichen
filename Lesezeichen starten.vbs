' Startet den Lesezeichen-Server OHNE sichtbares Konsolenfenster
' und oeffnet anschliessend die Seite im Standardbrowser.
' Ideal zum Anheften an die Taskleiste (siehe README).
Set sh = CreateObject("WScript.Shell")
scriptDir = CreateObject("Scripting.FileSystemObject").GetParentFolderName(WScript.ScriptFullName)
sh.CurrentDirectory = scriptDir

' Server unsichtbar starten (0 = kein Fenster)
sh.Run "node server.js", 0, False

' kurz warten, dann Browser oeffnen
WScript.Sleep 800
sh.Run "http://localhost:3000", 1, False
