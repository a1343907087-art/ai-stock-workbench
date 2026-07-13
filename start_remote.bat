@echo off
chcp 65001 >nul
title AI炒股工作台 - 远程启动

echo ================================================
echo    📊 AI 炒股工作台 - 远程访问启动器
echo ================================================
echo.

echo 🔍 检查Python环境...
call conda activate trading
if errorlevel 1 (
    echo ❌ 无法激活 trading 环境
    pause
    exit /b 1
)
echo ✅ 环境激活成功

echo.
echo 🚀 启动系统...
echo    提示：按 Ctrl+C 可停止所有服务
echo.

echo 📡 正在启动 ngrok（外网访问）...
start ngrok http 5000

echo.
echo ⏳ 等待系统启动...
timeout /t 3 /nobreak >nul

echo.
echo 🌐 本地访问: http://127.0.0.1:5000
echo 🌐 外网访问: 请查看 ngrok 窗口中的 Forwarding 地址
echo 📱 在手机上打开外网地址即可访问
echo.
echo ================================================

python main.py

pause