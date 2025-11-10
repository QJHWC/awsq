@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   启动本地测试服务器
echo ========================================
echo.
echo 📍 工作目录: %CD%
echo 🌐 服务地址: http://localhost:8000
echo 📖 API 文档: http://localhost:8000/docs
echo 🏥 健康检查: http://localhost:8000/healthz
echo.
echo 按 Ctrl+C 停止服务器
echo.
echo ========================================
echo.

C:\Users\QJHWC\AppData\Local\Programs\Python\Python310\python.exe -m uvicorn app:app --host 127.0.0.1 --port 8000 --reload

if %errorlevel% neq 0 (
    echo.
    echo ❌ 启动失败！
    echo.
    echo 可能原因：
    echo 1. Python 路径不正确
    echo 2. 依赖未安装：pip install -r requirements.txt
    echo 3. 端口8000已被占用
    echo.
)

pause

