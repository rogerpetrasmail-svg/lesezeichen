# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-Spec für die eigenständige Windows-.exe.

Bauen (auf Windows):
    pyinstaller packaging/rss_rechercheur.spec --noconfirm
Ergebnis:
    dist/RSS-Rechercheur/RSS-Rechercheur.exe   (One-Folder, schneller Start)
"""

import os

block_cipher = None

# Pfad zum Projekt-Wurzelverzeichnis (eine Ebene über packaging/)
ROOT = os.path.abspath(os.path.join(os.getcwd()))

icon_path = os.path.join("packaging", "app.ico")
if not os.path.exists(icon_path):
    icon_path = None

a = Analysis(
    ["run.py"],
    pathex=[ROOT],
    binaries=[],
    datas=[],
    hiddenimports=[
        "feedparser",
        "openpyxl",
        "requests",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=["tkinter", "PyQt5", "PyQt6", "matplotlib", "numpy", "PIL"],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="RSS-Rechercheur",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,  # GUI-Anwendung: kein Konsolenfenster
    disable_windowed_traceback=False,
    icon=icon_path,
    version=os.path.join("packaging", "version_info.txt"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="RSS-Rechercheur",
)
