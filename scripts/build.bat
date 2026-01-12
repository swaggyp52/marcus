@echo off
REM Build script for Marcus v0.5.2
REM Automates the PyInstaller build process

echo ========================================
echo Marcus v0.5.2 - Build Script
echo ========================================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    exit /b 1
)

echo [1/5] Checking virtual environment...
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        exit /b 1
    )
)

echo [2/5] Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment
    exit /b 1
)

echo [3/5] Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    exit /b 1
)

echo [4/5] Cleaning previous build...
if exist "build\" rmdir /s /q build
if exist "dist\" rmdir /s /q dist

echo [5/5] Building with PyInstaller...
pyinstaller marcus.spec
if errorlevel 1 (
    echo ERROR: PyInstaller build failed
    exit /b 1
)

echo.
echo ========================================
echo Build completed successfully!
echo.
echo Executable location: dist\Marcus\Marcus.exe
echo ========================================
echo.

pause
