<#
.SYNOPSIS
    Generate a practice quiz from workspace sources.

.DESCRIPTION
    Creates quiz questions from workspace content with answers in separate file.
    All questions cite source files.

.PARAMETER Name
    The workspace name.

.PARAMETER Count
    Number of questions to generate (default: 15).

.EXAMPLE
    .\workspace_quiz.ps1 -Name ece381 -Count 20
#>

[CmdletBinding()]
param(
    [Parameter(Mandatory)]
    [string]$Name,
    
    [Parameter()]
    [int]$Count = 15,

    [Parameter()]
    [string]$RunId
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
$sourcesIndexPath = Join-Path $indexDir "sources_index.json"
$keyTermsPath = Join-Path $indexDir "KEY_TERMS.md"
$openQuestionsPath = Join-Path $indexDir "OPEN_QUESTIONS.md"

if (-not (Test-Path $sourcesIndexPath)) {
    throw "Index not found. Run workspace-index first."
}

$indexData = Get-Content $sourcesIndexPath -Raw | ConvertFrom-Json

# Read text sources
$textExtensions = @('.txt', '.md', '.csv', '.json')
$sources = @()
foreach ($entry in $indexData) {
    if ($textExtensions -contains $entry.extension) {
        $filePath = Join-Path $workspaceRoot $entry.relativePath
        if (Test-Path $filePath) {
            try {
                $content = Get-Content $filePath -Raw -ErrorAction SilentlyContinue
                $sources += [PSCustomObject]@{
                    FileName = $entry.fileName
                    Content = $content
                }
            } catch {
                Write-Warning "Could not read: $($entry.fileName)"
            }
        }
    }
}

if ($sources.Count -eq 0) {
    throw "No text sources available. Add files first."
}

# Extract key terms if available
$keyTerms = @()
if (Test-Path $keyTermsPath) {
    $keyTermsContent = Get-Content $keyTermsPath -Raw
    $matches = [regex]::Matches($keyTermsContent, '- \*\*(\w+)\*\*')
    $keyTerms = $matches | ForEach-Object { $_.Groups[1].Value } | Select-Object -Unique
}

# Generate questions
$questions = @()
$questionNum = 1

# Question Type 1: Definition questions from key terms
$termQuestions = [Math]::Min($keyTerms.Count, [Math]::Ceiling($Count * 0.3))
for ($i = 0; $i -lt $termQuestions -and $i -lt $keyTerms.Count; $i++) {
    $term = $keyTerms[$i]
    $questions += [PSCustomObject]@{
        Number = $questionNum++
        Type = "Definition"
        Question = "Define: **$term**"
        Answer = "_(Student should define this term based on source materials)_"
        Source = "KEY_TERMS.md"
    }
}

# Question Type 2: Extract sentences with key concepts
$conceptQuestions = [Math]::Min($sources.Count * 2, [Math]::Ceiling($Count * 0.3))
$conceptCount = 0
foreach ($source in $sources) {
    if ($conceptCount -ge $conceptQuestions) { break }
    
    $sentences = $source.Content -split '[.!?]' | Where-Object { $_.Trim().Length -gt 20 } | Select-Object -First 3
    foreach ($sentence in $sentences) {
        if ($conceptCount -ge $conceptQuestions) { break }
        
        $cleanSentence = $sentence.Trim()
        if ($cleanSentence.Length -gt 30 -and $cleanSentence -notmatch '^\s*$') {
            $questions += [PSCustomObject]@{
                Number = $questionNum++
                Type = "Explain"
                Question = "Explain the following concept: `"$cleanSentence`""
                Answer = "_(Refer to $($source.FileName) for full context and explanation)_"
                Source = $source.FileName
            }
            $conceptCount++
        }
    }
}

# Question Type 3: Application questions from open questions
if (Test-Path $openQuestionsPath) {
    $openQuestionsContent = Get-Content $openQuestionsPath -Raw
    $qMatches = [regex]::Matches($openQuestionsContent, '- \[ \] (.+?) _\((.+?)\)_')
    
    $appQuestions = [Math]::Min($qMatches.Count, [Math]::Ceiling($Count * 0.2))
    for ($i = 0; $i -lt $appQuestions; $i++) {
        $qText = $qMatches[$i].Groups[1].Value.Trim()
        $qSource = $qMatches[$i].Groups[2].Value.Split(':')[0]
        
        $questions += [PSCustomObject]@{
            Number = $questionNum++
            Type = "Application"
            Question = $qText
            Answer = "_(Work through this problem using concepts from $qSource)_"
            Source = $qSource
        }
    }
}

# Question Type 4: Fill remaining with "True/False" or "Identify the mistake"
$remaining = $Count - $questions.Count
for ($i = 0; $i -lt $remaining -and $i -lt $sources.Count; $i++) {
    $source = $sources[$i % $sources.Count]
    $questions += [PSCustomObject]@{
        Number = $questionNum++
        Type = "Analysis"
        Question = "Based on $($source.FileName), identify one key concept and explain its importance."
        Answer = "_(Student should select and explain a concept from the source)_"
        Source = $source.FileName
    }
}

# Trim to requested count
$questions = $questions | Select-Object -First $Count

# Generate QUIZ_01.md
$quizPath = Join-Path $indexDir "QUIZ_01.md"
$quizContent = @"
# Practice Quiz: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")
Questions: $Count

---

**Instructions:**
- Answer all questions in your own words
- Refer to source files as needed
- Time yourself (suggested: 2-3 minutes per question)
- Check your answers against QUIZ_01_ANSWERS.md when complete

---

"@

foreach ($q in $questions) {
    $quizContent += @"
## Question $($q.Number) [$($q.Type)]

$($q.Question)

_Source: $($q.Source)_

---

"@
}

$quizContent += @"

## Submission

- **Score**: ___ / $Count
- **Time taken**: _____ minutes
- **Confidence level**: Low / Medium / High
- **Topics to review**: _________________________________

"@

$quizContent | Set-Content $quizPath -Encoding UTF8

# Generate QUIZ_01_ANSWERS.md
$answersPath = Join-Path $indexDir "QUIZ_01_ANSWERS.md"
$answersContent = @"
# Quiz Answers: $Name

Generated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

---

**Note:** These are guidance answers. Your answers should be in your own words and demonstrate understanding.

---

"@

foreach ($q in $questions) {
    $answersContent += @"
## Question $($q.Number) [$($q.Type)]

**Question:** $($q.Question)

**Answer:** $($q.Answer)

**Source:** $($q.Source)

---

"@
}

$answersContent | Set-Content $answersPath -Encoding UTF8

# Archive to run folder
$runMeta = Initialize-WorkspaceRun -WorkspaceRoot $workspaceRoot -Command "workspace-quiz" -RunId $RunId
$archived = @(
    (Add-ToRun -FilePath $quizPath -RunFolder $runMeta.RunFolder),
    (Add-ToRun -FilePath $answersPath -RunFolder $runMeta.RunFolder)
) | Where-Object { $_ -ne $null }
Complete-WorkspaceRun -WorkspaceRoot $workspaceRoot -RunMetadata $runMeta -ArchivedFiles $archived

Write-Host "[OK] Quiz generated: $Name ($Count questions)"
Write-Host "     - $quizPath"
Write-Host "     - $answersPath"
