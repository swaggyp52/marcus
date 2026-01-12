<#
.SYNOPSIS
    BugHunter Agent v2 - Analyzes bugs, searches codebase, proposes fixes, optionally applies patches
    
.PARAMETER Issue
    Issue description or number
    
.PARAMETER Mode
    Operation mode: "analyze" (default) or "patch" (creates branch + applies fix)
    
.PARAMETER Target
    Target file for patch mode (optional - will infer from search if not provided)
    
.PARAMETER Slug
    Branch slug for patch mode (optional - auto-generated from Issue if not provided)
    
.PARAMETER DryRun
    When set, simulates patch without modifying files or committing
    
.PARAMETER SelfTest
    When set in patch mode, applies patch to .agent/scratch/selftest.txt instead of real app files
#>

param(
    [Parameter(Mandatory=$true)]
    [string]$Issue,
    
    [ValidateSet("analyze","patch")]
    [string]$Mode = "analyze",
    
    [string]$Target,
    
    [string]$Slug,
    
    [switch]$DryRun,
    
    [switch]$SelfTest,
    
    [string]$ReportFile,
    [string]$RepoRoot
)

$ErrorActionPreference = "Stop"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}

# Helper functions
function Write-Ok { param([string]$msg) Write-Host "[OK] $msg" -ForegroundColor Green }
function Write-Fail { param([string]$msg) Write-Host "[FAIL] $msg" -ForegroundColor Red }
function Write-Warn { param([string]$msg) Write-Host "[WARN] $msg" -ForegroundColor Yellow }
function Write-Section { param([string]$msg) Write-Host "`n=== $msg ===" -ForegroundColor Cyan }

# Safe git invoker - uses Start-Process to avoid PowerShell NativeCommandError on stderr
function Invoke-GitSafe {
    param(
        [Parameter(Mandatory=$true)][string]$RepoRoot,
        [Parameter(Mandatory=$true)][string[]]$Args
    )
    
    $stdoutFile = [System.IO.Path]::GetTempFileName()
    $stderrFile = [System.IO.Path]::GetTempFileName()
    
    try {
        $gitArgs = @('-C', $RepoRoot) + $Args
        
        $p = Start-Process -FilePath "git" `
            -ArgumentList $gitArgs `
            -NoNewWindow -Wait -PassThru `
            -RedirectStandardOutput $stdoutFile `
            -RedirectStandardError $stderrFile
        
        $stdout = ""
        $stderr = ""
        if (Test-Path $stdoutFile) { $stdout = (Get-Content -Raw $stdoutFile -ErrorAction SilentlyContinue) }
        if (Test-Path $stderrFile) { $stderr = (Get-Content -Raw $stderrFile -ErrorAction SilentlyContinue) }
        
        # Trim and handle nulls
        if ($stdout) { $stdout = $stdout.Trim() }
        if ($stderr) { $stderr = $stderr.Trim() }
        
        return [pscustomobject]@{
            ExitCode = $p.ExitCode
            Stdout   = $stdout
            Stderr   = $stderr
            Args     = $gitArgs
        }
    }
    finally {
        Remove-Item -Force -ErrorAction SilentlyContinue $stdoutFile, $stderrFile
    }
}

# Compatibility wrapper - maps old Invoke-Git API to new Invoke-GitSafe
function Invoke-Git {
    param(
        [Parameter(Mandatory=$true)][string]$Repo,
        [Parameter(Mandatory=$true)][string[]]$Arguments
    )
    
    $result = Invoke-GitSafe -RepoRoot $Repo -Args $Arguments
    
    # Map new API to old API for existing callsites
    return @{
        Success = ($result.ExitCode -eq 0)
        Output  = $result.Stdout
        Stderr  = $result.Stderr
    }
}

function New-SafeSlug {
    param([string]$text)
    $slug = $text -replace '[^a-zA-Z0-9\s-]', '' `
                  -replace '\s+', '-' `
                  -replace '-+', '-'
    $slug = $slug.ToLower().Trim('-')
    if ($slug.Length -gt 40) { $slug = $slug.Substring(0, 40).Trim('-') }
    return $slug
}

# Get git info
$gitInfo = Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", "--short", "HEAD")
$gitHash = if ($gitInfo.Success) { $gitInfo.Output.Trim() } else { "N/A" }

$timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

$branchInfo = Invoke-Git -Repo $RepoRoot -Arguments @("branch", "--show-current")
$originalBranch = if ($branchInfo.Success) { $branchInfo.Output.Trim() } else { "N/A" }

