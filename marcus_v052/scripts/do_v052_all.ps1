Param(
    [int]$Port = 8000
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$root = Split-Path -Parent $scriptDir
Set-Location -Path $root
Write-Host "Working in $root"

function FailExit($msg){ Write-Host "[FAIL] $msg" -ForegroundColor Red; exit 1 }

Write-Host "[STEP] Create venv .venv if missing"
if(-not (Test-Path .\.venv)){ python -m venv .venv; if($LASTEXITCODE -ne 0){ FailExit 'venv creation failed' } }

Write-Host "[STEP] Activate venv"
. .\.venv\Scripts\Activate.ps1

Write-Host "[STEP] Install requirements"
python -m pip install --disable-pip-version-check -r requirements.txt
if($LASTEXITCODE -ne 0){ FailExit 'pip install failed' }
Write-Host "[PASS] dependencies installed"

Write-Host "[STEP] Dev sanity: start backend and check /health and /api/graph"
$env:PYTHONPATH = $root
$PY = (Get-Command python).Source
$backend = Start-Process -FilePath $PY -ArgumentList '-m','uvicorn','backend.api:app','--host','127.0.0.1','--port',$Port -PassThru -NoNewWindow -WorkingDirectory $root
$baseUrl = "http://127.0.0.1:$Port"
$ok=$false
for($i=0;$i -lt 40;$i++){
    try{ $r = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/health" -TimeoutSec 2 -ErrorAction Stop; if($r.StatusCode -eq 200){ $ok=$true; break } } catch{}
    Start-Sleep -Seconds 1
}
if(-not $ok){ if($backend){ $backend | Stop-Process -Force }; FailExit 'dev backend failed to start' }
Write-Host "[PASS] dev backend health OK"

try{
    $g = Invoke-WebRequest -UseBasicParsing -Uri "$baseUrl/api/graph" -TimeoutSec 5
    $jg = $g.Content | ConvertFrom-Json
    Write-Host "[PASS] dev graph returned nodes: $($jg.nodes.Count)"
} catch { if($backend){ $backend | Stop-Process -Force }; FailExit "dev graph check failed: $_" }

Write-Host "Stopping dev backend"
if($backend){ $backend | Stop-Process -Force }

Write-Host "[STEP] Build EXE (PyInstaller)"
& ".\scripts\build_windows_exe.ps1" -BasePath $PWD -HttpPort $Port
if($LASTEXITCODE -ne 0){ FailExit 'build_windows_exe.ps1 failed' }
Write-Host "[PASS] build completed"

Write-Host "[STEP] Run smoke test against EXE"
& ".\scripts\smoke_test.ps1" -ExePath (Join-Path $PWD 'dist\Marcus_v052.exe') -Port $Port
if($LASTEXITCODE -ne 0){ FailExit 'smoke_test failed' }
Write-Host "[PASS] smoke test passed"

Write-Host "[STEP] Package ZIP"
$zipPath = Join-Path $PWD 'Marcus_v052.zip'
if(Test-Path $zipPath){ Remove-Item $zipPath -Force }
$tmp = Join-Path $PWD 'dist_package'
if(Test-Path $tmp){ Remove-Item $tmp -Recurse -Force }
New-Item -ItemType Directory -Path $tmp | Out-Null
Copy-Item -Path (Join-Path $PWD 'dist\Marcus_v052.exe') -Destination $tmp
Copy-Item -Path (Join-Path $PWD 'README.md') -Destination $tmp
Copy-Item -Path (Join-Path $PWD 'sample_upload.txt') -Destination $tmp
Compress-Archive -Path $tmp\* -DestinationPath $zipPath -Force
Write-Host "[PASS] ZIP created: $zipPath (size: $((Get-Item $zipPath).length/1MB) MB)"

Write-Host "ALL STEPS PASSED"
exit 0
