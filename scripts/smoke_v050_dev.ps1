# scripts\smoke_v050_dev.ps1
# Development smoke test: uses local test storage instead of VeraCrypt

$ErrorActionPreference = "Stop"

$base = "http://127.0.0.1:8000"
$exe = "$env:LOCALAPPDATA\Marcus\Marcus.exe"
$testStoragePath = "C:\Users\conno\marcus\storage\packaging_temp"

Write-Host "=== Marcus v0.50 Smoke Test (DEV MODE) ===`n"

# Set env vars to use test storage (development only)
$env:MARCUS_DATA_ROOT = $testStoragePath
$env:MARCUS_STORAGE_PATH = "$testStoragePath\storage"
$env:MARCUS_VAULT_PATH = "$testStoragePath\vault"
$env:MARCUS_DB_PATH = "$testStoragePath\storage\marcus.db"

Write-Host "[SETUP] Using test storage: $testStoragePath`n"

# Kill old processes
Get-Process Marcus -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 1

# Verify exe exists
if (-not (Test-Path $exe)) {
  Write-Host "[FAIL] Marcus.exe not found at $exe" -ForegroundColor Red
  exit 1
}
Write-Host "[OK] Marcus.exe found`n"

# Start process with env vars
Write-Host "[START] Starting Marcus.exe..."
$proc = Start-Process -FilePath $exe -PassThru -NoNewWindow -ErrorAction Stop
Start-Sleep -Seconds 3

# Check if it's still alive
$running = Get-Process -Id $proc.Id -ErrorAction SilentlyContinue
if (-not $running) {
  Write-Host "[FAIL] Process exited immediately" -ForegroundColor Red
  exit 1
}
Write-Host "[OK] Process running (PID=$($proc.Id))`n"

# Wait for health endpoint
Write-Host "[WAIT] Polling /health..."
$healthy = $false
for ($i = 0; $i -lt 20; $i++) {
  try {
    $h = Invoke-RestMethod "$base/health" -TimeoutSec 2 -ErrorAction Stop
    $healthy = $true
    Write-Host "[OK] /health responding`n"
    break
  } catch {
    Start-Sleep -Seconds 1
  }
}

if (-not $healthy) {
  Write-Host "[FAIL] /health did not respond within 20s" -ForegroundColor Red
  exit 1
}

# Test app.js
Write-Host "[TEST] GET /static/app.js..."
try {
  # Static files are behind auth, so we expect a redirect or auth error
  # For smoke test, just verify the endpoint exists and responds (even if redirecting)
  try {
    $r = Invoke-WebRequest "http://127.0.0.1:8000/static/app.js" -UseBasicParsing -TimeoutSec 3 -MaximumRedirection 0 -ErrorAction Stop
    Write-Host "[OK] /static/app.js endpoint exists`n"
  } catch {
    # Expected: redirect or 401/403 for auth
    $statusCode = $_.Exception.Response.StatusCode.Value__
    if ($statusCode -in @(301, 302, 303, 307, 308, 401, 403)) {
      Write-Host "[OK] /static/app.js endpoint exists (auth expected: $statusCode)`n"
    } else {
      throw $_
    }
  }
} catch {
  Write-Host "[FAIL] /static/app.js not reachable: $_" -ForegroundColor Red
  exit 1
}

# Test root HTML
Write-Host "[TEST] GET / (root HTML)..."
try {
  $root = (Invoke-WebRequest "$base/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop -MaximumRedirection 0).Content
  if ($root -match "/static/app\.js") {
    Write-Host "[OK] Root HTML references /static/app.js`n"
  } else {
    Write-Host "[FAIL] Root HTML missing /static/app.js reference" -ForegroundColor Red
    exit 1
  }
} catch {
  if ($_.Exception.Message -match "307|308") {
    Write-Host "[OK] Root page auth check working (redirect expected)`n"
  } else {
    Write-Host "[FAIL] Root page not reachable: $_" -ForegroundColor Red
    exit 1
  }
}

# Test intake endpoint
Write-Host "[TEST] POST /api/intake..."
$intakeOk = $false
try {
  $x = Invoke-WebRequest "$base/api/intake" -Method Options -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
  if ($x.StatusCode -ge 200 -and $x.StatusCode -lt 500) { $intakeOk = $true }
} catch {
  $msg = $_.Exception.Message
  if ($msg -match "401|403") { $intakeOk = $true }
}

if ($intakeOk) {
  Write-Host "[OK] Intake route exists`n"
} else {
  Write-Host "[FAIL] Intake route appears missing (404)" -ForegroundColor Red
  exit 1
}

Write-Host "=== PASS: Marcus v0.50 looks good ===" -ForegroundColor Green
Write-Host "`nIf you see a window on screen right now, the UI is rendering." -ForegroundColor Cyan
Write-Host "If you do NOT see a window, check for pywebview/WebView2 issues." -ForegroundColor Cyan
