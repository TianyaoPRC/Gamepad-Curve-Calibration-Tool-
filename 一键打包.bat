@echo off
chcp 65001 >nul
echo.
echo ================================
echo   Stick Calibrator 打包工具
echo ================================
echo.

echo 正在准备打包环境...
cd /d "%~dp0"

echo.
echo 检查Python环境...
python --version
if errorlevel 1 (
    echo 错误: 未找到Python，请先安装Python
    pause
    exit /b 1
)

echo.
echo 检查并安装PyInstaller...
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo 未找到PyInstaller，正在安装...
    pip install pyinstaller
    if errorlevel 1 (
        echo PyInstaller安装失败
        pause
        exit /b 1
    )
)

echo.
echo 检查并安装项目依赖...
if exist requirements.txt (
    pip install -r requirements.txt
    if errorlevel 1 (
        echo 依赖安装失败
        pause
        exit /b 1
    )
) else (
    echo 未找到requirements.txt文件
    pause
    exit /b 1
)

echo.
echo 开始打包...
echo.

python build.py

echo.
echo ================================
echo   打包完成
echo ================================
pause