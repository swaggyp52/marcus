# smoke_v051.ps1 - Smoke test for v0.51 chat-first redesign

param(
    [int]$TimeoutSeconds = 30,
    [string]$MarcusExePath = "c:\Users\conno\marcus\dist\Marcus.exe"
)

$ErrorActionPreference = "Stop"

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host "Marcus v0.51 Smoke Test - Chat & File Upload" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# Check EXE exists
if (-not (Test-Path $MarcusExePath)) {
    Write-Host "ERROR: Marcus.exe not found at $MarcusExePath" -ForegroundColor Red
    Write-Host "Run build_windows_exe.ps1 first." -ForegroundColor Yellow
    exit 1
}

# Start Marcus.exe
Write-Host "`n[1/5] Starting Marcus.exe..." -ForegroundColor Cyan
$process = Start-Process $MarcusExePath -PassThru -WindowStyle Normal
$procId = $process.Id
Write-Host "      Process started (PID: $procId)"

# Wait for startup
Write-Host "`n[2/5] Waiting for backend to be ready..." -ForegroundColor Cyan
$startTime = Get-Date
$ready = $false

while ((Get-Date) - $startTime -lt (New-TimeSpan -Seconds $TimeoutSeconds)) {
    try {
        $resp = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction SilentlyContinue
        if ($resp.status -eq "ok") {
            Write-Host "      ✓ Backend is ready"
            $ready = $true
            break
        }
    } catch {
        Start-Sleep -Milliseconds 500
    }
}

if (-not $ready) {
    Write-Host "      ERROR: Backend did not respond within ${TimeoutSeconds}s" -ForegroundColor Red
    $process | Stop-Process -Force
    exit 2
}

try {
    # Test 1: Health check
    Write-Host "`n[3/5] Testing /health endpoint..." -ForegroundColor Cyan
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health"
    Write-Host "      ✓ Health: $($health.status)"
    
    # Test 2: Chat endpoint - simple message
    Write-Host "`n[4/5] Testing /api/chat endpoint..." -ForegroundColor Cyan
    $chatPayload = @{ message = "what's next" } | ConvertTo-Json
    $chatResp = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $chatPayload
    
    Write-Host "      ✓ Chat response received"
    Write-Host "      Reply: $($chatResp.reply.Substring(0, [Math]::Min(50, $chatResp.reply.Length)))..."
    Write-Host "      Actions: $($chatResp.actions.Count) action(s)"
    Write-Host "      Created: $($chatResp.created.Count) item(s)"
    
    # Test 3: File upload
    Write-Host "`n[5/5] Testing /api/chat/upload endpoint..." -ForegroundColor Cyan
    
    # Create test file
    $testFile = "$env:TEMP\test_syllabus.txt"
    $testContent = "CS 350 - Operating Systems`nInstructor: Prof. Smith`nOffice Hours: MW 2-4pm, ECS 240`n`nCourse Objectives:`nUnderstand kernel concepts`nStudy synchronization`nLearn about scheduling`n`nAssignments:`n1. Process Creation - Due: 2024-02-15`n2. Memory Management - Due: 2024-03-01`n3. Deadlock Detection - Due: 2024-03-15`n4. File System - Due: 2024-04-01"
    Set-Content -Path $testFile -Value $testContent -Force
    
    $fileBytes = [System.IO.File]::ReadAllBytes($testFile)
    $fileName = Split-Path $testFile -Leaf
    
    # Create multipart form
    $boundary = [System.Guid]::NewGuid().ToString()
    $bodyLines = @(
        "--$boundary"
        "Content-Disposition: form-data; name=`"file`"; filename=`"$fileName`""
        "Content-Type: text/plain"
        ""
        $testContent
        "--$boundary--"
    )
    $body = $bodyLines -join "`r`n"
    
    $uploadResp = Invoke-RestMethod -Uri "http://localhost:8000/api/chat/upload" `
        -Method Post `
        -ContentType "multipart/form-data; boundary=$boundary" `
        -Body $body
    
    Write-Host "      ✓ File uploaded successfully"
    Write-Host "      Artifact ID: $($uploadResp.artifactId)"
    Write-Host "      Filename: $($uploadResp.metadata.filename)"
    Write-Host "      Size: $($uploadResp.metadata.size) bytes"
    
    # Test 4: Chat with attachment
    Write-Host "`n      Testing chat with file attachment..." -ForegroundColor Cyan
    $chatPayload = @{
        message = "set this up"
        attachmentId = $uploadResp.artifactId
    } | ConvertTo-Json
    
    $chatResp2 = Invoke-RestMethod -Uri "http://localhost:8000/api/chat" `
        -Method Post `
        -ContentType "application/json" `
        -Body $chatPayload
    
    Write-Host "      ✓ Chat processed file"
    Write-Host "      Reply: $($chatResp2.reply.Substring(0, [Math]::Min(60, $chatResp2.reply.Length)))..."
    Write-Host "      Created: $($chatResp2.created.Count) item(s)"
    
    # Summary
    Write-Host "`n================================================================" -ForegroundColor Green
    Write-Host "✓ ALL SMOKE TESTS PASSED" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Open http://localhost:8000 in a web browser"
    Write-Host "2. Test chat UI: type messages and upload files"
    Write-Host "3. Check that action cards appear and items are created"
    Write-Host ""
    
    exit 0

} catch {
    Write-Host "`nERROR during testing:" -ForegroundColor Red
    Write-Host $_.Exception.Message
    exit 3

} finally {
    Write-Host "`nCleaning up..." -ForegroundColor Yellow
    if (Get-Process -Id $procId -ErrorAction SilentlyContinue) {
        Write-Host "Stopping Marcus.exe (PID: $procId)..."
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
    }
}
