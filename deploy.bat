@echo off
REM IFC Room Schedule Application - Windows Deployment Script

echo ========================================
echo IFC Room Schedule Application Deployer
echo ========================================

REM Check Python installation
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo Python found: 
python --version

REM Create virtual environment
echo.
echo Creating virtual environment...
if exist venv rmdir /s /q venv
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install dependencies
echo Installing dependencies...
pip install -r requirements.txt

REM Install PyInstaller for executable build
echo Installing PyInstaller...
pip install pyinstaller

REM Run tests
echo.
echo Running tests...
python -m pytest tests/ -v --tb=short
if errorlevel 1 (
    echo WARNING: Some tests failed. Continue anyway? (Y/N)
    set /p continue=
    if /i not "%continue%"=="Y" exit /b 1
)

REM Build executable
echo.
echo Building executable...
python build_executable.py

REM Create installer (optional)
if exist "C:\Program Files (x86)\NSIS\makensis.exe" (
    echo Creating installer...
    "C:\Program Files (x86)\NSIS\makensis.exe" installer.nsi
) else (
    echo NSIS not found. Skipping installer creation.
    echo Download NSIS from https://nsis.sourceforge.io/ to create installer.
)

echo.
echo ========================================
echo Deployment completed successfully!
echo ========================================
echo.
echo Files created:
echo - dist\IFC-Room-Schedule.exe (Standalone executable)
echo - deployment\ (Complete package)
echo.
echo To run the application:
echo 1. Navigate to deployment folder
echo 2. Double-click IFC-Room-Schedule.exe
echo.
pause