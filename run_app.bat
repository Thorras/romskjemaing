@echo off
REM Quick launcher for Romskjema Generator - Enhanced Room Schedule Application

echo ========================================
echo Romskjema Generator v2.0.0 Launcher
echo Enhanced Room Schedule Generator
echo ========================================

REM Check if Python 3.11 is available
echo Checking for Python 3.11...

REM Try py launcher with 3.11 first (Windows Python Launcher)
py -3.11 --version >nul 2>&1
if not errorlevel 1 (
    echo Python 3.11 found via py launcher:
    py -3.11 --version
    set PYTHON_CMD=py -3.11
    goto :python_found
)

REM Try python3.11 command
python3.11 --version >nul 2>&1
if not errorlevel 1 (
    echo Python 3.11 found:
    python3.11 --version
    set PYTHON_CMD=python3.11
    goto :python_found
)

REM Check if default python is 3.11
python --version 2>&1 | findstr "3.11" >nul
if not errorlevel 1 (
    echo Python 3.11 found (default):
    python --version
    set PYTHON_CMD=python
    goto :python_found
)

REM Python 3.11 not found
echo ERROR: Python 3.11 is required but not found
echo.
echo This application requires Python 3.11 specifically.
echo Current Python version:
python --version 2>nul || echo   No Python found in PATH
echo.
echo Please install Python 3.11 from:
echo   https://www.python.org/downloads/release/python-3118/
echo.
echo Or use Windows Python Launcher: py -3.11
pause
exit /b 1

:python_found

REM Check if main.py exists
if not exist main.py (
    echo ERROR: main.py not found in current directory
    echo Please run this script from the project root directory
    pause
    exit /b 1
)

REM Check if requirements are installed
echo Checking dependencies...
%PYTHON_CMD% -c "import ifcopenshell, pandas, numpy" >nul 2>&1
if errorlevel 1 (
    echo Installing missing dependencies...
    %PYTHON_CMD% -m pip install -r requirements.txt
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
echo   GUI Mode: %PYTHON_CMD% main.py --gui
echo   CLI Mode: %PYTHON_CMD% main.py --help
echo.

REM Run the application in GUI mode by default
%PYTHON_CMD% main.py --gui

REM Keep window open if there was an error
if errorlevel 1 (
    echo.
    echo Application exited with error code %errorlevel%
    pause
)