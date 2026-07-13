@echo off
chcp 65001 >nul
title AI炒股工作台 - 一键启动

echo ================================================
echo    📊 AI 炒股工作台 - 一键启动
echo ================================================
echo.

echo 🚀 正在启动系统...
echo    提示：按 Ctrl+C 可停止所有服务
echo.

cd /d C:\Users\Administrator\Desktop\ai_trading_workbench

echo ✅ 启动定时任务（备份调度器）...
start /min D:\Anaconda3\envs\trading\python.exe scheduler.py

echo ✅ 启动进程守护（崩溃自动重启）...
start /min D:\Anaconda3\envs\trading\python.exe watchdog.py

echo ✅ 启动主系统...
D:\Anaconda3\envs\trading\python.exe main.py

pause