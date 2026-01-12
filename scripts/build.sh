#!/bin/bash
# Build script for Marcus v0.5.2 (Unix/Linux/Mac)
# Automates the PyInstaller build process

echo "========================================"
echo "Marcus v0.5.2 - Build Script"
echo "========================================"
echo

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed or not in PATH"
    exit 1
fi

echo "[1/5] Checking virtual environment..."
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
fi

echo "[2/5] Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "[3/5] Installing dependencies..."
python -m pip install --upgrade pip
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo "[4/5] Cleaning previous build..."
rm -rf build dist

echo "[5/5] Building with PyInstaller..."
pyinstaller marcus.spec
if [ $? -ne 0 ]; then
    echo "ERROR: PyInstaller build failed"
    exit 1
fi

echo
echo "========================================"
echo "Build completed successfully!"
echo
echo "Executable location: dist/Marcus/Marcus"
echo "========================================"
echo
