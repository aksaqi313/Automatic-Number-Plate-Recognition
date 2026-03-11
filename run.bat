@echo off
title ANPR System - Running
color 0B
echo.
echo  ============================================================
echo   Automatic Number Plate Recognition - Starting Server
echo  ============================================================
echo.

REM Check if venv exists
if not exist venv (
    echo  [ERROR] Virtual environment not found.
    echo  Please run setup.bat first!
    pause
    exit /b 1
)

echo  Activating virtual environment...
call venv\Scripts\activate.bat

echo  Starting ANPR server...
echo.
echo  ============================================================
echo   Open your browser and go to:
echo   http://localhost:8000 
echo  ============================================================
echo.
echo  Press Ctrl+C to stop the server.
echo.


python -m uvicorn app:app --host 0.0.0.0 --port 8000 --reload
