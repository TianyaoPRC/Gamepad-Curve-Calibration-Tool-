# -*- mode: python ; coding: utf-8 -*-

import os
from PyInstaller.utils.hooks import collect_submodules, collect_data_files

block_cipher = None

# PyInstaller 在执行 spec 时会提供 SPECPATH（spec 文件所在目录）
BASE_DIR = os.path.abspath(SPECPATH)

# =========================
# 1) hiddenimports / datas
# =========================
hiddenimports = []
hiddenimports += collect_submodules("vgamepad")
hiddenimports += collect_submodules("controllers")

datas = []
binaries = []

# vgamepad 的数据文件（如果有）
datas += collect_data_files("vgamepad", include_py_files=False)

# 把 prereqs 目录打进包里（驱动/VC++ 安装器）
prereqs_dir = os.path.join(BASE_DIR, "prereqs")
if os.path.isdir(prereqs_dir):
    datas += [(prereqs_dir, "prereqs")]

# （可选）assets / configs
assets_dir = os.path.join(BASE_DIR, "assets")
if os.path.isdir(assets_dir):
    datas += [(assets_dir, "assets")]

configs_dir = os.path.join(BASE_DIR, "configs")
if os.path.isdir(configs_dir):
    datas += [(configs_dir, "configs")]

# =========================
# 2) 强制打包 ViGEmClient.dll
# =========================
try:
    import vgamepad
    vgamepad_dir = os.path.dirname(vgamepad.__file__)
except Exception:
    vgamepad_dir = None

if vgamepad_dir:
    dll_rel_path = os.path.join("win", "vigem", "client", "x64", "ViGEmClient.dll")
    dll_abs_path = os.path.join(vgamepad_dir, dll_rel_path)

    if os.path.exists(dll_abs_path):
        binaries += [
            (
                dll_abs_path,
                os.path.join("vgamepad", "win", "vigem", "client", "x64"),
            )
        ]
    else:
        # 兜底：在 vgamepad 包内递归搜索
        for root, _, files in os.walk(vgamepad_dir):
            for f in files:
                if f.lower() == "vigemclient.dll":
                    binaries += [
                        (
                            os.path.join(root, f),
                            os.path.join(
                                "vgamepad",
                                os.path.relpath(root, vgamepad_dir),
                            ),
                        )
                    ]
                    break

# =========================
# 3) 入口脚本（关键）
# =========================
# 必须是 launcher.py，先检测并安装 ViGEmBus，再启动 UI
entry_script = os.path.join(BASE_DIR, "launcher.py")

a = Analysis(
    [entry_script],
    pathex=[BASE_DIR],
    binaries=binaries,
    datas=datas,
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
    name="stick_calibrator",   # ← EXE 名字保持不变
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
