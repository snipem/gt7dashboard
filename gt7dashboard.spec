# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec file for GT7 Dashboard.

Build locally (on Windows):
    pip install pyinstaller
    pyinstaller gt7dashboard.spec

The output is a one-directory bundle at dist/gt7dashboard/.
Zip that directory and share it — users only need to extract and
double-click gt7dashboard.exe.
"""

import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Collect all data files, binaries and hidden imports for the heavy packages.
bokeh_datas, bokeh_binaries, bokeh_hiddenimports = collect_all("bokeh")
scipy_datas, scipy_binaries, scipy_hiddenimports = collect_all("scipy")
pandas_datas, pandas_binaries, pandas_hiddenimports = collect_all("pandas")

# Core application files that Bokeh's DirectoryHandler needs to find at runtime.
app_datas = [
    ("main.py", "."),
    ("gt7dashboard", "gt7dashboard"),
]

# Include the car-name database if it was downloaded before the build.
if os.path.exists("db/cars.csv"):
    app_datas.append(("db", "db"))

a = Analysis(
    ["gt7dashboard_launcher.py"],
    pathex=[],
    binaries=bokeh_binaries + scipy_binaries + pandas_binaries,
    datas=app_datas + bokeh_datas + scipy_datas + pandas_datas,
    hiddenimports=(
        bokeh_hiddenimports
        + scipy_hiddenimports
        + pandas_hiddenimports
        + [
            "bokeh.application.handlers.directory",
            "bokeh.server.server",
            "bokeh.server.views.ws",
            "Crypto",
            "Crypto.Cipher",
            "Crypto.Cipher.Salsa20",
            "tabulate",
            "tkinter",
            "tkinter.simpledialog",
        ]
    ),
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
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
    name="gt7dashboard",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # Keep the console window open so users can see connection status and errors.
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
    name="gt7dashboard",
)
