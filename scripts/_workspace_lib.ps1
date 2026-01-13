<#
.SYNOPSIS
    Shared library functions for workspace scripts.

.DESCRIPTION
    Provides common functionality for workspace commands:
    - Run folder creation and archiving
    - runs.json logging
    - LATEST.txt tracking
#>

<#
.SYNOPSIS
    Initialize a new run folder and return run metadata.

.DESCRIPTION
    Creates workspaces/<Name>/index/runs/YYYY-MM-DD_HHMMSS/ folder
    and returns metadata for logging.

.PARAMETER WorkspaceRoot
    The full path to the workspace root (workspaces/<Name>).

.PARAMETER Command
    The command name (e.g., "workspace-summarize").

.OUTPUTS
    Hashtable with: RunFolder, RunId, Timestamp, Command
#>
function Initialize-WorkspaceRun {
    param(
        [Parameter(Mandatory)]
        [string]$WorkspaceRoot,
        
        [Parameter(Mandatory)]
        [string]$Command
    )
    
    $indexDir = Join-Path $WorkspaceRoot "index"
    $runsDir = Join-Path $indexDir "runs"
    
    # Create runs directory if missing
    if (-not (Test-Path $runsDir)) {
        New-Item -ItemType Directory -Force -Path $runsDir | Out-Null
    }
    
    # Generate run ID
    $runId = Get-Date -Format "yyyy-MM-dd_HHmmss"
    $runFolder = Join-Path $runsDir $runId
    
    # Create run folder
    New-Item -ItemType Directory -Force -Path $runFolder | Out-Null
    
    # Update LATEST.txt
    $latestPath = Join-Path $runsDir "LATEST.txt"
    $runId | Set-Content $latestPath -Encoding UTF8
    
    @{
        RunFolder = $runFolder
        RunId = $runId
        Timestamp = (Get-Date).ToString("o")
        Command = $Command
    }
}

<#
.SYNOPSIS
    Archive a file to the current run folder.

.DESCRIPTION
    Copies a file to the run folder and returns the relative path.

.PARAMETER FilePath
    The full path to the file to archive.

.PARAMETER RunFolder
    The full path to the run folder.

.OUTPUTS
    String: relative path to archived file (from index/ directory)
#>
function Add-ToRun {
    param(
        [Parameter(Mandatory)]
        [string]$FilePath,
        
        [Parameter(Mandatory)]
        [string]$RunFolder
    )
    
    if (-not (Test-Path $FilePath)) {
        Write-Warning "File not found for archiving: $FilePath"
        return $null
    }
    
    $fileName = Split-Path $FilePath -Leaf
    $destPath = Join-Path $RunFolder $fileName
    
    Copy-Item -Path $FilePath -Destination $destPath -Force
    
    # Return relative path from index/ directory
    $runId = Split-Path $RunFolder -Leaf
    "runs/$runId/$fileName"
}

<#
.SYNOPSIS
    Finalize a run by logging to runs.json.

.DESCRIPTION
    Appends run metadata to runs.json with archived file paths.

.PARAMETER WorkspaceRoot
    The full path to the workspace root.

.PARAMETER RunMetadata
    Hashtable from Initialize-WorkspaceRun.

.PARAMETER ArchivedFiles
    Array of relative paths to archived files.
#>
function Complete-WorkspaceRun {
    param(
        [Parameter(Mandatory)]
        [string]$WorkspaceRoot,
        
        [Parameter(Mandatory)]
        [hashtable]$RunMetadata,
        
        [Parameter()]
        [string[]]$ArchivedFiles = @()
    )
    
    $indexDir = Join-Path $WorkspaceRoot "index"
    $runsJsonPath = Join-Path $indexDir "runs\runs.json"
    
    # Get git commit hash if available
    $gitCommit = $null
    try {
        $gitCommit = (git rev-parse --short HEAD 2>$null) | Out-String
        $gitCommit = $gitCommit.Trim()
    } catch {
        # Git not available or not a repo
    }
    
    # Build run entry
    $runEntry = [PSCustomObject]@{
        timestamp = $RunMetadata.Timestamp
        runId = $RunMetadata.RunId
        command = $RunMetadata.Command
        outputs = $ArchivedFiles
        gitCommit = $gitCommit
    }
    
    # Append to runs.json
    $existingRuns = @()
    if (Test-Path $runsJsonPath) {
        try {
            $content = Get-Content $runsJsonPath -Raw
            if ($content.Trim() -ne "") {
                $existingRuns = $content | ConvertFrom-Json
            }
        } catch {
            # Invalid JSON, start fresh
        }
    }
    
    $allRuns = @($existingRuns) + $runEntry
    $allRuns | ConvertTo-Json -Depth 10 | Set-Content $runsJsonPath -Encoding UTF8
}
