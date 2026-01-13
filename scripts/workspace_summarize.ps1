<#
.SYNOPSIS
    Summarize workspace content into structured documents.

.DESCRIPTION
    Reads workspace sources and generates:
    - BRIEF.md: 1-2 page overview
    - KEY_TERMS.md: Vocabulary and definitions
    - OPEN_QUESTIONS.md: Unclear topics

.PARAMETER Name
    The workspace name.

.EXAMPLE
    .\workspace_summarize.ps1 -Name ece381
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name
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
$indexDir = Join-Path $workspaceRoot "index"

# Text-readable extensions
$textExtensions = @('.txt', '.md', '.csv', '.json')

# Collect content from text files
$sourceContent = @()
foreach ($entry in $indexData) {
    if ($textExtensions -contains $entry.extension) {
        $filePath = Join-Path $workspaceRoot $entry.relativePath
        
        if (Test-Path $filePath) {
            try {
                $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
                $sourceContent += [PSCustomObject]@{
                    FileName = $entry.fileName
                    Content = $content
                    Extension = $entry.extension
                }
            } catch {
                Write-Warning "Could not read: $($entry.fileName)"
            }
        }
    }
}

# Generate BRIEF.md
$briefPath = Join-Path $indexDir "BRIEF.md"
$briefContent = @"
# Workspace Brief: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Summary

"@

if ($sourceContent.Count -eq 0) {
    $briefContent += @"
No text sources available yet.

Add files with:
``````
.\scripts\agent.ps1 workspace-add -Name $Name -Paths @("path\to\file.txt")
``````
"@
} else {
    $briefContent += @"
This workspace contains $($sourceContent.Count) text file(s).

## Sources

"@
    foreach ($source in $sourceContent) {
        $lines = ($source.Content -split "`r?`n").Count
        $chars = $source.Content.Length
        $briefContent += "- **$($source.FileName)** ($lines lines, $chars chars)`n"
    }
    
    $briefContent += @"

## Content Overview

"@
    
    # Extract first few lines from each file as preview
    foreach ($source in $sourceContent) {
        $preview = ($source.Content -split "`r?`n" | Select-Object -First 5) -join "`n"
        $briefContent += @"

### $($source.FileName)

``````
$preview
``````

"@
    }
}

$briefContent | Set-Content $briefPath -Encoding UTF8

# Generate KEY_TERMS.md
$keyTermsPath = Join-Path $indexDir "KEY_TERMS.md"
$keyTermsContent = @"
# Key Terms: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

"@

if ($sourceContent.Count -eq 0) {
    $keyTermsContent += "No sources yet. Add files to extract terminology.`n"
} else {
    $keyTermsContent += @"
## Extracted Terms

"@
    # Simple term extraction: look for capitalized words or technical patterns
    $allText = ($sourceContent | ForEach-Object { $_.Content }) -join " "
    $words = $allText -split '\s+' | Where-Object { $_ -match '^[A-Z][a-z]+$' } | Select-Object -Unique | Sort-Object
    
    if ($words.Count -gt 0) {
        $terms = $words | Select-Object -First 50
        foreach ($term in $terms) {
            $keyTermsContent += "- **$term**: _(definition needed)_`n"
        }
    } else {
        $keyTermsContent += "No obvious terms extracted. Review sources manually.`n"
    }
    
    $keyTermsContent += @"

## Sources Referenced

"@
    foreach ($source in $sourceContent) {
        $keyTermsContent += "- $($source.FileName)`n"
    }
}

$keyTermsContent | Set-Content $keyTermsPath -Encoding UTF8

# Generate OPEN_QUESTIONS.md
$openQuestionsPath = Join-Path $indexDir "OPEN_QUESTIONS.md"
$openQuestionsContent = @"
# Open Questions: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

"@

if ($sourceContent.Count -eq 0) {
    $openQuestionsContent += "No sources yet. Add files to identify unclear topics.`n"
} else {
    $openQuestionsContent += @"
## Questions to Investigate

"@
    
    # Look for question marks or TODO patterns
    $questions = @()
    foreach ($source in $sourceContent) {
        $lines = $source.Content -split "`r?`n"
        for ($i = 0; $i -lt $lines.Count; $i++) {
            $line = $lines[$i]
            if ($line -match '\?|TODO|FIXME|XXX|UNCLEAR') {
                $questions += [PSCustomObject]@{
                    Source = $source.FileName
                    LineNum = $i + 1
                    Text = $line.Trim()
                }
            }
        }
    }
    
    if ($questions.Count -gt 0) {
        foreach ($q in $questions) {
            $openQuestionsContent += "- [ ] $($q.Text) _($($q.Source):$($q.LineNum))_`n"
        }
    } else {
        $openQuestionsContent += @"
No explicit questions found in sources.

## Suggested Review Topics

- Review course objectives
- Identify prerequisite knowledge gaps
- List upcoming assignments or exams
- Note confusing concepts from lectures

"@
    }
    
    $openQuestionsContent += @"

## Sources Reviewed

"@
    foreach ($source in $sourceContent) {
        $openQuestionsContent += "- $($source.FileName)`n"
    }
}

$openQuestionsContent | Set-Content $openQuestionsPath -Encoding UTF8

Write-Host "[OK] Workspace summarized: $Name"
Write-Host "     - $briefPath"
Write-Host "     - $keyTermsPath"
Write-Host "     - $openQuestionsPath"
