@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   Amazon Q API - 公网部署模式
echo ========================================
echo.
echo ✅ 配置文件：.env
echo ✅ API 密钥：sk-790214
echo ✅ 监听地址：0.0.0.0:8000
echo.
echo 服务启动后可通过以下方式访问：
echo   本地：http://localhost:8000
echo   局域网：http://你的局域网IP:8000
echo   公网：需要配置端口转发或内网穿透
echo.
echo ========================================
echo.

python -m uvicorn app:app --host 0.0.0.0 --port 8000

pause

