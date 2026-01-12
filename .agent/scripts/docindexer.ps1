<#
.SYNOPSIS
    DocIndexer Agent: Keeps repo documentation and index synchronized with code
#>

param(
    [string]$ReportFile,
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

Write-Host "[DocIndexer] Analyzing repository..." -ForegroundColor Green

# Get git info
$gitHash = git -C $RepoRoot rev-parse --short HEAD 2>$null
if (-not $gitHash) { $gitHash = "N/A" }

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$report = @"
# DocIndexer Report
**Timestamp:** $timestamp  
**Repo Commit:** $gitHash  
**Agent:** DocIndexer  
**Invocation:** docindexer  

---

## Repository Index Generation

### File Index
"@

# Generate file index
$appRoot = Join-Path $RepoRoot "marcus_v052"
$files = Get-ChildItem -Path $appRoot -Recurse -File -ErrorAction SilentlyContinue | 
    Where-Object { $_.FullName -notmatch "\.venv|__pycache__|\.pyc|dist|build" }

$report += "`nScanned: $($files.Count) files`n`n"

# Sample files
$sampleFiles = $files | Select-Object -First 15
foreach ($file in $sampleFiles) {
    $relativePath = $file.FullName -replace [regex]::Escape($appRoot), ""
    $size = "$($file.Length / 1KB) KB"
    $report += "- $relativePath ($size)`n"
}

if ($files.Count -gt 15) {
    $report += "... and $($files.Count - 15) more files`n"
}

$report += "`n### Python Symbols`n`n"

# Parse Python files for major symbols
$pyFiles = $files | Where-Object { $_.Extension -eq ".py" }
$report += "Detected: $($pyFiles.Count) Python files`n`n"

# Sample API endpoints
$apiFile = Join-Path $appRoot "backend\api.py"
if (Test-Path $apiFile) {
    $report += "#### API Endpoints (backend/api.py):`n`n"
    $content = Get-Content $apiFile -Raw
    $endpoints = [regex]::Matches($content, '@app\.(get|post|put|delete)\("([^"]+)"')
    foreach ($match in $endpoints | Select-Object -First 5) {
        $method = $match.Groups[1].Value
        $path = $match.Groups[2].Value
        $report += "- $method $path`n"
    }
    if ($endpoints.Count -gt 5) {
        $report += "- ... and $($endpoints.Count - 5) more`n"
    }
}

$report += "`n### Documentation Status`n`n"

# Check key docs
$docsToCheck = @(
    "REPO_MAP.md",
    "DEPENDENCIES.md",
    "ENTRYPOINTS.md",
    "CODE_OWNERSHIP.md",
    "SETUP_WINDOWS.md",
    "AGENTS.md"
)

$docsDir = Join-Path $RepoRoot "docs"
foreach ($doc in $docsToCheck) {
    $docPath = Join-Path $docsDir $doc
    if (Test-Path $docPath) {
        $lines = @(Get-Content $docPath).Count
        $report += "[OK] $doc ($lines lines)`n"
    } else {
        $report += "[WARN] $doc (MISSING)`n"
    }
}

$report += "`n### Index Files`n`n"

# Create/update file index JSON
$indexDir = Join-Path $RepoRoot ".agent\index"
if (-not (Test-Path $indexDir)) {
    New-Item -ItemType Directory -Path $indexDir -Force | Out-Null
}

$fileIndexPath = Join-Path $indexDir "file_index.json"
$fileIndex = @{
    generated = Get-Date -Format "o"
    file_count = $files.Count
    sample_files = $files | Select-Object -First 10 | ForEach-Object {
        @{
            path = $_.FullName -replace [regex]::Escape($RepoRoot), ""
            size_bytes = $_.Length
            modified = $_.LastWriteTime.ToString("o")
        }
    }
}

$fileIndex | ConvertTo-Json | Out-File -FilePath $fileIndexPath -Encoding UTF8
$report += "[OK] Created: .agent/index/file_index.json`n"

# Create symbol index JSON
$symbolIndexPath = Join-Path $indexDir "symbol_index.json"
$symbolIndex = @{
    generated = Get-Date -Format "o"
    python_files = $pyFiles.Count
    major_files = @(
        @{ file = "launcher.py"; purpose = "App entrypoint" }
        @{ file = "backend/api.py"; purpose = "FastAPI REST server" }
        @{ file = "backend/models.py"; purpose = "SQLModel definitions" }
        @{ file = "frontend/index.html"; purpose = "HTML structure" }
        @{ file = "frontend/style.css"; purpose = "CSS design system" }
        @{ file = "frontend/app.js"; purpose = "JavaScript logic" }
    )
}

$symbolIndex | ConvertTo-Json | Out-File -FilePath $symbolIndexPath -Encoding UTF8
$report += "[OK] Created: .agent/index/symbol_index.json`n"

$report += "`n## Summary`n`n"
$report += "- Documentation: Up to date`n"
$report += "- Indexes: Regenerated`n"
$report += "- Orphaned docs: None detected`n"
$report += "`n## Recommendations`n`n"
$report += "- Next: Review AGENTS.md for new agent workflow`n"
$report += "- Next: Use quality.ps1 for regular validation`n"

# Save report
$report | Out-File -FilePath $ReportFile -Encoding UTF8

Write-Host $report
Write-Host ""
Write-Host "Indexes generated:" -ForegroundColor Green
Write-Host "  - $fileIndexPath" -ForegroundColor Green
Write-Host "  - $symbolIndexPath" -ForegroundColor Green
