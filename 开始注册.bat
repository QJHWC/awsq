@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
py amazonq_auto_register.py
pause

