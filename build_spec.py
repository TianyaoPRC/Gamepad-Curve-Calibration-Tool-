# -*- coding: utf-8 -*-
# -*- mode: python -*-
"""
打包规范文件，用于将stick_calibrator项目打包成单个exe文件
"""

import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules
from PyInstaller.building.build_main import Analysis, EXE
from PyInstaller.building.api import COLLECT, MERGE
from PyInstaller.archive.writers import ZlibArchiveWriter

# 获取项目根目录
basedir = os.path.dirname(os.path.abspath(__file__))

# 分析入口
a = Analysis(
    ['launcher.py'],  # 主入口文件
    pathex=[basedir],  # Python模块搜索路径
    binaries=[],  # 额外二进制文件
    datas=[
        # 包含语言文件
        ('languages', 'languages'),
        # 如果有prereqs目录，也要包含
        ('prereqs', 'prereqs'),
    ],
    hiddenimports=[
        # 隐藏导入，这些是动态导入但PyInstaller无法检测到的模块
        'controllers',
        'controllers.gamepad_vigem',
        'detectors',
        'detectors.base',
        'detectors.manual',
        'i18n',
        'prereqs_installer',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# 为Windows平台排除一些不需要的模块
if a.binaries:
    # 排除tkinter的tcl/tk相关文件以减小体积
    a.binaries = a.binaries - [('tcl85.dll', None, None), ('tk85.dll', None, None)]

# 收集pyz
pyz = ZlibArchiveWriter(
    name='stick_calibrator.pyz',
    cdict=None,
    threshold=8192,
    compresslevel=6,
    cipher=None,
)

# 创建exe
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='stick_calibrator',  # 输出exe名称
    debug=False,  # 不输出调试信息
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # 启用UPX压缩
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 不显示控制台窗口
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico',  # 如果有图标文件的话
)