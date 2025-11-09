@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"

echo.
echo ========================================
echo   同步项目到 GitHub
echo ========================================
echo.
echo 仓库地址: https://github.com/QJHWC/awsq.git
echo.

:: 检查 Git 是否安装
where git >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ 未找到 Git
    echo.
    echo 请先安装 Git:
    echo https://git-scm.com/download/win
    echo.
    pause
    exit /b 1
)

echo ✅ Git 已安装
echo.

:: 检查是否已初始化
if not exist .git (
    echo 【步骤 1/4】初始化 Git 仓库...
    git init
    echo.
    
    echo 【步骤 2/4】添加远程仓库...
    git remote add origin https://github.com/QJHWC/awsq.git
    echo.
) else (
    echo ✅ Git 仓库已初始化
    echo.
    
    :: 检查远程仓库
    git remote get-url origin >nul 2>&1
    if %errorlevel% neq 0 (
        echo 添加远程仓库...
        git remote add origin https://github.com/QJHWC/awsq.git
    ) else (
        echo 更新远程仓库地址...
        git remote set-url origin https://github.com/QJHWC/awsq.git
    )
    echo.
)

echo 【步骤 3/4】添加文件到暂存区...
git add .
echo.

echo 【步骤 4/4】提交并推送到 GitHub...
echo.

:: 提示输入提交信息
set /p commit_msg="请输入提交说明（直接回车使用默认）: "
if "%commit_msg%"=="" set commit_msg=Update: Amazon Q to OpenAI API Bridge - Full Auto Registration

echo.
echo 提交信息: %commit_msg%
echo.

git commit -m "%commit_msg%"
echo.

echo 正在推送到 GitHub...
echo ⚠️ 可能需要输入 GitHub 用户名和密码/Token
echo.

git push -u origin main

if %errorlevel% equ 0 (
    echo.
    echo ========================================
    echo   ✅ 同步成功！
    echo ========================================
    echo.
    echo 🌐 访问你的仓库:
    echo    https://github.com/QJHWC/awsq
    echo.
) else (
    echo.
    echo ⚠️ 推送失败，可能是分支名称问题，尝试 master 分支...
    git push -u origin master
    
    if %errorlevel% equ 0 (
        echo.
        echo ========================================
        echo   ✅ 同步成功！
        echo ========================================
        echo.
        echo 🌐 访问你的仓库:
        echo    https://github.com/QJHWC/awsq
        echo.
    ) else (
        echo.
        echo ❌ 推送失败
        echo.
        echo 可能的原因：
        echo 1. 未配置 GitHub 认证
        echo 2. 没有推送权限
        echo 3. 网络问题
        echo.
        echo 解决方法：
        echo 1. 配置 Git 用户信息（见下方）
        echo 2. 使用 GitHub Token 认证（见 GitHub文档）
        echo 3. 检查网络连接
        echo.
    )
)

echo.
echo 💡 提示：
echo    如果首次使用 Git，需要配置用户信息：
echo    git config --global user.name "你的用户名"
echo    git config --global user.email "你的邮箱"
echo.
pause

