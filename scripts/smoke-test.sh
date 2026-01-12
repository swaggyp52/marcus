#!/bin/bash
# Smoke test script for Marcus v0.5.2 (Unix/Linux/Mac)
# Tests the built application to ensure it works

echo "========================================"
echo "Marcus v0.5.2 - Smoke Test"
echo "========================================"
echo

# Check if the executable exists
if [ ! -f "dist/Marcus/Marcus" ]; then
    echo "ERROR: Marcus executable not found in dist/Marcus/"
    echo "Please run build.sh first"
    exit 1
fi

echo "[1/4] Testing executable exists..."
echo "✓ Marcus executable found"

echo "[2/4] Checking file size..."
size=$(stat -f%z "dist/Marcus/Marcus" 2>/dev/null || stat -c%s "dist/Marcus/Marcus" 2>/dev/null)
if [ $size -lt 1000000 ]; then
    echo "WARNING: Executable seems too small (less than 1MB)"
fi
echo "✓ Executable size: $size bytes"

echo "[3/4] Checking required files..."
MISSING_FILES=0

if [ ! -d "dist/Marcus/_internal/" ]; then
    echo "✗ _internal directory missing"
    MISSING_FILES=1
else
    echo "✓ _internal directory found"
fi

if [ $MISSING_FILES -eq 1 ]; then
    echo
    echo "ERROR: Some required files are missing"
    exit 1
fi

echo "[4/4] Application ready for manual verification..."
echo
echo "========================================"
echo "To start the application, run:"
echo "  ./dist/Marcus/Marcus"
echo
echo "Please verify:"
echo "  1. Window opens successfully"
echo "  2. Neon UI is displayed"
echo "  3. Globe animation is working"
echo "  4. API status shows 'Online'"
echo "  5. You can add/view/delete items"
echo "========================================"
echo