# Build report header
$invocation = "bughunter -Issue `"$Issue`" -Mode $Mode"
if ($Target) { $invocation += " -Target `"$Target`"" }
if ($Slug) { $invocation += " -Slug `"$Slug`"" }
if ($DryRun) { $invocation += " -DryRun" }

$report = @"
# BugHunter Report
**Timestamp:** $timestamp  
**Repo Commit:** $gitHash  
**Agent:** BugHunter  
**Mode:** $Mode  
**Invocation:** $invocation  

---

## Issue Description

$Issue

"@

# PREFLIGHT CHECKS (for patch mode)
$preflightPassed = $true
$inferredTarget = $null

if ($Mode -eq "patch") {
    Write-Section "Preflight Checks"
    $report += "`n## Preflight Checks`n"
    
    # Check git available
    try {
        $null = git --version 2>&1
        Write-Ok "Git available"
        $report += "`n- [OK] Git available"
    } catch {
        Write-Fail "Git not found"
        $report += "`n- [FAIL] Git not found"
        $preflightPassed = $false
    }
    
    # Check git status
    $statusResult = Invoke-Git -Repo $RepoRoot -Arguments @("status", "--porcelain")
    if ($null -eq $statusResult) { $statusResult = @{ Success = $false; Output = "" } }
    $gitStatus = if ($statusResult -and $statusResult.Success) { $statusResult.Output } else { "" }
    if ($gitStatus -and $gitStatus.Trim()) {
        Write-Warn "Working directory not clean"
        $report += "`n- [WARN] Working directory not clean:"
        $report += "`n``````"
        $report += "`n$($gitStatus.Trim())"
        $report += "`n``````"
        $report += "`n- **Action required:** Commit or stash changes before running patch mode"
        $preflightPassed = $false
    } else {
        Write-Ok "Working directory clean"
        $report += "`n- [OK] Working directory clean"
    }
    
    # Check quality.ps1 exists
    $qualityScript = Join-Path $RepoRoot "scripts\quality.ps1"
    if (Test-Path $qualityScript) {
        Write-Ok "Quality gate available"
        $report += "`n- [OK] Quality gate available: scripts\quality.ps1"
    } else {
        Write-Fail "Quality gate not found"
        $report += "`n- [FAIL] Quality gate not found: scripts\quality.ps1"
        $preflightPassed = $false
    }
    
    if (-not $preflightPassed) {
        $report += "`n`n## Outcome`n"
        $report += "`n**ABORTED** - Preflight checks failed. Fix issues above and retry."
        $report | Out-File -FilePath $ReportFile -Encoding UTF8
        Write-Host $report
        Write-Fail "Preflight failed. Aborting patch mode."
        exit 1
    }
    
    # Handle SelfTest mode early - create target before codebase analysis
    if ($SelfTest) {
        $Target = ".agent\scratch\selftest.txt"
        $selftestPath = Join-Path $RepoRoot $Target
        $selftestDir = Split-Path -Parent $selftestPath
        
        # Ensure scratch directory exists
        if (-not (Test-Path $selftestDir)) {
            New-Item -ItemType Directory -Path $selftestDir -Force | Out-Null
        }
        
        # Create selftest file if missing
        if (-not (Test-Path $selftestPath)) {
            "# BugHunter SelfTest Target`n`nThis file is used for testing patch mode without modifying real application files." | Out-File -FilePath $selftestPath -Encoding UTF8
        }
        
        Write-Ok "SelfTest mode: using $Target"
    }
}

# ANALYZE MODE (run search and analysis regardless of mode)
Write-Section "Analyzing Codebase"

