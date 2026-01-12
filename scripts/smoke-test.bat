@echo off
REM Smoke test script for Marcus v0.5.2
REM Tests the built application to ensure it works

echo ========================================
echo Marcus v0.5.2 - Smoke Test
echo ========================================
echo.

REM Check if the executable exists
if not exist "dist\Marcus\Marcus.exe" (
    echo ERROR: Marcus.exe not found in dist\Marcus\
    echo Please run build.bat first
    exit /b 1
)

echo [1/4] Testing executable exists...
echo ✓ Marcus.exe found

echo [2/4] Checking file size...
for %%A in ("dist\Marcus\Marcus.exe") do (
    set size=%%~zA
)
if %size% LSS 1000000 (
    echo WARNING: Executable seems too small (less than 1MB^)
)
echo ✓ Executable size: %size% bytes

echo [3/4] Checking required files...
set MISSING_FILES=0

if not exist "dist\Marcus\_internal\" (
    echo ✗ _internal directory missing
    set MISSING_FILES=1
) else (
    echo ✓ _internal directory found
)

if %MISSING_FILES% EQU 1 (
    echo.
    echo ERROR: Some required files are missing
    exit /b 1
)

echo [4/4] Starting application for manual verification...
echo.
echo ========================================
echo The application will now start.
echo Please verify:
echo   1. Window opens successfully
echo   2. Neon UI is displayed
echo   3. Globe animation is working
echo   4. API status shows "Online"
echo   5. You can add/view/delete items
echo.
echo Close the application window when done.
echo ========================================
echo.

start "" "dist\Marcus\Marcus.exe"

echo.
echo Application started. Check the window...
echo.
echo If the application works correctly, the smoke test is PASSED.
echo If there are any issues, the smoke test is FAILED.
echo.

pause
