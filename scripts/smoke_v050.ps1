$ErrorActionPreference = "Stop"

$base = "http://127.0.0.1:8000"
$exeDefault = Join-Path $env:LOCALAPPDATA "Marcus\Marcus.exe"
$exe = $exeDefault
$logDir = Join-Path $env:LOCALAPPDATA "Marcus\logs"

function Fail($msg) {
  Write-Host "[FAIL] $msg" -ForegroundColor Red
  
  # Try to show log if available
  if (Test-Path $logDir) {
    Write-Host "`n[LOG TAIL]" -ForegroundColor Yellow
    Get-ChildItem $logDir -Filter "*.txt" -ErrorAction SilentlyContinue | ForEach-Object {
      if ((Get-Item $_.FullName).Length -gt 0) {
        Write-Host "--- $($_.Name) ---"
        Get-Content $_.FullName -Tail 30 -ErrorAction SilentlyContinue
      }
    }
  }
  exit 1
}

function Ok($msg) {
  Write-Host "[OK] $msg" -ForegroundColor Green
}

Write-Host "=== Marcus v0.50 Smoke Test ===`n"

# 0) Encrypted mount check
if (-not (Test-Path "M:\Marcus\")) {
  Fail "Encrypted drive not mounted. Expected M:\Marcus\ to exist. Mount VeraCrypt volume first."
}
Ok "Encrypted drive mounted (M:\Marcus\ found)"

# 1) Start Marcus.exe or detect running
$running = Get-Process -Name "Marcus" -ErrorAction SilentlyContinue
if ($running) {
  Ok "Marcus process already running (pid=$($running.Id))"
  $proc = $running[0]
} else {
  if (-not (Test-Path $exe)) {
    Fail "Marcus.exe not found at $exe. Run build script first."
  }

  # Create log directory
  New-Item -ItemType Directory -Force -Path $logDir | Out-Null

  Ok "Starting Marcus.exe..."
  $stdout = Join-Path $logDir "stdout.txt"
  $stderr = Join-Path $logDir "stderr.txt"
  
  $proc = Start-Process -FilePath $exe -PassThru -RedirectStandardOutput $stdout -RedirectStandardError $stderr
  
  Start-Sleep -Seconds 2
  
  # Check if it exited immediately
  if ($proc.HasExited) {
    Write-Host "`n[EARLY EXIT] Marcus exited. Stderr:" -ForegroundColor Red
    Get-Content $stderr -Tail 50 -ErrorAction SilentlyContinue | Write-Host
    Fail "Marcus exited immediately (see logs above)"
  }
}

# Wait for /health to come up (max ~15s)
$ready = $false
for ($i=0; $i -lt 15; $i++) {
  try {
    $h = Invoke-RestMethod "$base/health" -TimeoutSec 2 -ErrorAction Stop
    $ready = $true
    break
  } catch {
    Start-Sleep -Seconds 1
  }
}
if (-not $ready) {
  Fail "/health did not become ready at $base/health within 15s"
}
Ok "/health reachable"

# 2) app.js reachable (packaging sanity)
try {
  $r = Invoke-WebRequest "$base/app.js" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop
} catch {
  Fail "/app.js not reachable: $($_.Exception.Message)"
}

if ($r.StatusCode -ne 200) { Fail "/app.js returned status $($r.StatusCode)" }
if ($r.RawContentLength -lt 2000) { Fail "/app.js too small ($($r.RawContentLength) bytes). Likely not bundled/served correctly." }
Ok "/app.js served (bytes=$($r.RawContentLength))"

# 3) Root HTML references app.js
try {
  $root = (Invoke-WebRequest "$base/" -UseBasicParsing -TimeoutSec 3 -ErrorAction Stop).Content
} catch {
  Fail "Root page not reachable: $($_.Exception.Message)"
}

if ($root -notmatch "/app\.js") { Fail "Root HTML missing /app.js reference. UI will not load." }
Ok "Root HTML references /app.js"

# 4) Optional /api/health
try {
  $api = Invoke-RestMethod "$base/api/health" -TimeoutSec 2 -ErrorAction Stop
  Ok "/api/health reachable"
} catch {
  Write-Host "[WARN] /api/health missing or blocked (OK if your app uses /health only)" -ForegroundColor Yellow
}

# 5) Intake route exists
$intakeOk = $false
try {
  $x = Invoke-WebRequest "$base/api/intake" -Method Options -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
  if ($x.StatusCode -ge 200 -and $x.StatusCode -lt 500) { $intakeOk = $true }
} catch {
  $msg = $_.Exception.Message
  if ($msg -match "401" -or $msg -match "403") { $intakeOk = $true }
  elseif ($msg -match "404") { $intakeOk = $false }
  else {
    Write-Warning "Intake probe unclear: $msg"
  }
}

if (-not $intakeOk) {
  Fail "Intake route appears missing (404). Syllabi upload won't work."
}
Ok "Intake route exists"

Write-Host "`n=== PASS: Marcus v0.50 looks deployable ===" -ForegroundColor Green
exit 0
