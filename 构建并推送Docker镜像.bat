@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   构建并推送 Docker 镜像到 Docker Hub
echo ========================================
echo.
echo 目标仓库: https://hub.docker.com/r/qjhwc/awsq
echo 镜像名称: qjhwc/awsq:latest
echo.

:: 检查 Docker 是否安装
where docker >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Docker
    echo.
    echo 请先安装 Docker Desktop:
    echo https://www.docker.com/products/docker-desktop/
    echo.
    pause
    exit /b 1
)

echo ✅ Docker 已安装
docker --version
echo.

:: 检查 Docker 是否运行
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker 未运行
    echo.
    echo 请先启动 Docker Desktop
    echo.
    pause
    exit /b 1
)

echo ✅ Docker 正在运行
echo.

:: 登录 Docker Hub
echo 【步骤 1/3】登录 Docker Hub
echo ========================================
echo.
echo 请输入你的 Docker Hub 凭据
echo （如果还没有账号，请先访问 https://hub.docker.com 注册）
echo.

docker login

if %errorlevel% neq 0 (
    echo.
    echo ❌ 登录失败
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 登录成功
echo.

:: 构建镜像
echo 【步骤 2/3】构建 Docker 镜像
echo ========================================
echo.
echo 正在构建镜像 qjhwc/awsq:latest ...
echo 这可能需要几分钟时间...
echo.

docker build -t qjhwc/awsq:latest .

if %errorlevel% neq 0 (
    echo.
    echo ❌ 构建失败
    echo.
    echo 请检查：
    echo 1. Dockerfile 是否正确
    echo 2. requirements.txt 是否存在
    echo 3. 项目文件是否完整
    echo.
    pause
    exit /b 1
)

echo.
echo ✅ 构建成功
echo.

:: 推送镜像
echo 【步骤 3/3】推送镜像到 Docker Hub
echo ========================================
echo.
echo 正在推送 qjhwc/awsq:latest 到 Docker Hub...
echo 这可能需要几分钟时间（取决于网络速度）...
echo.

docker push qjhwc/awsq:latest

if %errorlevel% neq 0 (
    echo.
    echo ❌ 推送失败
    echo.
    echo 可能的原因：
    echo 1. 网络连接问题
    echo 2. 没有推送权限
    echo 3. 仓库名称错误
    echo.
    pause
    exit /b 1
)

echo.
echo ========================================
echo   ✅ 推送成功！
echo ========================================
echo.
echo 🌐 镜像地址:
echo    https://hub.docker.com/r/qjhwc/awsq
echo.
echo 📦 镜像名称:
echo    qjhwc/awsq:latest
echo.
echo 💡 使用方法:
echo.
echo    【本地运行】
echo    docker run -p 8000:8000 -e OPENAI_KEYS=sk-790214 qjhwc/awsq:latest
echo.
echo    【claw.cloud 部署】
echo    Image Name: qjhwc/awsq:latest
echo    Container Port: 8000
echo    Environment Variables: OPENAI_KEYS=sk-790214
echo.
echo 🎉 现在可以在 claw.cloud 使用这个镜像了！
echo.
pause

