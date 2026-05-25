@echo off
chcp 65001 >nul
cd /d "%~dp0"

echo ========================================
echo   问元 Wenyuan - 探问天地人三元
echo ========================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH
    pause
    exit /b 1
)

if not exist "venv\Scripts\python.exe" (
    echo [1/3] 创建虚拟环境...
    python -m venv venv
    if errorlevel 1 (
        echo [错误] 创建虚拟环境失败
        pause
        exit /b 1
    )
) else (
    echo [1/3] 虚拟环境已存在
)

echo [2/3] 安装依赖...
call venv\Scripts\activate.bat
python -m pip install -r requirements.txt -q
if errorlevel 1 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

if not exist ".env" (
    copy .env.example .env >nul
    echo [提示] 已从 .env.example 创建 .env，如需 AI 解读请配置 DEEPSEEK_API_KEY
)

echo [3/3] 启动服务...
echo.
echo   主页: http://localhost:8000
echo   文档: http://localhost:8000/docs
echo   按 Ctrl+C 停止
echo.

python run.py

pause
