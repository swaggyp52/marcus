<#
.SYNOPSIS
    Single-command pipeline for workspace processing.

.DESCRIPTION
    Runs add (optional), index, summarize, plan, and quiz in one command.
    Uses a single runId so all archived outputs land in the same run folder.

.PARAMETER Name
    Workspace name.

.PARAMETER Paths
    Optional file paths to add before running pipeline.

.PARAMETER Path
    Optional single file path (convenience).

.PARAMETER Count
    Number of quiz questions (default 15).
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name,

    [Parameter()]
    [string[]]$Paths,

    [Parameter()]
    [string]$Path,

    [Parameter()]
    [int]$Count = 15
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Load workspace library
. (Join-Path $PSScriptRoot "_workspace_lib.ps1")

# Resolve workspace location
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Join-Path $repoRoot "workspaces\$Name"
if (-not (Test-Path $workspaceRoot)) {
    throw "Workspace not found: $workspaceRoot. Run workspace-new first."
}

# Normalize paths input
if (-not $Paths -and $Path) {
    $Paths = @($Path)
}

# Script paths
$workspaceAddScript = Join-Path $PSScriptRoot "workspace_add.ps1"
$workspaceIndexScript = Join-Path $PSScriptRoot "workspace_index.ps1"
$workspaceSummarizeScript = Join-Path $PSScriptRoot "workspace_summarize.ps1"
$workspacePlanScript = Join-Path $PSScriptRoot "workspace_plan.ps1"
$workspaceQuizScript = Join-Path $PSScriptRoot "workspace_quiz.ps1"

# Create single run
$runMeta = Initialize-WorkspaceRun -WorkspaceRoot $workspaceRoot -Command "workspace-run"
$runId = $runMeta.RunId

# 1) Add (optional)
if ($Paths -and $Paths.Count -gt 0) {
    $addParams = @{ Name = $Name; Paths = $Paths }
    & $workspaceAddScript @addParams
}

# 2) Index
& $workspaceIndexScript -Name $Name -RunId $runId

# 3) Summarize
& $workspaceSummarizeScript -Name $Name -RunId $runId

# 4) Plan
& $workspacePlanScript -Name $Name -RunId $runId

# 5) Quiz
& $workspaceQuizScript -Name $Name -Count $Count -RunId $runId

# Output summary
$indexDir = Join-Path $workspaceRoot "index"
$runDir = Join-Path $indexDir "runs\$runId"

$currentOutputs = @(
    Join-Path $indexDir "sources_index.json"
    Join-Path $indexDir "BRIEF.md"
    Join-Path $indexDir "KEY_TERMS.md"
    Join-Path $indexDir "OPEN_QUESTIONS.md"
    Join-Path $indexDir "STUDY_PLAN.md"
    Join-Path $indexDir "NEXT_ACTIONS.md"
    Join-Path $indexDir "QUIZ_01.md"
    Join-Path $indexDir "QUIZ_01_ANSWERS.md"
)

$archivedOutputs = @(
    Join-Path $runDir "sources_index.json"
    Join-Path $runDir "BRIEF.md"
    Join-Path $runDir "KEY_TERMS.md"
    Join-Path $runDir "OPEN_QUESTIONS.md"
    Join-Path $runDir "STUDY_PLAN.md"
    Join-Path $runDir "NEXT_ACTIONS.md"
    Join-Path $runDir "QUIZ_01.md"
    Join-Path $runDir "QUIZ_01_ANSWERS.md"
)

Write-Host "[OK] Workspace run complete: $Name" -ForegroundColor Green
Write-Host "RunId: $runId"
Write-Host "Current outputs:" -ForegroundColor Gray
$currentOutputs | ForEach-Object { Write-Host "  $_" }
Write-Host "Archived outputs (run folder):" -ForegroundColor Gray
$archivedOutputs | ForEach-Object { Write-Host "  $_" }
