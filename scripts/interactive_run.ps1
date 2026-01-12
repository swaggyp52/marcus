# Interactive run helper for Marcus.exe
# Runs the EXE (simulates mount if M:\Marcus missing), polls /health up to 120s, fetches root HTML, then stops the process.

$dist = "C:\Users\conno\marcus\dist"
Set-Location $dist
Write-Output "-- Interactive EXE run: dist=$dist (120s timeout) --"
$mountExists = Test-Path 'M:\Marcus'
if (-not $mountExists) {
  Write-Output "M:\Marcus not present; simulating mount using packaging_temp storage"
  $env:MARCUS_STORAGE_PATH = 'C:\Users\conno\marcus\storage\packaging_temp\storage'
} else { Write-Output "M:\Marcus present." }

$proc = Start-Process -FilePath ".\Marcus.exe" -PassThru
Write-Output "Started Marcus.exe PID=$($proc.Id)"
$procId = $proc.Id
$start = Get-Date
$healthOk = $false
while (((Get-Date) - $start).TotalSeconds -lt 120) {
  try {
    $r = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/health' -UseBasicParsing -TimeoutSec 2
    if ($r.StatusCode -eq 200) { Write-Output "HEALTH_OK"; $healthOk = $true; break }
  } catch { }
  Start-Sleep -Seconds 1
}
if (-not $healthOk) { Write-Output "HEALTH_TIMEOUT" }

try {
  $root = Invoke-WebRequest -Uri 'http://127.0.0.1:8000/' -UseBasicParsing -TimeoutSec 5
  Write-Output "ROOT_STATUS: $($root.StatusCode)"
  $len = $root.Content.Length
  Write-Output "ROOT_CONTENT_LENGTH: $len"
  $snippet = $root.Content.Substring(0,[Math]::Min(800,$len))
  Write-Output "ROOT_SNIPPET_START:`n$snippet"
} catch { Write-Output "ROOT_FETCH_FAILED: $($_.Exception.Message)" }

Start-Sleep -Seconds 2
Stop-Process -Id $procId -Force
Write-Output "Stopped PID $procId"
