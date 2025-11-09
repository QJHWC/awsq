@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   配置 API 密钥
echo ========================================
echo.
echo 当前密钥：sk-790214
echo.
echo 正在创建配置文件 .env ...
echo.

echo OPENAI_KEYS=sk-790214 > .env

if exist .env (
    echo ✅ 配置文件创建成功！
    echo.
    echo 📄 文件位置：.env
    echo 🔑 API 密钥：sk-790214
    echo.
    echo 下一步：双击运行 "启动公网服务.bat"
) else (
    echo ❌ 创建失败
)

echo.
pause

