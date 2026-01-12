Param(
    [string]$BasePath = "C:\Users\conno\marcus\marcus_v052",
    [int]$HttpPort = 8000
)

Set-Location -Path $BasePath

Write-Host "Activating venv if present (otherwise use system python)"
if(Test-Path .\.venv\Scripts\Activate.ps1){ . .\.venv\Scripts\Activate.ps1 }

Write-Host "Installing deps"
python -m pip install --disable-pip-version-check -r requirements.txt

Write-Host "Compile and import check"
$env:PYTHONPATH = $BasePath
python -m compileall .
python -c "import sys; sys.path.insert(0, r'$BasePath'); import importlib; importlib.import_module('backend.api'); print('IMPORT_OK')"

Write-Host "Start backend smoke test"
$PY = 'python'
if(Test-Path .\.venv\Scripts\python.exe){ $PY = (Resolve-Path .\.venv\Scripts\python.exe).Path }
$backendProc = Start-Process -FilePath $PY -ArgumentList '-m','uvicorn','backend.api:app','--host','127.0.0.1','--port',$HttpPort -PassThru -NoNewWindow -WorkingDirectory $BasePath

$ApiUrl = "http://127.0.0.1:$HttpPort/health"
$timeout = 30; $healthy=$false
for($i=0;$i -lt $timeout;$i++){
    try{ $r = Invoke-WebRequest -UseBasicParsing -Uri $ApiUrl -TimeoutSec 2 -ErrorAction Stop; if($r.StatusCode -eq 200){ $healthy=$true; break } } catch{}
    Start-Sleep -Seconds 1
}
if(-not $healthy){ Write-Error "Backend did not start"; if($backendProc){ $backendProc | Stop-Process -Force }; exit 1 }

Write-Host "Building EXE with PyInstaller (spec file)"
pyinstaller --noconfirm Marcus_v052.spec
if($LASTEXITCODE -ne 0){ Write-Error "Build failed"; exit 1 }
Write-Host "EXE built at dist\Marcus_v052.exe"

if($backendProc){ $backendProc | Stop-Process -Force }
