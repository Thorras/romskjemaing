@echo off
REM Quick launcher for Romskjema Generator - Enhanced Room Schedule Application

echo ========================================
echo Romskjema Generator v2.0.0 Launcher
echo Enhanced Room Schedule Generator
echo ========================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Check if main.py exists
if not exist main.py (
    echo ERROR: main.py not found in current directory
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
python -c "import ifcopenshell, pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo ERROR: Failed to install dependencies
        pause
        exit /b 1
    )
)

echo Dependencies OK!
echo.
echo Starting Romskjema Generator...
echo.
echo Available modes:
echo   GUI Mode: python main.py --gui
echo   CLI Mode: python main.py --help
echo.

REM Run the application in GUI mode by default
python main.py --gui

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)