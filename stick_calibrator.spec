# -*- mode: python ; coding: utf-8 -*-
import os
from pathlib import Path
import vgamepad
from PyInstaller.utils.hooks import collect_submodules

pathex = [os.path.abspath('.')]

block_cipher = None

hiddenimports = [
    "controllers",
    "controllers.gamepad_vigem",
    "detectors",
    "detectors.base",
    "detectors.manual",
    "i18n",
    "prereqs_installer",
    "vgamepad",
]

# Locate bundled ViGEm client DLLs inside vgamepad package
_vg_base = Path(vgamepad.__file__).parent
_dll_x64 = _vg_base / "win" / "vigem" / "client" / "x64" / "ViGEmClient.dll"
_dll_x86 = _vg_base / "win" / "vigem" / "client" / "x86" / "ViGEmClient.dll"

binaries = []
if _dll_x64.exists():
    binaries.append((str(_dll_x64), "vgamepad/win/vigem/client/x64"))
if _dll_x86.exists():
    binaries.append((str(_dll_x86), "vgamepad/win/vigem/client/x86"))

a = Analysis(
    ['launcher.py'],
    pathex=pathex,
    binaries=binaries,
    datas=[
        ('languages', 'languages'),
        ('prereqs', 'prereqs'),
        ('controllers', 'controllers'),
        ('detectors', 'detectors'),
    ],
    hiddenimports=hiddenimports,
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
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='游戏摇杆曲线探测器_v1.8.6',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    icon=os.path.join(pathex[0], "icon.ico"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='游戏摇杆曲线探测器_v1.8.6'
)
