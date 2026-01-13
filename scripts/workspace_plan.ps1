<#
.SYNOPSIS
    Generate study plan and next actions for a workspace.

.DESCRIPTION
    Reads BRIEF, KEY_TERMS, and OPEN_QUESTIONS to produce:
    - STUDY_PLAN.md: Weekly breakdown of topics
    - NEXT_ACTIONS.md: Concrete tasks to complete

.PARAMETER Name
    The workspace name.

.EXAMPLE
    .\workspace_plan.ps1 -Name ece381
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

# Load workspace library
. (Join-Path $PSScriptRoot "_workspace_lib.ps1")

# Resolve workspace location
$repoRoot = Split-Path -Parent $PSScriptRoot
$workspaceRoot = Join-Path $repoRoot "workspaces\$Name"

if (-not (Test-Path $workspaceRoot)) {
    throw "Workspace not found: $workspaceRoot"
}

$indexDir = Join-Path $workspaceRoot "index"
$briefPath = Join-Path $indexDir "BRIEF.md"
$keyTermsPath = Join-Path $indexDir "KEY_TERMS.md"
$openQuestionsPath = Join-Path $indexDir "OPEN_QUESTIONS.md"
$sourcesIndexPath = Join-Path $indexDir "sources_index.json"

# Check if summary exists
if (-not (Test-Path $briefPath)) {
    throw "BRIEF.md not found. Run workspace-summarize first."
}

# Read existing summaries
$briefContent = if (Test-Path $briefPath) { Get-Content $briefPath -Raw } else { "" }
$keyTermsContent = if (Test-Path $keyTermsPath) { Get-Content $keyTermsPath -Raw } else { "" }
$openQuestionsContent = if (Test-Path $openQuestionsPath) { Get-Content $openQuestionsPath -Raw } else { "" }

# Count sources
$sourceCount = 0
if (Test-Path $sourcesIndexPath) {
    $indexData = Get-Content $sourcesIndexPath -Raw | ConvertFrom-Json
    $sourceCount = $indexData.Count
}

# Extract key terms count
$termsCount = 0
if ($keyTermsContent -match '- \*\*\w+\*\*') {
    $termsCount = ([regex]::Matches($keyTermsContent, '- \*\*\w+\*\*')).Count
}

# Extract open questions count
$questionsCount = 0
if ($openQuestionsContent -match '- \[ \]') {
    $questionsCount = ([regex]::Matches($openQuestionsContent, '- \[ \]')).Count
}

# Generate STUDY_PLAN.md
$studyPlanPath = Join-Path $indexDir "STUDY_PLAN.md"
$studyPlanContent = @"
# Study Plan: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Overview

- **Sources**: $sourceCount file(s)
- **Key Terms**: $termsCount term(s)
- **Open Questions**: $questionsCount question(s)

"@

if ($sourceCount -eq 0) {
    $studyPlanContent += @"
No sources available yet. Add materials first:

``````
.\scripts\agent.ps1 workspace-add -Name $Name -Paths @("path\to\file")
``````
"@
} else {
    $studyPlanContent += @"
## Week 1: Foundation

**Goals:**
- Review all source materials
- Master key terminology ($termsCount terms)
- Resolve open questions ($questionsCount items)

**Daily Breakdown:**

### Day 1-2: Initial Review
- Read all source materials completely
- Highlight unfamiliar concepts
- Note connections between topics

### Day 3-4: Terminology Mastery
- Create flashcards for key terms (see KEY_TERMS.md)
- Practice definitions out loud
- Test yourself on each term

### Day 5-6: Question Resolution
- Work through OPEN_QUESTIONS.md systematically
- Research unclear topics
- Update notes with answers

### Day 7: Integration & Practice
- Take practice quiz (see workspace-quiz)
- Review weak areas
- Summarize main concepts

## Week 2+: Advanced Practice

**Focus Areas:**
- Application problems
- Past exams/assignments
- Peer study sessions
- Office hours for remaining questions

## Study Tips

1. **Spaced Repetition**: Review KEY_TERMS.md daily for 10 minutes
2. **Active Recall**: Close materials and write what you remember
3. **Source Tracking**: Always note which file concepts come from
4. **Question Everything**: Add to OPEN_QUESTIONS.md as you study

## Progress Tracking

- [ ] All sources read completely
- [ ] All key terms memorized
- [ ] All open questions resolved
- [ ] Practice quiz completed (80%+ score)
- [ ] Self-explanation of main concepts (recorded or written)

"@
}

