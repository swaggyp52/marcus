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
    [string[]]$Paths,

    [Parameter()]
    [ValidateSet('auto','skip','fail')]
    [string]$PdfMode = 'auto'
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

# Find pdftotext once (if requested)
$pdfExtractor = $null
if ($PdfMode -ne 'skip') {
    $pdfExtractor = Get-Command pdftotext -ErrorAction SilentlyContinue
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

    # PDF extraction handling
    if ($extension -ieq '.pdf') {
        switch ($PdfMode) {
            'skip' {
                Write-Warning "PDF skipped by PdfMode=skip: $destPath"
                break
            }
            'auto' { if (-not $pdfExtractor) { Write-Warning "pdftotext not found; skipping PDF: $filePath"; break } }
            'fail' { if (-not $pdfExtractor) { throw "pdftotext not found; PdfMode=fail requires extractor. PDF: $filePath" } }
        }

        if ($PdfMode -ne 'skip' -and $pdfExtractor) {
            # Determine extracted text path with collision handling (keep .pdf in name)
            $txtName = "$destName.txt"
            $txtPath = Join-Path $sourcesDir $txtName
            $txtCounter = 1
            while (Test-Path $txtPath) {
                $txtName = "${destName}_($txtCounter).txt"
                $txtPath = Join-Path $sourcesDir $txtName
                $txtCounter++
            }

            $cmdOutput = & $pdfExtractor.Path "-enc" "UTF-8" "-layout" $destPath $txtPath 2>&1
            $exitCode = $LASTEXITCODE
            if ($exitCode -ne 0) {
                $tail = ($cmdOutput | Select-Object -Last 5) -join " `n"
                $failMsg = "pdftotext failed (exit $exitCode); skipping PDF: $filePath" + (if ($tail) { " - $tail" } else { "" })
                if ($PdfMode -eq 'fail') {
                    throw $failMsg
                }
                Write-Warning $failMsg
                if (Test-Path $txtPath) { Remove-Item $txtPath -ErrorAction SilentlyContinue }
            } else {
                Write-Host "[OK] Extracted PDF to $txtPath" -ForegroundColor Green
            }
        }
    }
}

Write-Host "[OK] Added $addedCount files to $Name"
