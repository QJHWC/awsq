@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   Cloudflare Tunnel 内网穿透
echo ========================================
echo.
echo 【前置条件】
echo 1. 已安装 Cloudflare Tunnel (cloudflared)
echo    下载地址：https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation/
echo.
echo 2. 已注册 Cloudflare 账号
echo    注册地址：https://dash.cloudflare.com/sign-up
echo.
echo ========================================
echo.

echo 正在启动内网穿透...
echo.

cloudflared tunnel --url http://localhost:8000

echo.
echo ⚠️ 如果出现错误，请确保：
echo    1. cloudflared 已正确安装
echo    2. 本地服务已启动（端口 8000）
echo.
pause

