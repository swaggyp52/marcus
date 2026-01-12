# Workspace System

The workspace system organizes course materials, projects, and agent configurations into isolated, reusable units. Each workspace is a self-contained folder with sources, indexes, and agent profiles.

## Quick Start

### 1. Create a workspace

```powershell
.\scripts\agent.ps1 workspace-new -Name ece380
```

This creates:
- `workspaces/ece380/` with sources, index, and agents folders
- Template agent profiles (Homework Coach, Exam Builder, etc.)

### 2. Add sources

Drop your materials into:
```
workspaces/ece380/sources/
```

Supported:
- PDFs (lecture notes, textbooks)
- Markdown (assignments, notes)
- Code files (examples, starter code)
- Text files (reading lists, syllabi)

### 3. Index the workspace

```powershell
.\scripts\agent.ps1 workspace-index -Workspace ece380
```

Creates an index in `workspaces/ece380/index/file_index.json` with:
- File paths and sizes
- Modified timestamps
- File previews (for text files)
- Organized by file type

### 4. Use agents with the workspace

Example: homework coach explains a concept from ece380 materials

```powershell
# (Future UI integration - for now, reference the agent profile)
# Agent profiles in workspaces/ece380/agents/ define:
# - What the agent can read (scope_paths)
# - What it's allowed to do (allowed_actions)
# - System prompt and guardrails
```

## Workspace Structure

Each workspace contains:

```
workspaces/<name>/
├── sources/           # Upload course materials here
│   ├── lectures/      # Lecture notes (PDFs, Markdown)
│   ├── assignments/   # Homework, projects, exams
│   ├── readings/      # Textbooks, papers
│   └── code/          # Examples, starter code
├── index/             # Generated indices (do not edit)
│   └── file_index.json
├── agents/            # Agent profiles (JSON configs)
│   ├── homework_coach.json
│   ├── exam_builder.json
│   └── <custom>.json
└── README.md          # Workspace description
```

## Agent Profiles

Each agent profile is a JSON file in `agents/` that defines:

```json
{
  "name": "Agent Name",
  "description": "What this agent does",
  "scope_paths": ["sources/**"],
  "allowed_actions": ["read_only"],
  "system_prompt": "Instructions for the agent",
  "user_prompt_prefix": "How to prompt this agent",
  "guardrails": ["Rules the agent must follow"]
}
```

### Allowed Actions

- `read_only` - Read workspace sources and respond with analysis/explanations
- `patch_repo` - Allowed to create branches and modify code (with quality checks)
- `generate_pr_text` - Allowed to write PR descriptions and commit messages
- `run_quality` - Allowed to run quality.ps1 checks before committing

### Examples

#### Homework Coach (read-only)
- Explains assignments and concepts from course materials
- Works through examples step-by-step
- Never gives full solutions to homework problems
- Scope: `sources/**`

#### Exam Builder (read-only)
- Generates practice questions from course materials
- Creates questions at varying difficulty levels
- Includes answer keys and explanations
- Scope: `sources/**`

#### RedByte PR Agent (patch-capable)
- Analyzes code, identifies bugs, creates fix branches
- Runs quality checks before committing
- Writes clear PR descriptions
- Scope: `**` (entire repo)
- Actions: `patch_repo`, `run_quality`, `generate_pr_text`

## Reports

All workspace operations write reports to `docs/REPORTS/`:

```
docs/REPORTS/
├── 20260112_143500-workspace-new-ece380.md
├── 20260112_143530-workspace-index-ece380.md
└── ...
```

Reports include:
- Timestamp and repo commit
- Command invocation
- Workspace name and location
- File counts, index contents
- Any warnings or errors

## Commands

### Create a workspace

```powershell
.\scripts\agent.ps1 workspace-new -Name ece380
.\scripts\agent.ps1 workspace-new -Name cyeng350 -SkipIndex  # Skip auto-indexing
.\scripts\agent.ps1 workspace-new -Name redbyte -Force       # Overwrite existing
```

### Index a workspace

```powershell
.\scripts\agent.ps1 workspace-index -Workspace ece380
```

Generates/updates the index in `workspaces/ece380/index/file_index.json`.

### List workspaces

```powershell
Get-ChildItem workspaces -Directory | Where-Object { $_.Name -ne "_template" } | ForEach-Object { Write-Host $_.Name }
```

## Best Practices

1. **Keep sources organized** - Use subfolders (lectures/, assignments/, code/)
2. **Index regularly** - After adding new materials, re-run workspace-index
3. **One workspace per context** - Separate ECE380 materials from CYENG350
4. **Profile isolation** - Agent profiles can only read what's in `scope_paths`
5. **Quality first** - Patch-capable agents always run quality checks before committing

## Future Enhancements

- Document ingest: PDF text extraction, OCR if needed
- Search: ripgrep integration + optional embeddings
- UI: Workspace selector + per-workspace chat tabs
- Archive: Export/compress workspaces for backup
- Sharing: Package workspaces for collaboration

## Troubleshooting

### Workspace already exists
```powershell
# Use -Force to overwrite
.\scripts\agent.ps1 workspace-new -Name ece380 -Force
```

### Index not updating
```powershell
# Re-run indexing to refresh
.\scripts\agent.ps1 workspace-index -Workspace ece380
```

### Sources not showing in index
```powershell
# Ensure files are in workspaces/<name>/sources/
# Re-run index if files were recently added
.\scripts\agent.ps1 workspace-index -Workspace ece380
```

### Agent can't access sources
```powershell
# Check the agent's scope_paths in its JSON profile
# Ensure scope includes the sources directory:
# "scope_paths": ["sources/**"]
```
