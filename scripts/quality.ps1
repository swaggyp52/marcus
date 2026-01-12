#
# Quality Gate Script
#
param([string]$RepoRoot = (git rev-parse --show-toplevel 2>$null))

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

if (-not $RepoRoot) { Write-Error "Not in a git repo"; exit 1 }

$appRoot = Join-Path $RepoRoot "marcus_v052"

Write-Host "====== MARCUS v052 QUALITY GATE ======" -ForegroundColor Cyan
Write-Host ""

$passCount = 0
$failCount = 0

# Report-Check helper
function Report-Check {
    param([string]$Name, [bool]$Passed, [string]$Msg = "")
    if ($Passed) {
        Write-Host "  [OK] $Name" -ForegroundColor Green
        $script:passCount++
    } else {
        Write-Host "  [FAIL] $Name" -ForegroundColor Red
        if ($Msg) { Write-Host "        $Msg" -ForegroundColor Yellow }
        $script:failCount++
    }
}

# Phase 1: Environment
Write-Host "Phase 1: Environment" -ForegroundColor Cyan
try {
    $py = & python --version 2>&1
    Report-Check "Python installed" $? $py
} catch {
    Report-Check "Python installed" $false "Not in PATH"
}

Report-Check "Virtual environment" (Test-Path "$appRoot\.venv")

# Phase 2: Syntax
Write-Host ""
Write-Host "Phase 2: Python Syntax" -ForegroundColor Cyan

@("launcher.py", "backend\api.py", "backend\models.py", "backend\ollama_adapter.py") | ForEach-Object {
    $file = Join-Path $appRoot $_
    if (Test-Path $file) {
        & python -m py_compile $file 2>$null
        Report-Check "Syntax: $_" ($LASTEXITCODE -eq 0)
    }
}

# Phase 3: Dependencies
Write-Host ""
Write-Host "Phase 3: Dependencies" -ForegroundColor Cyan
$reqFile = Join-Path $appRoot "requirements.txt"
Report-Check "requirements.txt" (Test-Path $reqFile)

if (Test-Path $reqFile) {
    $content = Get-Content $reqFile -Raw
    @("fastapi", "uvicorn", "sqlmodel", "pyinstaller") | ForEach-Object {
        Report-Check "  Package: $_" ($content -match $_)
    }
}

# Phase 4: Build Artifacts
Write-Host ""
Write-Host "Phase 4: Build Artifacts" -ForegroundColor Cyan
Report-Check "PyInstaller spec" (Test-Path "$appRoot\Marcus_v052.spec")
Report-Check "EXE exists" (Test-Path "$appRoot\dist\Marcus_v052.exe")

# Summary
Write-Host ""
Write-Host "====== SUMMARY ======" -ForegroundColor Cyan
Write-Host "  Passed: $passCount" -ForegroundColor Green
Write-Host "  Failed: $failCount" -ForegroundColor Red

if ($failCount -eq 0) {
    Write-Host ""
    Write-Host "  [OK] READY TO BUILD" -ForegroundColor Green
    exit 0
} else {
    Write-Host ""
    Write-Host "  [FAIL] FIX ISSUES FIRST" -ForegroundColor Red
    exit 1
}