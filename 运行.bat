@echo off
chcp 65001 >nul
title 桌面宠物 Desktop Pet
echo ============================================
echo   桌面宠物 Desktop Pet 启动器
echo ============================================
echo.

REM 检查 Python 是否安装
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未检测到 Python，请先安装 Python 3.8+
    echo 下载地址: https://www.python.org/downloads/
    echo 安装时请务必勾选 "Add Python to PATH"
    echo.
    pause
    exit /b 1
)

echo [信息] Python 已就绪，正在启动桌宠...
echo.

REM 检查可选依赖
python -c "import sounddevice" 2>nul
if %errorlevel% neq 0 (
    echo [提示] 未安装声音检测依赖(sounddevice/numpy)，跳舞功能将不可用
    echo        如需启用声音跳舞，请运行: pip install sounddevice numpy
    echo.
)

REM 启动程序
python "%~dp0pet.py"

if %errorlevel% neq 0 (
    echo.
    echo [错误] 程序运行出错，请检查 Python 环境
    pause
)
