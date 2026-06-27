"""Start-Skript (auch Einstiegspunkt für PyInstaller).

Start im Entwicklungsmodus:
    python run.py
"""

from app.main import main

if __name__ == "__main__":
    raise SystemExit(main())
