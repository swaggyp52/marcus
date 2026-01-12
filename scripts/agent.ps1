<#
.SYNOPSIS
    Main agent runner for Marcus development automation.
    
.DESCRIPTION
    Orchestrates autonomous agent workflows (BuildDoctor, BugHunter, Refactorer, TestWriter, DocIndexer, ReleaseSheriff).
    Each agent produces a report and optional code changes on a new branch.
    
.PARAMETER Agent
    Which agent to run: builddoctor, bughunter, refactorer, testwriter, docindexer, releasesheriff
    
.PARAMETER Issue
    (BugHunter only) Issue number or description for context
    
.PARAMETER File
    (Refactorer, TestWriter) File or feature to focus on
    
.EXAMPLE
    .\agent.ps1 builddoctor
    .\agent.ps1 bughunter -Issue "Chat endpoint 404"
    .\agent.ps1 refactorer -File backend/api.py
    .\agent.ps1 testwriter -File backend/models.py
    .\agent.ps1 docindexer
    .\agent.ps1 releasesheriff
#>

param(
    [Parameter(Position=0)]
    [ValidateSet("builddoctor", "bughunter", "refactorer", "testwriter", "docindexer", "releasesheriff", "help")]
    [string]$Agent = "help",
    
    [string]$Issue,
    [string]$File,
    [string]$Mode,
    [string]$Target,
    [string]$Slug,
    [switch]$DryRun,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    $ExtraArgs
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

function Show-Usage {
    Write-Host "Usage:" -ForegroundColor Cyan
    Write-Host "  .\scripts\agent.ps1 <agent> [options]" -ForegroundColor White
    Write-Host ""
    Write-Host "Agents:" -ForegroundColor Cyan
    Write-Host "  builddoctor      Validate build environment" -ForegroundColor Gray
    Write-Host "  docindexer       Sync docs and generate indexes" -ForegroundColor Gray
    Write-Host "  bughunter        Reproduce and diagnose bugs" -ForegroundColor Gray
    Write-Host "  refactorer       Safe refactoring with validation" -ForegroundColor Gray
    Write-Host "  testwriter       Improve test coverage" -ForegroundColor Gray
    Write-Host "  releasesheriff   Validate release readiness" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Other:" -ForegroundColor Cyan
    Write-Host "  help             Show this message" -ForegroundColor Gray
    Write-Host ""
}

if ($Agent -eq "help") {
    Show-Usage
    exit 0
}

# Detect repo root
$repoRoot = git rev-parse --show-toplevel 2>$null
if (-not $repoRoot) {
    # Fallback: use script directory parent
    $repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
}

if (-not $repoRoot) {
    Write-Error "Could not determine repository root"
    exit 1
}

$agentDir = Join-Path $repoRoot ".agent"
$scriptsDir = Join-Path $agentDir "scripts"
$reportsDir = Join-Path $repoRoot "docs\REPORTS"
$timestamp = Get-Date -Format "yyyy-MM-dd-HHmmss"
$reportFile = Join-Path $reportsDir "$timestamp-$Agent.md"

# Ensure directories exist
foreach ($dir in @($agentDir, "$agentDir\index", $reportsDir)) {
    if (-not (Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
    }
}

Write-Host "═════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "Agent Runner: $Agent" -ForegroundColor Cyan
Write-Host "Report: $reportFile" -ForegroundColor Gray
Write-Host "═════════════════════════════════════════" -ForegroundColor Cyan
Write-Host ""

# Route to appropriate agent
try {
    $agentScript = switch ($Agent) {
        "builddoctor" { Join-Path $scriptsDir "builddoctor.ps1" }
        "bughunter" { Join-Path $scriptsDir "bughunter.ps1" }
        "refactorer" { Join-Path $scriptsDir "refactorer.ps1" }
        "testwriter" { Join-Path $scriptsDir "testwriter.ps1" }
        "docindexer" { Join-Path $scriptsDir "docindexer.ps1" }
        "releasesheriff" { Join-Path $scriptsDir "releasesheriff.ps1" }
    }
    
    if (-not (Test-Path $agentScript)) {
        throw "Agent script not found: $agentScript"
    }
    
    Write-Host "[OK] Invoking $Agent..." -ForegroundColor Green
    
    # Invoke agent with appropriate parameters
    switch ($Agent) {
        "bughunter" { 
            $bugArgs = @("-Issue", $Issue, "-ReportFile", $reportFile, "-RepoRoot", $repoRoot)
            if ($Mode) { $bugArgs += @("-Mode", $Mode) }
            if ($Target) { $bugArgs += @("-Target", $Target) }
            if ($Slug) { $bugArgs += @("-Slug", $Slug) }
            if ($DryRun) { $bugArgs += "-DryRun" }
            & powershell -ExecutionPolicy Bypass -File $agentScript @bugArgs
        }
        "refactorer" { & powershell -ExecutionPolicy Bypass -File $agentScript -File $File -ReportFile $reportFile -RepoRoot $repoRoot }
        "testwriter" { & powershell -ExecutionPolicy Bypass -File $agentScript -File $File -ReportFile $reportFile -RepoRoot $repoRoot }
        default { & powershell -ExecutionPolicy Bypass -File $agentScript -ReportFile $reportFile -RepoRoot $repoRoot }
    }
    
    if ($LASTEXITCODE -ne 0) {
        throw "Agent failed with exit code $LASTEXITCODE"
    }
} catch {
    Write-Host ""
    Write-Host "[FAIL] Agent execution failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "═════════════════════════════════════════" -ForegroundColor Cyan
if (Test-Path $reportFile) {
    Write-Host "[OK] Report saved: $reportFile" -ForegroundColor Green
} else {
    Write-Host "[WARN] Report file not found: $reportFile" -ForegroundColor Yellow
}
Write-Host "═════════════════════════════════════════" -ForegroundColor Cyan

exit 0
