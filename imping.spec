# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec for IMPGING Q-Engine cross-platform desktop build.
"""
import os
import sys
from pathlib import Path

block_cipher = None

# Collect all IMPGING scripts
SKILLS_DIR = Path("../Skills/imping/scripts")
IMPGING_SCRIPTS = [
    str(SKILLS_DIR / "apk-scanner.py"),
    str(SKILLS_DIR / "game-detector.py"),
    str(SKILLS_DIR / "hardware-mapper.py"),
    str(SKILLS_DIR / "net-jammer.py"),
    str(SKILLS_DIR / "imping-status.py"),
]

a = Analysis(
    ["../imping-launcher.py"],
    pathex=[],
    binaries=[],
    datas=[
        (str(SKILLS_DIR), "Skills/imping/scripts"),
        ("../requirements.txt", "."),
    ],
    hiddenimports=[
        "psutil",
        "logging",
        "threading",
        "collections",
        "pathlib",
        "concurrent.futures",
    ],
    hookspath=[],
    hooksconfig={},
    keys=[],
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
    name="IMPGING",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="IMPGING",
)
