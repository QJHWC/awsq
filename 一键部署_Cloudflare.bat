@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   一键部署到公网 (Cloudflare Tunnel)
echo ========================================
echo.

:: 检查 cloudflared 是否安装
where cloudflared >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 cloudflared
    echo.
    echo 请先下载 cloudflared:
    echo https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-windows-amd64.exe
    echo.
    echo 下载后重命名为 cloudflared.exe 并放到当前目录或系统 PATH
    echo.
    pause
    exit /b 1
)

echo ✅ 检查到 cloudflared
echo.

:: 启动本地服务（后台）
echo 【步骤 1/2】启动本地 API 服务...
start /b "" python -m uvicorn app:app --host 0.0.0.0 --port 8000

:: 等待服务启动
echo 等待服务启动...
timeout /t 5 /nobreak >nul

:: 启动内网穿透
echo.
echo 【步骤 2/2】启动 Cloudflare 内网穿透...
echo.
echo ========================================
echo   🚀 部署成功！
echo ========================================
echo.
echo 📋 下方会显示你的公网地址，格式如：
echo    https://xxxx-xxxx-xxxx.trycloudflare.com
echo.
echo 📱 客户端配置：
echo    API 地址：https://xxxx-xxxx-xxxx.trycloudflare.com/v1
echo    API 密钥：sk-790214
echo    模型：claude-sonnet-4.5
echo.
echo ========================================
echo.

cloudflared tunnel --url http://localhost:8000

pause

