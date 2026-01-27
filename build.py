# -*- coding: utf-8 -*-
"""
打包脚本，用于将stick_calibrator项目打包成单个exe文件
"""
import os
import sys
import subprocess
import shutil
from pathlib import Path

def install_pyinstaller():
    """安装PyInstaller"""
    print("正在安装PyInstaller...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("PyInstaller安装完成")
    except subprocess.CalledProcessError:
        print("PyInstaller安装失败")
        sys.exit(1)

def install_dependencies():
    """安装项目依赖"""
    print("正在安装项目依赖...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("项目依赖安装完成")
    except subprocess.CalledProcessError:
        print("项目依赖安装失败")
        sys.exit(1)

def create_dist_dir():
    """创建dist目录"""
    dist_path = Path("dist")
    dist_path.mkdir(exist_ok=True)
    return dist_path

def build_executable():
    """使用PyInstaller构建exe文件"""
    print("开始构建exe文件...")
    
    # 使用PyInstaller构建
    cmd = [
        "pyinstaller",
        "--onefile",           # 打包成单个exe文件
        "--windowed",          # 不显示控制台窗口
        "--add-data", "languages;languages",  # 包含语言文件
        "--add-data", "prereqs;prereqs",      # 包含前置条件安装文件
        "--hidden-import", "controllers.gamepad_vigem",
        "--hidden-import", "i18n",
        "--hidden-import", "prereqs_installer",
        "--clean",             # 清理临时文件
        "--noconfirm",         # 不需要确认覆盖
        "launcher.py"          # 主入口文件
    ]
    
    try:
        subprocess.check_call(cmd)
        print("exe文件构建完成")
    except subprocess.CalledProcessError as e:
        print(f"exe文件构建失败: {e}")
        sys.exit(1)

def main():
    """主函数"""
    print("开始打包stick_calibrator项目...")
    
    # 检查是否安装了PyInstaller
    try:
        import PyInstaller
    except ImportError:
        install_pyinstaller()
    
    # 安装项目依赖
    install_dependencies()
    
    # 构建exe文件
    build_executable()
    
    # 检查生成的exe文件
    dist_path = Path("dist/stick_calibrator.exe")
    if dist_path.exists():
        print(f"\n打包成功！生成的exe文件位于: {dist_path.absolute()}")
        print(f"文件大小: {dist_path.stat().st_size / (1024*1024):.2f} MB")
        
        # 检查prereqs目录是否存在，如果存在则复制到dist目录
        prereqs_path = Path("prereqs")
        if prereqs_path.exists():
            dest_prereqs = Path("dist/prereqs")
            if dest_prereqs.exists():
                shutil.rmtree(dest_prereqs)
            shutil.copytree(prereqs_path, dest_prereqs)
            print("已将prereqs目录复制到dist目录")
        
        # 检查languages目录是否存在，如果存在则复制到dist目录
        languages_path = Path("languages")
        if languages_path.exists():
            dest_languages = Path("dist/languages")
            if dest_languages.exists():
                shutil.rmtree(dest_languages)
            shutil.copytree(languages_path, dest_languages)
            print("已将languages目录复制到dist目录")
            
        print("\n注意: 如果目标计算机上没有安装ViGEmBus驱动，用户首次运行时程序会提示安装。")
        print("您需要将ViGEmBus安装程序放入prereqs文件夹中，以便程序可以自动安装驱动。")
    else:
        print("打包失败，未找到生成的exe文件")
        sys.exit(1)

if __name__ == "__main__":
    main()