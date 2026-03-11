@echo off
title ANPR System Setup
color 0A
echo.
echo  ============================================================
echo   Automatic Number Plate Recognition - Setup
echo  ============================================================
echo.

REM Check Python installation
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo  [ERROR] Python is not installed or not in PATH.
    echo  Please install Python 3.9+ from https://python.org
    pause
    exit /b 1
)

echo  [1/4] Creating Python virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo  [ERROR] Failed to create virtual environment.
    pause
    exit /b 1
)
echo  [OK] Virtual environment created.
echo.

echo  [2/4] Activating virtual environment...
call venv\Scripts\activate.bat
echo  [OK] Activated.
echo.

echo  [3/4] Installing dependencies (this may take a few minutes)...
pip install --upgrade pip --quiet
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo  [ERROR] Dependency installation failed. Check your internet connection.
    pause
    exit /b 1
)
echo  [OK] All dependencies installed.
echo.

echo  [4/4] Creating output directory...
if not exist outputs mkdir outputs
echo  [OK] Done.
echo.
echo  ============================================================
echo   Setup Complete!
echo  ============================================================
echo.
echo   To start the application, run:  run.bat
echo   Then open:  http://localhost:8000
echo.
pause
