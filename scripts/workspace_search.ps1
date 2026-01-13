<#
.SYNOPSIS
    Search workspace files by name and content.

.DESCRIPTION
    Searches workspace files by filename and text content.
    Only searches content for text-like files: .txt, .md, .csv, .json

.PARAMETER Name
    The workspace name.

.PARAMETER Query
    The search query string.

.EXAMPLE
    .\workspace_search.ps1 -Name ece381 -Query "midterm"
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name,

    [Parameter(Mandatory)]
    [string]$Query,

    [Parameter()]
    [int]$Top = 10
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Resolve workspace location
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Join-Path $repoRoot "workspaces\$Name"

if (-not (Test-Path $workspaceRoot)) {
    throw "Workspace not found: $workspaceRoot"
}

$indexPath = Join-Path $workspaceRoot "index\sources_index.json"
if (-not (Test-Path $indexPath)) {
    throw "Index not found: $indexPath. Run workspace-index first."
}

$indexData = Get-Content $indexPath -Raw | ConvertFrom-Json

# Text-searchable extensions
$textExtensions = @('.txt', '.md', '.csv', '.json')
$maxReadBytes = 200KB

$results = @()

foreach ($entry in $indexData) {
    $filePath = Join-Path $workspaceRoot $entry.relativePath
    
    if (-not (Test-Path $filePath)) {
        continue
    }

    $score = 0
    $snippet = ""

    # Search filename
    if ($entry.fileName -like "*$Query*") {
        $score += 10
        $snippet = "Filename match"
    }

    # Search content for text files
    if ($textExtensions -contains $entry.extension) {
        try {
            $content = ""
            
            if ($entry.bytes -le $maxReadBytes) {
                $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
            } else {
                # Read first chunk
                $bytes = [System.IO.File]::ReadAllBytes($filePath) | Select-Object -First $maxReadBytes
                $content = [System.Text.Encoding]::UTF8.GetString($bytes)
            }

            if ($content -like "*$Query*") {
                $score += 5
                
                # Extract snippet around match
                $index = $content.IndexOf($Query, [StringComparison]::OrdinalIgnoreCase)
                if ($index -ge 0) {
                    $start = [Math]::Max(0, $index - 30)
                    $length = [Math]::Min(80, $content.Length - $start)
                    $snippet = "..." + $content.Substring($start, $length).Trim() + "..."
                    $snippet = $snippet -replace '\r?\n', ' '
                }
            }
        } catch {
            # Ignore read errors
        }
    }

    if ($score -gt 0) {
        $results += [PSCustomObject]@{
            Score = $score
            File = $entry.fileName
            Snippet = $snippet
        }
    }
}

if ($results.Count -eq 0) {
    Write-Host "No matches found for: $Query"
} else {
    $results | Sort-Object -Property Score -Descending | Select-Object -First $Top | Format-Table -AutoSize
}
