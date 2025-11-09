@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   Ngrok 内网穿透
echo ========================================
echo.
echo 【前置条件】
echo 1. 已安装 ngrok
echo    下载地址：https://ngrok.com/download
echo.
echo 2. 已注册 ngrok 账号并获取 authtoken
echo    注册地址：https://dashboard.ngrok.com/signup
echo    设置 token：ngrok authtoken YOUR_TOKEN
echo.
echo ========================================
echo.

echo 正在启动内网穿透...
echo.

ngrok http 8000

echo.
echo ⚠️ 如果出现错误，请确保：
echo    1. ngrok 已正确安装
echo    2. 已配置 authtoken
echo    3. 本地服务已启动（端口 8000）
echo.
pause

