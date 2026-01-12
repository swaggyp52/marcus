@echo off
echo ====================================================================
echo MARCUS - Academic Operating Environment
echo ====================================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
echo.

REM Install dependencies
echo Checking dependencies...
pip install -r requirements.txt --quiet
echo.

REM Run the application
echo Starting Marcus...
echo.
python main.py
