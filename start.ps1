$ErrorActionPreference = "Stop"
Set-Location -Path $PSScriptRoot

function Invoke-ProjectPython {
    param([string[]]$Arguments)
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 @Arguments
        return
    }
    if (Get-Command python -ErrorAction SilentlyContinue) {
        & python @Arguments
        return
    }
    throw "Python is not installed or is not in PATH. Install Python 3.11+ from https://www.python.org/downloads/ and enable 'Add python.exe to PATH'."
}

if (-not (Test-Path ".\.venv\Scripts\python.exe")) {
    Write-Host "Creating virtual environment in .venv ..."
    Invoke-ProjectPython -Arguments @("-m", "venv", ".venv")
}

$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"

Write-Host "Installing dependencies from requirements.txt ..."
& $VenvPython -m pip install --upgrade pip
& $VenvPython -m pip install -r requirements.txt

if (-not (Test-Path ".\.env")) {
    Copy-Item ".\.env.example" ".\.env"
    Write-Host "Created .env from .env.example. Fill BOT_TOKEN and AUTHORIZED_TELEGRAM_USER_IDS, then run this script again."
    exit 1
}

Write-Host "Starting SEKSOV bot ..."
& $VenvPython run.py
