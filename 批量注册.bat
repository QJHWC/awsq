@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
py 批量注册.py
pause