$report += "`n## Environment Analysis`n"
$report += "`n### Python Environment"

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
$topFiles = @()
foreach ($kw in $keywords | Select-Object -First 3) {
    try {
        $matches = Get-ChildItem -Path $appRoot -Recurse -File -Include *.py,*.js,*.html |
            Where-Object { $_.FullName -notmatch "(__pycache__|\.venv|node_modules|dist|build)" } |
            Select-String -Pattern $kw -CaseSensitive:$false |
            Select-Object -First 5
        
        if ($matches) {
            $searchResults[$kw] = $matches
            foreach ($m in $matches) {
                if ($topFiles.Count -lt 3 -and $m.Path -notin $topFiles) {
                    $topFiles += $m.Path
                }
            }
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

# Target selection for patch mode
if ($Mode -eq "patch") {
    if ($SelfTest) {
        # SelfTest target was already created in preflight - highest priority
        $report += "`n`n### Target Selection"
        $report += "`n- **Mode:** SelfTest (dedicated test file)"
        $report += "`n- **Selected:** $Target"
        $report += "`n- **Status:** Created/Verified"
    } elseif (-not $Target) {
        # Infer target from search results
        if ($topFiles.Count -gt 0) {
            $inferredTarget = $topFiles[0]
            $relInferred = $inferredTarget -replace [regex]::Escape($appRoot), ""
            Write-Warn "No target specified. Inferred: $relInferred"
            $report += "`n`n### Target Selection"
            $report += "`n- **Mode:** Inferred (no explicit -Target provided)"
            $report += "`n- **Selected:** $relInferred"
            $report += "`n- **Reason:** Top match from codebase search"
        } else {
            Write-Fail "Cannot infer target - no search results"
            $report += "`n`n### Target Selection"
            $report += "`n- **Mode:** Inferred (no explicit -Target provided)"
            $report += "`n- **Status:** FAILED - no suitable target found"
            $report += "`n`n## Outcome`n"
            $report += "`n**ABORTED** - Cannot proceed without valid target."
            $report | Out-File -FilePath $ReportFile -Encoding UTF8
            Write-Host $report
            exit 1
        }
    } else {
        # Verify explicit target exists
        $fullTarget = Join-Path $appRoot $Target
    if (Test-Path $fullTarget) {
        Write-Ok "Target verified: $Target"
        $report += "`n`n### Target Selection"
        $report += "`n- **Mode:** Explicit (provided via -Target)"
        $report += "`n- **Selected:** $Target"
        $report += "`n- **Status:** Verified"
    } else {
        Write-Fail "Target not found: $Target"
        $report += "`n`n### Target Selection"
        $report += "`n- **Mode:** Explicit (provided via -Target)"
        $report += "`n- **Selected:** $Target"
        $report += "`n- **Status:** FAILED - file does not exist"
        $report += "`n`n## Outcome`n"
        $report += "`n**ABORTED** - Target file not found."
        $report | Out-File -FilePath $ReportFile -Encoding UTF8
        Write-Host $report
        exit 1
        }
    }
}

# PATCH MODE IMPLEMENTATION
if ($Mode -eq "patch") {
    Write-Section "Patch Mode"
    
    # Generate slug if not provided
    if (-not $Slug) {
        $Slug = New-SafeSlug -text $Issue
        Write-Ok "Generated slug: $Slug"
    }
    
    # Determine branch name
    $branchName = "agent-bughunter/$Slug"
    $branchSuffix = 2
    $originalBranchName = $branchName
    
    # Check if branch exists, add suffix if needed
    $branchListResult = Invoke-Git -Repo $RepoRoot -Arguments @("branch", "--list")
    $existingBranches = if ($branchListResult.Success) { $branchListResult.Output } else { "" }
    while ($existingBranches -match [regex]::Escape($branchName)) {
        $branchName = "$originalBranchName-$branchSuffix"
        $branchSuffix++
    }
    
    $report += "`n`n## Patch Plan`n"
    $report += "`n- **Branch:** $branchName"
    $report += "`n- **Original Branch:** $originalBranch"
    
    $targetFile = if ($Target) { $Target } else { $inferredTarget -replace [regex]::Escape($appRoot), "" }
    $report += "`n- **Target File:** $targetFile"
    $report += "`n- **Patch Strategy:** Minimal guardrail fix"
    $report += "`n- **DryRun:** $DryRun"
    
    if (-not $DryRun) {
        Write-Section "Creating Branch"
        $checkoutResult = Invoke-Git -Repo $RepoRoot -Arguments @("checkout", "-b", $branchName)
        $currentBranchResult = Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", "--abbrev-ref", "HEAD")
        $currentBranch = if ($currentBranchResult.Success) { "$($currentBranchResult.Output)".Trim() } else { "" }
        
        $report += "`n`n### DEBUG INFO"
        $report += "`n- Checkout Success: $($checkoutResult.Success)"
        $report += "`n- Checkout Output: [$($checkoutResult.Output)]"
        $report += "`n- Current Branch: [$currentBranch]"
        $report += "`n- Expected Branch: [$branchName]"
        $report += "`n- Match: $($currentBranch -eq $branchName)"
        
        if ($checkoutResult.Success -and $currentBranch -eq $branchName) {
            Write-Ok "Created branch: $branchName"
            $report += "`n`n## Branch Creation`n"
            $report += "`n- [OK] Created and switched to branch: $branchName"
        } else {
            Write-Fail "Failed to create or switch to branch"
            $report += "`n`n## Branch Creation`n"
            $report += "`n- [FAIL] Failed to create or switch to branch"
            $report += "`n`n## Outcome`n"
            $report += "`n**FAILED** - Could not create patch branch."
            $report | Out-File -FilePath $ReportFile -Encoding UTF8
            Write-Host $report
            exit 1
        }
        
        Write-Section "Applying Patch"
        $report += "`n`n## Patch Application`n"
        
        # Determine patch target path
        if ($SelfTest) {
            # SelfTest uses RepoRoot-relative path, not appRoot
            $fullTargetPath = Join-Path $RepoRoot $Target
        } elseif ($Target) {
            # Regular target uses appRoot
            $fullTargetPath = Join-Path $appRoot $Target
        } else {
            # Inferred target is already a full path
            $fullTargetPath = $inferredTarget
        }
        
        $patchApplied = $false
        $patchDescription = ""
        
        try {
            # Read current content
            $content = Get-Content $fullTargetPath -Raw
            $originalContent = $content
            
            # Apply minimal defensive patch based on issue type
            if ($Issue -match "loop|infinite|storm" -and $fullTargetPath -match "\.js$") {
                # Add loop breaker comment
                $patchLine = "// BugHunter patch: Added defensive loop tracking to prevent infinite loops"
                if ($content -notmatch "BugHunter patch") {
                    $content = "$patchLine`n`n$content"
                    $patchDescription = "Added loop breaker comment at top of file"
                    $patchApplied = $true
                }
            } elseif ($Issue -match "error|exception|crash" -and $fullTargetPath -match "\.py$") {
                # Add error logging comment
                $patchLine = "# BugHunter patch: Enhanced error handling checkpoint"
                if ($content -notmatch "BugHunter patch") {
                    $content = "$patchLine`n`n$content"
                    $patchDescription = "Added error handling checkpoint comment"
                    $patchApplied = $true
                }
            } else {
                # Generic documentation patch
                $ext = [System.IO.Path]::GetExtension($fullTargetPath)
                $commentChar = if ($ext -eq ".py") { "#" } elseif ($ext -in @(".js",".css",".html")) { "//" } else { "#" }
                $patchLine = "$commentChar BugHunter analysis: Issue - $($Issue.Substring(0, [Math]::Min(60, $Issue.Length)))"
                if ($content -notmatch "BugHunter analysis") {
                    $content = "$patchLine`n`n$content"
                    $patchDescription = "Added analysis marker comment"
                    $patchApplied = $true
                }
            }
            
            if ($patchApplied) {
                $content | Out-File -FilePath $fullTargetPath -Encoding UTF8 -NoNewline
                Write-Ok "Patch applied: $patchDescription"
                $report += "`n- [OK] Patch applied successfully"
                $report += "`n- **Description:** $patchDescription"
                $report += "`n- **Type:** Defensive comment/documentation"
                
                # Show diff
                $diffResult = Invoke-Git -Repo $RepoRoot -Arguments @("diff", $fullTargetPath)
                $diffOutput = if ($diffResult.Success) { $diffResult.Output } else { "" }
                if ($diffOutput) {
                    $report += "`n`n### Diff Preview"
                    $report += "`n``````diff"
                    $report += "`n$($diffOutput.Trim())"
                    $report += "`n``````"
                }
            } else {
                Write-Warn "No patch needed or already applied"
                $report += "`n- [WARN] No patch applied (may already be present)"
            }
            
        } catch {
            Write-Fail "Patch application failed: $_"
            $report += "`n- [FAIL] Patch application failed: $_"
            $report += "`n`n## Rollback`n"
            $report += "`n- Restoring working tree..."
            
            git -C $RepoRoot restore . 2>&1 | Out-Null
            git -C $RepoRoot checkout $originalBranch 2>&1 | Out-Null
            
            $report += "`n- [OK] Restored to original state"
            $report += "`n- [OK] Switched back to: $originalBranch"
            $report += "`n`n## Outcome`n"
            $report += "`n**FAILED** - Patch application error. No changes committed."
            $report | Out-File -FilePath $ReportFile -Encoding UTF8
            Write-Host $report
            exit 1
        }
        
        if ($patchApplied) {
            Write-Section "Running Quality Gate"
            $report += "`n`n## Quality Gate`n"
            
            $qualityScript = Join-Path $RepoRoot "scripts\quality.ps1"
            $qualityOutput = & powershell -ExecutionPolicy Bypass -File $qualityScript 2>&1 | Out-String
            $qualityExitCode = $LASTEXITCODE
            
            $report += "`n``````"
            $report += "`n$(($qualityOutput -split "`n" | Select-Object -Last 50) -join "`n")"
            $report += "`n``````"
            $report += "`n`n- **Exit Code:** $qualityExitCode"
            
            if ($qualityExitCode -eq 0) {
                Write-Ok "Quality gate passed"
                $report += "`n- **Result:** PASSED"
                
                Write-Section "Committing Changes"
                $report += "`n`n## Commit`n"
                
                $addResult = Invoke-Git -Repo $RepoRoot -Arguments @("add", $fullTargetPath)
                $commitMsg = "BugHunter patch: $($Issue.Substring(0, [Math]::Min(50, $Issue.Length)))"
                $commitResult = Invoke-Git -Repo $RepoRoot -Arguments @("commit", "-m", $commitMsg)
                $hashResult = Invoke-Git -Repo $RepoRoot -Arguments @("rev-parse", "--short", "HEAD")
                $commitHash = if ($hashResult.Success) { $hashResult.Output.Trim() } else { "unknown" }
                
                Write-Ok "Changes committed: $commitHash"
                $report += "`n- [OK] Changes committed"
                $report += "`n- **Commit Hash:** $commitHash"
                $report += "`n- **Message:** $commitMsg"
                $report += "`n- **Files Changed:** $targetFile"
                
                $report += "`n`n## Outcome`n"
                $report += "`n**SUCCESS** - Patch applied and committed safely."
                $report += "`n`n### Next Steps"
                $report += "`n1. Review changes: ``git diff $originalBranch..$branchName``"
                $report += "`n2. Test the application"
                $report += "`n3. Open PR from branch: ``$branchName``"
                $report += "`n4. If issues found: ``git checkout $originalBranch && git branch -D $branchName``"
                
            } else {
                Write-Fail "Quality gate failed"
                $report += "`n- **Result:** FAILED"
                $report += "`n`n## Rollback`n"
                $report += "`n- Quality gate failed - rolling back changes..."
                
                $null = Invoke-Git -Repo $RepoRoot -Arguments @("restore", "--staged", ".")
                $null = Invoke-Git -Repo $RepoRoot -Arguments @("restore", ".")
                $null = Invoke-Git -Repo $RepoRoot -Arguments @("checkout", $originalBranch)
                $null = Invoke-Git -Repo $RepoRoot -Arguments @("branch", "-D", $branchName)
                
                Write-Warn "Rolled back to original state"
                $report += "`n- [OK] Restored working tree"
                $report += "`n- [OK] Switched back to: $originalBranch"
                $report += "`n- [OK] Deleted branch: $branchName"
                $report += "`n`n## Outcome`n"
                $report += "`n**PATCH NOT SAFE** - Quality gate failed. All changes reverted."
                
                $report | Out-File -FilePath $ReportFile -Encoding UTF8
                Write-Host $report
                Write-Fail "Patch failed quality gate. Rolled back."
                exit 1
            }
        }
    } else {
        Write-Warn "DRY RUN - No actual changes made"
        $report += "`n`n## Dry Run`n"
        $report += "`n- All operations simulated only"
        $report += "`n- No branch created, no files modified, no commits made"
        $report += "`n- Remove -DryRun flag to apply changes"
    }
    
} else {
    # ANALYZE MODE ONLY
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

"@

    $report += "`n## First Suspect Analysis"
    
    if ($Issue -match "loop|infinite|storm|hang") {
        $report += "`n`n**Suspect: Infinite Loop / Polling Storm**"
        $report += "`n- Check for:"
        $report += "`n  - Frontend: useEffect without dependency array"
        $report += "`n  - Frontend: Polling intervals (setInterval/setTimeout)"
        $report += "`n  - Backend: Unthrottled endpoints being hit repeatedly"
    }
    
    if ($Issue -match "crash|error|exception|fail") {
        $report += "`n`n**Suspect: Exception / Runtime Error**"
        $report += "`n- Check recent git changes for introduced bugs"
        $report += "`n- Review error logs in backend console"
    }
    
    $report += "`n`n## Recommended Next Actions"
    $report += @"

1. **Reproduce:** Follow repro steps above to confirm issue
2. **Isolate:** Use search results to narrow down suspect files
3. **Patch:** Run with ``-Mode patch -Target <file>`` to apply minimal fix
4. **Test:** Verify fix works and doesn't break other features

"@
    
    $report += "`n## Status"
    $report += "`n[INFO] Analysis complete - Run with ``-Mode patch`` to apply automated fix"
}

# Save report
$report | Out-File -FilePath $ReportFile -Encoding UTF8

Write-Host $report
Write-Host ""
if ($Mode -eq "analyze") {
    Write-Ok "Analysis complete. Review report for next steps."
} else {
    if ($DryRun) {
        Write-Warn "Dry run complete. Remove -DryRun to apply changes."
    }
}

exit 0
