@echo off
rem Startet den Lesezeichen-Server und oeffnet die Seite im Browser.
rem Solange dieses Fenster offen ist, laeuft der Server. Fenster schliessen = Server stoppen.
cd /d "%~dp0"
start "" http://localhost:3000
node server.js