$studyPlanContent | Set-Content $studyPlanPath -Encoding UTF8

# Generate NEXT_ACTIONS.md
$nextActionsPath = Join-Path $indexDir "NEXT_ACTIONS.md"
$nextActionsContent = @"
# Next Actions: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

## Immediate Tasks (Do Today)

"@

if ($sourceCount -eq 0) {
    $nextActionsContent += @"
1. **Add course materials** to workspace
   ``````
   .\scripts\agent.ps1 workspace-add -Name $Name -Paths @("path\to\syllabus.pdf", "path\to\notes.txt")
   ``````

2. **Re-index workspace**
   ``````
   .\scripts\agent.ps1 workspace-index -Name $Name
   ``````

3. **Generate summary**
   ``````
   .\scripts\agent.ps1 workspace-summarize -Name $Name
   ``````
"@
} else {
    $actionNum = 1
    
    if ($termsCount -gt 0) {
        $nextActionsContent += @"
$actionNum. **Review KEY_TERMS.md** ($termsCount terms)
   - Create flashcards for unfamiliar terms
   - Look up definitions for technical vocabulary
   - _Source: index/KEY_TERMS.md_

"@
        $actionNum++
    }
    
    if ($questionsCount -gt 0) {
        $nextActionsContent += @"
$actionNum. **Address OPEN_QUESTIONS.md** ($questionsCount questions)
   - Start with the first unanswered question
   - Research using textbook/lecture notes
   - Document answers in workspace sources
   - _Source: index/OPEN_QUESTIONS.md_

"@
        $actionNum++
    }
    
    $nextActionsContent += @"
$actionNum. **Generate practice quiz**
   ``````
   .\scripts\agent.ps1 workspace-quiz -Name $Name -Count 15
   ``````
   - Take the quiz without looking at answers
   - Grade yourself honestly
   - Review incorrect answers

$($actionNum+1). **Read source materials** ($sourceCount files)
   - See index/BRIEF.md for file list
   - Take notes on key concepts
   - Add questions to OPEN_QUESTIONS.md as they arise

$($actionNum+2). **Schedule study time**
   - Block 2-hour focused session
   - Review STUDY_PLAN.md for structure
   - Track progress on checklist items

"@
}

$nextActionsContent += @"

## This Week

- Complete all immediate tasks above
- Work through at least 50% of key terms
- Resolve at least 3 open questions
- Take initial practice quiz

## Ongoing

- Add new materials as course progresses
- Re-run workspace-summarize weekly
- Update study plan based on upcoming exams/deadlines
- Review NEXT_ACTIONS.md daily

---

**Tip**: Check off completed tasks and re-run ``workspace-plan`` to get fresh recommendations.
"@

$nextActionsContent | Set-Content $nextActionsPath -Encoding UTF8

# Archive to run folder
$runMeta = Initialize-WorkspaceRun -WorkspaceRoot $workspaceRoot -Command "workspace-plan"
$archived = @(
    (Add-ToRun -FilePath $studyPlanPath -RunFolder $runMeta.RunFolder),
    (Add-ToRun -FilePath $nextActionsPath -RunFolder $runMeta.RunFolder)
) | Where-Object { $_ -ne $null }
Complete-WorkspaceRun -WorkspaceRoot $workspaceRoot -RunMetadata $runMeta -ArchivedFiles $archived

Write-Host "[OK] Workspace plan generated: $Name"
Write-Host "     - $studyPlanPath"
Write-Host "     - $nextActionsPath"
