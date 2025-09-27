#!/bin/bash
# IFC Room Schedule Application - Unix/Linux/macOS Deployment Script

set -e  # Exit on any error

echo "========================================"
echo "IFC Room Schedule Application Deployer"
echo "========================================"

# Check Python installation
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.8+ from your package manager"
    exit 1
fi

echo "Python found: $(python3 --version)"

# Create virtual environment
echo ""
echo "Creating virtual environment..."
rm -rf venv
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Install PyInstaller for executable build
echo "Installing PyInstaller..."
pip install pyinstaller

# Run tests
echo ""
echo "Running tests..."
if ! python -m pytest tests/ -v --tb=short; then
    echo "WARNING: Some tests failed. Continue anyway? (y/N)"
    read -r continue
    if [[ ! "$continue" =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Build executable
echo ""
echo "Building executable..."
python build_executable.py

# Create .app bundle on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Creating macOS app bundle..."
    # Additional macOS-specific packaging could go here
fi

# Create .deb package on Ubuntu/Debian
if command -v dpkg-deb &> /dev/null; then
    echo "Creating .deb package..."
    # Additional Debian packaging could go here
fi

echo ""
echo "========================================"
echo "Deployment completed successfully!"
echo "========================================"
echo ""
echo "Files created:"
echo "- dist/IFC-Room-Schedule (Standalone executable)"
echo "- deployment/ (Complete package)"
echo ""
echo "To run the application:"
echo "1. Navigate to deployment folder"
echo "2. Run ./IFC-Room-Schedule"
echo ""

# Make executable runnable
chmod +x dist/IFC-Room-Schedule 2>/dev/null || true
chmod +x deployment/IFC-Room-Schedule 2>/dev/null || true

echo "Deployment ready!"