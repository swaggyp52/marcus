<#
.SYNOPSIS
    BuildDoctor Agent: Validates build environment and fixes common issues
#>

param(
    [string]$ReportFile,
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

$report = @"
# BuildDoctor Report
$(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Environment Validation

### Python Environment
"@

# Check Python
try {
    $pythonVersion = & python --version 2>&1
    $report += "`n[OK] Python: $pythonVersion"
} catch {
    $report += "`n[FAIL] Python: Not found in PATH"
}

# Check pip
try {
    $pipVersion = & pip --version 2>&1
    $report += "`n[OK] pip: $pipVersion"
} catch {
    $report += "`n[FAIL] pip: Not found"
}

# Check venv
$appRoot = Join-Path $RepoRoot "marcus_v052"
$venvPath = Join-Path $appRoot ".venv"
if (Test-Path $venvPath) {
    $report += "`n[OK] Virtual environment: exists at $venvPath"
} else {
    $report += "`n[FAIL] Virtual environment: NOT FOUND`n`n   Remedy: Run 'python -m venv $venvPath' then '.venv\Scripts\Activate.ps1'"
}

# Check requirements
$reqFile = Join-Path $appRoot "requirements.txt"
if (Test-Path $reqFile) {
    $report += "`n[OK] requirements.txt: exists"
    $packages = Get-Content $reqFile | Measure-Object -Line
    $report += "`n  Contains: $($packages.Lines) packages"
} else {
    $report += "`n[FAIL] requirements.txt: NOT FOUND"
}

# Check PyInstaller
try {
    $piVersion = & pyinstaller --version 2>&1
    $report += "`n[OK] PyInstaller: $piVersion"
} catch {
    $report += "`n[FAIL] PyInstaller: Not installed`n   Remedy: pip install pyinstaller"
}

# Check spec file
$specFile = Join-Path $appRoot "Marcus_v052.spec"
if (Test-Path $specFile) {
    $report += "`n[OK] Build spec: exists"
} else {
    $report += "`n[FAIL] Build spec: NOT FOUND"
}

$report += "`n`n## Syntax Validation`n`n"

# Validate Python files
$pythonFiles = @(
    (Join-Path $appRoot "launcher.py"),
    (Join-Path $appRoot "backend\api.py"),
    (Join-Path $appRoot "backend\models.py")
)

foreach ($file in $pythonFiles) {
    if (Test-Path $file) {
        try {
            & python -m py_compile $file 2>&1 | Out-Null
            $report += "[OK] $(Split-Path $file -Leaf)`n"
        } catch {
            $report += "[FAIL] $(Split-Path $file -Leaf): Syntax error`n"
        }
    }
}

$report += "`n## Recommendations`n`n"
$report += "- Run full build: .\marcus_v052\scripts\do_v052_all.ps1`n"
$report += "- Run quality gate: .\scripts\quality.ps1`n"
$report += "- For more details, see docs/SETUP_WINDOWS.md`n"

$report += "`n## Status`n`n"
if ($report -match "\[FAIL\]") {
    $report += "[ALERT] ISSUES FOUND - Fix above before building`n"
} else {
    $report += "[OK] READY TO BUILD - Environment is healthy`n"
}

# Save report
$report | Out-File -FilePath $ReportFile -Encoding UTF8

Write-Host $report
Write-Host ""
Write-Host "Report saved: $ReportFile" -ForegroundColor Green
