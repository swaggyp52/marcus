<#
.SYNOPSIS
    Add files to a workspace's sources folder.

.DESCRIPTION
    Copies files into workspaces\<Name>\sources\.
    Handles filename collisions by appending _(1), _(2), etc.

.PARAMETER Name
    The workspace name.

.PARAMETER Path
    A single file path to add.

.PARAMETER Paths
    An array of file paths to add.

.EXAMPLE
    .\workspace_add.ps1 -Name ece381 -Path "C:\notes\lecture.pdf"

.EXAMPLE
    .\workspace_add.ps1 -Name ece381 -Paths @("C:\notes\a.pdf", "C:\notes\b.docx")
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name,

    [Parameter(ParameterSetName='Single')]
    [string]$Path,

    [Parameter(ParameterSetName='Multiple')]
    [string[]]$Paths
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve workspace location
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Join-Path $repoRoot "workspaces\$Name"

if (-not (Test-Path $workspaceRoot)) {
    throw "Workspace not found: $workspaceRoot. Run workspace-new first."
}

$sourcesDir = Join-Path $workspaceRoot "sources"
if (-not (Test-Path $sourcesDir)) {
    New-Item -ItemType Directory -Force -Path $sourcesDir | Out-Null
}

# Normalize input to array
$filesToAdd = @()
if ($PSCmdlet.ParameterSetName -eq 'Single') {
    $filesToAdd = @($Path)
} else {
    $filesToAdd = $Paths
}

# Copy files with collision handling
$addedCount = 0
foreach ($filePath in $filesToAdd) {
    if (-not (Test-Path $filePath)) {
        Write-Warning "File not found, skipping: $filePath"
        continue
    }

    $item = Get-Item $filePath
    if ($item.PSIsContainer) {
        Write-Warning "Directories not supported, skipping: $filePath"
        continue
    }

    # Determine destination with collision handling
    $baseName = [System.IO.Path]::GetFileNameWithoutExtension($item.Name)
    $extension = $item.Extension
    $destName = $item.Name
    $destPath = Join-Path $sourcesDir $destName

    $counter = 1
    while (Test-Path $destPath) {
        $destName = "${baseName}_($counter)${extension}"
        $destPath = Join-Path $sourcesDir $destName
        $counter++
    }

    Copy-Item -Path $filePath -Destination $destPath -Force
    $addedCount++
}

Write-Host "[OK] Added $addedCount files to $Name"
