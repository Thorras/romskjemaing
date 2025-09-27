#!/bin/bash
# Quick launcher for IFC Room Schedule Application

echo "========================================"
echo "IFC Room Schedule Application Launcher"
echo "========================================"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

echo "Python found: $(python3 --version)"

# Check if main.py exists
if [ ! -f "main.py" ]; then
    echo "ERROR: main.py not found in current directory"
    echo "Please run this script from the project root directory"
    exit 1
fi

# Check if requirements are installed
echo "Checking dependencies..."
if ! python3 -c "import PyQt6, ifcopenshell, pandas" &> /dev/null; then
    echo "Installing missing dependencies..."
    if ! pip3 install -r requirements.txt; then
        echo "ERROR: Failed to install dependencies"
        exit 1
    fi
fi

echo "Dependencies OK!"
echo ""
echo "Starting IFC Room Schedule Application..."
echo ""

# Set display for Linux
if [[ "$OSTYPE" == "linux-gnu"* ]]; then
    export QT_QPA_PLATFORM=xcb
fi

# Run the application
python3 main.py

# Check exit code
if [ $? -ne 0 ]; then
    echo ""
    echo "Application exited with error code $?"
    read -p "Press Enter to continue..."
fi