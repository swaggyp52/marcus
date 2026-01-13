# Workspace Phase E: File Ingest + Enhanced Index + Search

Phase E adds the ability to add files to workspaces, index them with rich metadata, and search across files.

## Commands

### workspace-add
Add files to a workspace's sources folder.

**Usage:**
```powershell
# Single file
.\scripts\agent.ps1 workspace-add -Name ece381 -Path "C:\notes\lecture.pdf"

# Multiple files
.\scripts\agent.ps1 workspace-add -Name ece381 -Paths @("C:\notes\a.pdf", "C:\notes\b.docx")
```

**Behavior:**
- Copies files into `workspaces\<Name>\sources\`
- Creates sources directory if missing
- Handles filename collisions by appending `_(1)`, `_(2)`, etc.
- Does NOT move files, only copies

**Output:**
```
[OK] Added 2 files to ece381
```

---

### workspace-index
Index all files in a workspace with enhanced metadata.

**Usage:**
```powershell
.\scripts\agent.ps1 workspace-index -Name ece381
```

**Behavior:**
- Scans `workspaces\<Name>\sources\` recursively
- Computes SHA256 hash for each file
- Outputs JSON to `workspaces\<Name>\index\sources_index.json`
- Empty sources produces `[]`

**Index Schema:**
```json
[
  {
    "relativePath": "sources\\note1.txt",
    "fileName": "note1.txt",
    "extension": ".txt",
    "bytes": 1234,
    "lastWriteTimeUtc": "2026-01-12T19:30:00.000Z",
    "sha256": "ABC123..."
  }
]
```

**Output:**
```
[OK] Wrote index: C:\Users\...\workspaces\ece381\index\sources_index.json
```

---

### workspace-search
Search workspace files by name and content.

**Usage:**
```powershell
.\scripts\agent.ps1 workspace-search -Name ece381 -Query "midterm"
```

**Behavior:**
- Searches all filenames (always)
- Searches file content for text files: `.txt`, `.md`, `.csv`, `.json`
- Caps file reads at 200KB for performance
- Returns scored results with snippets

**Output:**
```
Score File       Snippet
----- ----       -------
   15 note1.txt  ...hello midterm schedule...
    5 notes.md   ...exam midterm...
```

**Scoring:**
- Filename match: +10 points
- Content match: +5 points
- Results sorted by score descending

---

## Typical Workflow

```powershell
# 1. Create workspace
.\scripts\agent.ps1 workspace-new -Name ece381 -Force

# 2. Add course materials
.\scripts\agent.ps1 workspace-add -Name ece381 -Paths @(
  "C:\courses\ece381\syllabus.pdf",
  "C:\courses\ece381\lecture01.pdf",
  "C:\courses\ece381\notes.txt"
)

# 3. Index files
.\scripts\agent.ps1 workspace-index -Name ece381

# 4. Search
.\scripts\agent.ps1 workspace-search -Name ece381 -Query "final exam"
```

---

## Troubleshooting

### "Workspace not found"
- Run `workspace-new -Name <name>` first
- Verify workspace exists at `workspaces\<name>\`

### "Index not found" (during search)
- Run `workspace-index -Name <name>` first
- Verify index exists at `workspaces\<name>\index\sources_index.json`

### Search returns no results
- Check that query matches filename or content
- Verify files are text-searchable (`.txt`, `.md`, `.csv`, `.json`)
- Binary files (PDF, DOCX) are NOT content-searchable in Phase E

### Filename collision warnings
- Files are auto-renamed with `_(1)` suffix
- Original file is NOT overwritten
- Use unique filenames to avoid confusion

---

## Next Steps

Phase E provides the foundation for:
- **Phase F**: LLM-based workspace analysis and Q&A
- **Phase G**: Advanced parsing (PDF text extraction)
- **Phase H**: Integration with Marcus chat interface

For now, workspace search gives you fast lookups across course materials, notes, and documentation without leaving the terminal.
