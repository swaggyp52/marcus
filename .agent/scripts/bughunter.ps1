<#
.SYNOPSIS
    BugHunter Agent - Analyzes bugs, searches codebase, proposes fixes
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Issue,
    [string]$ReportFile,
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Get git info
$gitHash = git -C $RepoRoot rev-parse --short HEAD 2>$null
if (-not $gitHash) { $gitHash = "N/A" }

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$report = @"
# BugHunter Report
**Timestamp:** $timestamp  
**Repo Commit:** $gitHash  
**Agent:** BugHunter  
**Invocation:** bughunter -Issue "$Issue"  

---

## Issue Description

$Issue

## Environment Analysis

### Repository Status
"@

# Check git status
try {
    $gitStatus = git -C $RepoRoot status --short 2>&1 | Out-String
    if ($gitStatus.Trim()) {
        $report += "`n``````"
        $report += "`n$gitStatus"
        $report += "``````"
    } else {
        $report += "`nClean working directory"
    }
} catch {
    $report += "`nGit status unavailable"
}

$report += "`n`n### Python Environment"

# Check Python
try {
    $pyVersion = & python --version 2>&1
    $report += "`n- Python: $pyVersion"
} catch {
    $report += "`n- Python: NOT FOUND"
}

# Check installed packages
$appRoot = Join-Path $RepoRoot "marcus_v052"
$reqFile = Join-Path $appRoot "requirements.txt"
if (Test-Path $reqFile) {
    $packages = (Get-Content $reqFile | Measure-Object -Line).Lines
    $report += "`n- requirements.txt: $packages packages"
} else {
    $report += "`n- requirements.txt: NOT FOUND"
}

$report += "`n`n## Codebase Search"

# Search for relevant keywords from issue
$keywords = @()
if ($Issue -match "react|React") { $keywords += "React" }
if ($Issue -match "loop|infinite|storm") { $keywords += "loop", "while", "for", "useEffect" }
if ($Issue -match "185|#185") { $keywords += "185" }
if ($Issue -match "backend|api|endpoint") { $keywords += "api", "endpoint", "@app" }
if ($Issue -match "frontend|ui|html|css") { $keywords += "html", "css", "js" }

if ($keywords.Count -eq 0) {
    # Fallback: generic error terms
    $keywords = @("error", "exception", "fail")
}

$report += "`n`n### Search Keywords"
$report += "`n" + ($keywords -join ", ")

$report += "`n`n### Probable Components"

# Search for keywords in codebase
$searchResults = @{}
foreach ($kw in $keywords | Select-Object -First 3) {
    try {
        $matches = Get-ChildItem -Path $appRoot -Recurse -File -Include *.py,*.js,*.html |
            Where-Object { $_.FullName -notmatch "(__pycache__|\.venv|node_modules|dist|build)" } |
            Select-String -Pattern $kw -CaseSensitive:$false |
            Select-Object -First 5
        
        if ($matches) {
            $searchResults[$kw] = $matches
        }
    } catch {
        # Skip if search fails
    }
}

if ($searchResults.Count -gt 0) {
    foreach ($kw in $searchResults.Keys) {
        $report += "`n`n**Keyword: $kw**"
        foreach ($match in $searchResults[$kw]) {
            $relPath = $match.Path -replace [regex]::Escape($appRoot), ""
            $report += "`n- $relPath`:$($match.LineNumber)"
        }
    }
} else {
    $report += "`n- No direct matches found for search keywords"
}

$report += "`n`n## Repro Steps Scaffold"
$report += @"

1. Verify environment:
   ``````powershell
   python --version
   Test-Path .\marcus_v052\.venv
   Test-Path .\marcus_v052\requirements.txt
   ``````

2. Start application:
   ``````powershell
   cd marcus_v052
   .\.venv\Scripts\Activate.ps1
   python launcher.py
   ``````

3. Access frontend and reproduce issue:
   - Open browser to http://localhost:8000
   - Follow steps from issue description
   - Monitor console for errors

4. Capture logs/screenshots:
   - Backend logs (terminal output)
   - Browser console (F12 -> Console)
   - Network tab if relevant

"@

$report += "`n## First Suspect Analysis"

# Heuristic: if "loop" mentioned, look for useEffect, while, or polling
if ($Issue -match "loop|infinite|storm|hang") {
    $report += "`n`n**Suspect: Infinite Loop / Polling Storm**"
    $report += "`n- Check for:"
    $report += "`n  - Frontend: useEffect without dependency array"
    $report += "`n  - Frontend: Polling intervals (setInterval/setTimeout)"
    $report += "`n  - Backend: Unthrottled endpoints being hit repeatedly"
    $report += "`n  - Backend: Missing pagination/limits on queries"
    
    # Try to find frontend JS files
    $jsFiles = Get-ChildItem -Path $appRoot -Filter "*.js" -Recurse |
        Where-Object { $_.FullName -notmatch "(node_modules|dist|build)" } |
        Select-Object -First 3
    
    if ($jsFiles) {
        $report += "`n`n**JavaScript files to inspect:**"
        foreach ($file in $jsFiles) {
            $relPath = $file.FullName -replace [regex]::Escape($appRoot), ""
            $report += "`n- $relPath"
        }
    }
}

if ($Issue -match "crash|error|exception|fail") {
    $report += "`n`n**Suspect: Exception / Runtime Error**"
    $report += "`n- Check recent git changes for introduced bugs"
    $report += "`n- Review error logs in backend console"
    $report += "`n- Validate input handling / edge cases"
}

$report += "`n`n## Proposed Minimal Fix Plan"
$report += @"

### Step 1: Isolate Root Cause
- Add debug logging around suspected hotspot
- Reproduce issue with minimal steps
- Confirm fix hypothesis with isolated test

### Step 2: Implement Fix
- Apply smallest possible change to address root cause
- Avoid refactoring unrelated code
- Document fix reasoning in commit message

### Step 3: Verify Fix
- Run repro steps to confirm issue resolved
- Run regression tests (if available)
- Check for side effects in related features

### Step 4: Prevent Recurrence
- Add unit test or integration test
- Update documentation if behavior was ambiguous
- Consider adding guardrails (rate limiting, timeouts, etc.)

"@

$report += "`n## Recommended Next Actions"
$report += @"

1. **Reproduce:** Follow repro steps above to confirm issue
2. **Isolate:** Use search results to narrow down suspect files
3. **Fix:** Implement minimal fix in new branch
4. **Test:** Verify fix works and doesn't break other features
5. **Document:** Update issue with findings and resolution

"@

$report += "`n## Status"
$report += "`n[INFO] Analysis complete - Manual reproduction and fix implementation required"

# Save report
$report | Out-File -FilePath $ReportFile -Encoding UTF8

Write-Host $report
Write-Host ""
Write-Host "Analysis complete. Review report for next steps." -ForegroundColor Green

exit 0
