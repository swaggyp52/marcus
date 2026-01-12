Param(
    [string]$ExePath = "dist\Marcus_v052.exe",
    [int]$Port = 8000
)

$base = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location -Path $base\..\

if(-not (Test-Path $ExePath)){ Write-Error "EXE not found at $ExePath"; exit 1 }

# set port env for EXE and disable browser opening
$env:MARCUS_PORT = $Port.ToString()
$env:MARCUS_HEADLESS = "1"

Write-Host "Starting EXE: $ExePath (port $Port)"
$proc = Start-Process -FilePath $ExePath -PassThru -NoNewWindow

$ApiBase = "http://127.0.0.1:$Port"
$ApiUrl = "$ApiBase/health"
$timeout = 45; $ok=$false
for($i=0;$i -lt $timeout;$i++){
    try{ $r=Invoke-WebRequest -UseBasicParsing -Uri $ApiUrl -TimeoutSec 2 -ErrorAction Stop; if($r.StatusCode -eq 200){ $ok=$true; break } } catch{}
    Start-Sleep -Seconds 1
}
if(-not $ok){ Write-Error 'EXE health check failed'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
Write-Host "[PASS] health ok"

# GET / should return HTML referencing app.js
try{
    $root = Invoke-WebRequest -UseBasicParsing -Uri "$ApiBase/" -TimeoutSec 5
    if($root.Content -notmatch '/static/app.js'){ Write-Error 'Root HTML does not reference /static/app.js'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    Write-Host "[PASS] root HTML references /static/app.js"
} catch { Write-Error "Failed to GET root: $_"; if($proc){ $proc | Stop-Process -Force }; exit 1 }

# GET /api/graph
try{
    $g = Invoke-WebRequest -UseBasicParsing -Uri "$ApiBase/api/graph" -TimeoutSec 5
    $j = $g.Content | ConvertFrom-Json
    if(-not $j.nodes){ Write-Error 'Graph empty or invalid'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    Write-Host "[PASS] graph ok (nodes: $($j.nodes.Count))"
} catch { Write-Error "Graph check failed: $_"; if($proc){ $proc | Stop-Process -Force }; exit 1 }

# upload sample_upload.txt
try{
    $sample = Resolve-Path ..\sample_upload.txt
    if(-not $sample){ Write-Error 'sample_upload.txt not found'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    if(Get-Command curl -ErrorAction SilentlyContinue){
        $out = curl -s -F "file=@$($sample.Path)" "$ApiBase/api/upload" | ConvertFrom-Json
    } else {
        # PowerShell Invoke-RestMethod multipart (works in PowerShell 7+)
        $form = @{ file = Get-Item $sample }
        $out = Invoke-RestMethod -Uri "$ApiBase/api/upload" -Method Post -Form $form
    }
    if(-not $out.excerpt){ Write-Error 'Upload failed or no excerpt returned'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    Write-Host "[PASS] upload ok (excerpt length: $($out.excerpt.Length))"
} catch { Write-Error "Upload failed: $_"; if($proc){ $proc | Stop-Process -Force }; exit 1 }

# chat create class
try{
    $chatReq = @{ message = 'create class TEST101' } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$ApiBase/api/chat" -Method Post -Body $chatReq -ContentType 'application/json'
    if(-not $res.results){ Write-Error 'Chat did not return results'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    $createdClass = $res.results | Where-Object { $_.created -eq 'class' }
    if(-not $createdClass){ Write-Error 'Chat did not create a class'; if($proc){ $proc | Stop-Process -Force }; exit 1 }
    Write-Host "[PASS] chat created class id=$($createdClass.id) name=$($createdClass.name)"
} catch { Write-Error "Chat test failed: $_"; if($proc){ $proc | Stop-Process -Force }; exit 1 }

# cleanup
if($proc){ $proc | Stop-Process -Force }
Write-Host '[PASS] smoke test completed successfully' -ForegroundColor Green
exit 0
