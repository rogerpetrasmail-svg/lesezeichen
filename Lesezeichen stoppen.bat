@echo off
rem Stoppt einen im Hintergrund laufenden Lesezeichen-Server (gestartet per .vbs).
taskkill /f /im node.exe >nul 2>&1
echo Lesezeichen-Server gestoppt.
timeout /t 1 >nul
