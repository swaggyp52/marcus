# Build script for Marcus Windows EXE (main app)
# Steps:
# 1) Activate venv
# 2) Install requirements
# 3) Compileall
# 4) Run import smoke tests (with local temp mount)
# 5) Start backend briefly and check /health
# 6) Build EXE with PyInstaller
# 7) Run EXE smoke test (check /health)

Param(
    [string]$VenvPath = "C:\Users\conno\marcus\venv",
    [string]$BasePath = "C:\Users\conno\marcus",
    [int]$HttpPort = 8000
)

function Write-Header($msg) {
    $line = ''.PadLeft(60,'=')
    Write-Host "`n$line" -ForegroundColor Cyan
    Write-Host "  $msg" -ForegroundColor Cyan
    Write-Host $line -ForegroundColor Cyan
}

Set-Location -Path $BasePath

# Activate venv (PowerShell)
$activateScript = Join-Path $VenvPath 'Scripts\Activate.ps1'
if (-Not (Test-Path $activateScript)) {
    Write-Error "Virtualenv activate script not found at $activateScript"
    exit 1
}

Write-Header "Activating virtualenv"
. $activateScript

Write-Header "Installing/Upgrading packaging deps"
python -m pip install --disable-pip-version-check -r requirements.txt
# Ensure PyInstaller and pywebview are explicitly installed (match system compatibility)
python -m pip install --disable-pip-version-check --upgrade pyinstaller pywebview requests

Write-Header "Compile all Python files"
python -m compileall .
if ($LASTEXITCODE -ne 0) { Write-Error "compileall failed"; exit 1 }

# Prepare temp mount for smoke tests
$TempMount = Join-Path $BasePath 'storage\packaging_temp'
New-Item -ItemType Directory -Force $TempMount | Out-Null
$env:MARCUS_DATA_ROOT = $TempMount
$env:MARCUS_DB_PATH = (Join-Path $TempMount 'marcus.db')
$env:MARCUS_VAULT_PATH = (Join-Path $TempMount 'vault')
$env:MARCUS_STORAGE_PATH = (Join-Path $TempMount 'storage')

New-Item -ItemType Directory -Force (Join-Path $TempMount 'vault') | Out-Null
New-Item -ItemType Directory -Force (Join-Path $TempMount 'storage') | Out-Null

Write-Header "Import smoke test: FastAPI app"
python -c "import importlib,sys; m=importlib.import_module('marcus_app.backend.api'); print('IMPORT_OK', m.app.title, m.app.version)"
if ($LASTEXITCODE -ne 0) { Write-Error "Import test failed"; exit 1 }

# Start backend using uvicorn in background
$ApiUrl = "http://127.0.0.1:$HttpPort/health"
Write-Header "Backend boot smoke test"
$uvicornCmd = "& `"$($env:VIRTUAL_ENV)\Scripts\python.exe`" -m uvicorn marcus_app.backend.api:app --host 127.0.0.1 --port $HttpPort --log-level info"
Write-Host "Starting backend: $uvicornCmd"
$backendProc = Start-Process -FilePath $env:VIRTUAL_ENV\Scripts\python.exe -ArgumentList '-m','uvicorn','marcus_app.backend.api:app','--host','127.0.0.1','--port',$HttpPort,'--log-level','info' -PassThru -NoNewWindow

# Wait for /health
$timeout = 30
$healthy = $false
for ($i = 0; $i -lt $timeout; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $ApiUrl -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $healthy = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-Not $healthy) { Write-Error "Backend did not respond on $ApiUrl"; if ($backendProc) { $backendProc | Stop-Process -Force }; exit 1 }
Write-Host "Backend health OK"

# Now build EXE with PyInstaller
Write-Header "Building EXE with PyInstaller"
# Ensure pyinstaller present
python -c "import PyInstaller; print('PyInstaller OK')"

# Prepare add-data for frontend
$frontendSrc = Join-Path $BasePath 'marcus_app\frontend'
$addData = "$frontendSrc;marcus_app/frontend"

# PyInstaller command: onefile, console on (so logs visible), name Marcus
# Include hidden imports for modules PyInstaller may miss
pyinstaller --noconfirm --onefile --add-data `"$addData`" --paths `"$BasePath`" --hidden-import=requests --hidden-import=webview --name Marcus launcher_desktop.py
if ($LASTEXITCODE -ne 0) { Write-Error "PyInstaller build failed"; if ($backendProc) { $backendProc | Stop-Process -Force }; exit 1 }

Write-Host "PyInstaller build completed. EXE at: dist\Marcus.exe"

# Stop backend
if ($backendProc) {
    Write-Host "Stopping backend (PID $($backendProc.Id))"
    $backendProc | Stop-Process -Force
}

# EXE smoke test: start EXE and check /health
$exePath = Join-Path $BasePath 'dist\Marcus.exe'
if (-Not (Test-Path $exePath)) { Write-Error "EXE not found: $exePath"; exit 1 }

Write-Header "Running EXE smoke test (background)"
$exeProc = Start-Process -FilePath $exePath -PassThru -NoNewWindow

# Wait for /health again
$timeout = 30
$healthy = $false
for ($i = 0; $i -lt $timeout; $i++) {
    try {
        $r = Invoke-WebRequest -UseBasicParsing -Uri $ApiUrl -TimeoutSec 2 -ErrorAction Stop
        if ($r.StatusCode -eq 200) { $healthy = $true; break }
    } catch {}
    Start-Sleep -Seconds 1
}

if (-Not $healthy) {
    Write-Error "EXE did not bring up backend health endpoint within timeout"
    if ($exeProc) { $exeProc | Stop-Process -Force }
    exit 1
}

Write-Host "EXE boot smoke test: /health OK"

# Leave EXE running and provide instructions
Write-Header "Build Complete"
Write-Host "EXE Path: $exePath"
Write-Host "To pin to taskbar: right-click the exe and 'Pin to taskbar' or create a shortcut and pin that."
Write-Host "Daily workflow: 1) Mount VeraCrypt to M:\Marcus, 2) Run $exePath"

Write-Host "Stopping EXE process started for smoke test"
if ($exeProc) { $exeProc | Stop-Process -Force }

Write-Host "Done."
