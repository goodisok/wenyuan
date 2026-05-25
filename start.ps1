# 问元 Wenyuan 启动脚本 (PowerShell)
$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

Write-Host "========================================"
Write-Host "  问元 Wenyuan - 探问天地人三元"
Write-Host "========================================"
Write-Host ""

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "[错误] 未找到 Python，请先安装 Python 3.10+ 并加入 PATH" -ForegroundColor Red
    exit 1
}

$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "[1/3] 创建虚拟环境..."
    python -m venv venv
} else {
    Write-Host "[1/3] 虚拟环境已存在"
}

Write-Host "[2/3] 安装依赖..."
& $venvPython -m pip install -r requirements.txt -q

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "[提示] 已从 .env.example 创建 .env，如需 AI 解读请配置 DEEPSEEK_API_KEY" -ForegroundColor Yellow
}

Write-Host "[3/3] 启动服务..."
Write-Host ""
Write-Host "  主页: http://localhost:8000"
Write-Host "  文档: http://localhost:8000/docs"
Write-Host "  按 Ctrl+C 停止"
Write-Host ""

& $venvPython run.py
