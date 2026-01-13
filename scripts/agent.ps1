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
    [ValidateSet("builddoctor", "bughunter", "refactorer", "testwriter", "docindexer", "releasesheriff", "workspace-new", "workspace-index", "workspace-add", "workspace-search", "workspace-summarize", "help")]
    [string]$Agent = "help",
    
    [string]$Issue,
    [string]$File,
    [string]$Mode,
    [string]$Target,
    [string]$Slug,
    [string]$Name,
    [string]$Workspace,
    [string]$Path,
    [string[]]$Paths,
    [string]$Query,
    [switch]$DryRun,
    [switch]$Force,
    [switch]$SkipIndex,
    
    [Parameter(ValueFromRemainingArguments=$true)]
    $ExtraArgs
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Safe native command invoker - handles git stderr without crashing on exit 0
function Invoke-SafeNative {
    param(
        [Parameter(Mandatory=$true)][string]$FilePath,
        [string[]]$Arguments = @(),
        [switch]$AllowStderrWhenExitZero
    )
    
    # Use Start-Process to capture stdout/stderr separately
    $outFile = [System.IO.Path]::GetTempFileName()
    $errFile = [System.IO.Path]::GetTempFileName()
    
    try {
        $process = Start-Process -FilePath $FilePath -ArgumentList $Arguments `
            -RedirectStandardOutput $outFile `
            -RedirectStandardError $errFile `
            -NoNewWindow -PassThru -Wait
        
        $stdout = Get-Content $outFile -Raw
        $stderr = Get-Content $errFile -Raw
        $exitCode = $process.ExitCode
        
        if ($exitCode -ne 0) {
            $errorMsg = "Native command failed with exit code $exitCode`n"
            if ($stderr) { $errorMsg += "STDERR: $stderr`n" }
            if ($stdout) { $errorMsg += "STDOUT: $stdout" }
            throw $errorMsg
        }
        
        # Return object with all streams for caller to use
        @{
            ExitCode = $exitCode
            Stdout = $stdout
            Stderr = $stderr
        }
    } finally {
        Remove-Item $outFile, $errFile -Force -ErrorAction SilentlyContinue
    }
}

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
    Write-Host "Workspace Agents:" -ForegroundColor Cyan
    Write-Host "  workspace-new       Create a new workspace" -ForegroundColor Gray
    Write-Host "  workspace-index     Index a workspace's sources" -ForegroundColor Gray
    Write-Host "  workspace-add       Add files to a workspace" -ForegroundColor Gray
    Write-Host "  workspace-search    Search workspace files" -ForegroundColor Gray
    Write-Host "  workspace-summarize Generate BRIEF/KEY_TERMS/OPEN_QUESTIONS" -ForegroundColor Gray
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

# Handle workspace agents first (before main agent routing)
if ($Agent -eq "workspace-new") {
    $workspaceNewScript = Join-Path $PSScriptRoot "workspace_new.ps1"
    if (-not (Test-Path $workspaceNewScript)) {
        throw "workspace_new.ps1 not found: $workspaceNewScript"
    }
    Write-Host "[OK] Invoking workspace-new..." -ForegroundColor Green
    $workspaceParams = @{
        Name = $Name
    }
    if ($Force) { $workspaceParams.Force = $true }
    & $workspaceNewScript @workspaceParams
    exit 0
}

if ($Agent -eq "workspace-index") {
    $workspaceIndexScript = Join-Path $PSScriptRoot "workspace_index.ps1"
    if (-not (Test-Path $workspaceIndexScript)) {
        throw "workspace_index.ps1 not found: $workspaceIndexScript"
    }
    if (-not $Name) {
        throw "workspace-index requires -Name parameter"
    }
    Write-Host "[OK] Invoking workspace-index..." -ForegroundColor Green
    $indexParams = @{
        Name = $Name
    }
    & $workspaceIndexScript @indexParams
    exit 0
}

if ($Agent -eq "workspace-add") {
    $workspaceAddScript = Join-Path $PSScriptRoot "workspace_add.ps1"
    if (-not (Test-Path $workspaceAddScript)) {
        throw "workspace_add.ps1 not found: $workspaceAddScript"
    }
    if (-not $Name) {
        throw "workspace-add requires -Name parameter"
    }
    Write-Host "[OK] Invoking workspace-add..." -ForegroundColor Green
    $addParams = @{
        Name = $Name
    }
    if ($Path) { $addParams.Path = $Path }
    if ($Paths) { $addParams.Paths = $Paths }
    & $workspaceAddScript @addParams
    exit 0
}

if ($Agent -eq "workspace-search") {
    $workspaceSearchScript = Join-Path $PSScriptRoot "workspace_search.ps1"
    if (-not (Test-Path $workspaceSearchScript)) {
        throw "workspace_search.ps1 not found: $workspaceSearchScript"
    }
    if (-not $Name) {
        throw "workspace-search requires -Name parameter"
    }
    if (-not $Query) {
        throw "workspace-search requires -Query parameter"
    }
    Write-Host "[OK] Invoking workspace-search..." -ForegroundColor Green
    $searchParams = @{
        Name = $Name
        Query = $Query
    }
    & $workspaceSearchScript @searchParams
    exit 0
}

if ($Agent -eq "workspace-summarize") {
    $workspaceSummarizeScript = Join-Path $PSScriptRoot "workspace_summarize.ps1"
    if (-not (Test-Path $workspaceSummarizeScript)) {
        throw "workspace_summarize.ps1 not found: $workspaceSummarizeScript"
    }
    if (-not $Name) {
        throw "workspace-summarize requires -Name parameter"
    }
    Write-Host "[OK] Invoking workspace-summarize..." -ForegroundColor Green
    $summarizeParams = @{
        Name = $Name
    }
    & $workspaceSummarizeScript @summarizeParams
    exit 0
}

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
    
    # Invoke agent script directly in this process (avoids nested PowerShell stderr issues)
    # Build arguments as a hashtable for splatting
    $agentParams = @{
        ReportFile = $reportFile
        RepoRoot = $repoRoot
    }
    
    switch ($Agent) {
        "bughunter" { 
            $agentParams["Issue"] = $Issue
            if ($Mode) { $agentParams["Mode"] = $Mode }
            if ($Target) { $agentParams["Target"] = $Target }
            if ($Slug) { $agentParams["Slug"] = $Slug }
            if ($DryRun) { $agentParams["DryRun"] = $DryRun }
            & $agentScript @agentParams
        }
        "refactorer" { 
            $agentParams["File"] = $File
            & $agentScript @agentParams
        }
        "testwriter" { 
            $agentParams["File"] = $File
            & $agentScript @agentParams
        }
        default { 
            & $agentScript @agentParams
        }
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
