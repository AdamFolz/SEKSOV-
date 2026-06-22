@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %ERRORLEVEL%==0 (
    set "PY_CMD=py -3"
) else (
    where python >nul 2>nul
    if %ERRORLEVEL%==0 (
        set "PY_CMD=python"
    ) else (
        echo Python is not installed or is not in PATH.
        echo Install Python 3.11+ from https://www.python.org/downloads/ and enable "Add python.exe to PATH".
        exit /b 1
    )
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    %PY_CMD% -m venv .venv
    if errorlevel 1 exit /b 1
)

echo Installing dependencies from requirements.txt ...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 exit /b 1
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 exit /b 1

if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo Created .env from .env.example. Fill BOT_TOKEN and access settings, then run start.bat again.
    exit /b 1
)

echo Starting SEKSOV bot ...
".venv\Scripts\python.exe" run.py
