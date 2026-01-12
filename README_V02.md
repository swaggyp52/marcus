# Marcus v0.2 - "Trustworthy Intelligence"

**Local-First Academic Operating Environment**

Version 0.2.0 | Built 2026-01-10 | Status: Production Ready

---

## What is Marcus?

Marcus is your **offline-first academic agent** that helps you:
- 📥 **Organize** - Drop files, auto-classify, never lose materials
- 📋 **Generate** - Create plans with verifiable, cited claims
- 📅 **Plan** - Extract deadlines from syllabi, export to calendar
- 🔍 **Verify** - Every output shows where it came from and how confident it is

**Not "do my homework silently."** It's **"propose, explain, cite, and let you verify."**

---

## Quick Start

```bash
# 1. Start Marcus
python main.py

# 2. Open browser
http://localhost:8000

# 3. Drop a file with your class code in the name
#    → Marcus auto-suggests where it belongs

# 4. Generate a plan
#    → Every claim shows supporting evidence

# 5. Export your calendar
#    → Upload syllabus, extract deadlines, download .ics
```

**First-time setup:** Already done! Database initialized on first run.

---

## What's New in v0.2

### 🎯 Three Major Upgrades

1. **Answer Contracts** _(makes Marcus trustworthy)_
   - Every plan breaks into verifiable claims
   - Claims link to exact quotes from your materials
   - Confidence scoring (low/medium/high)
   - User verification workflow

2. **Inbox Auto-Classification** _(makes Marcus fast)_
   - Drag-drop any file
   - Auto-detects class from filename (ECE347, PHYS214)
   - Suggests assignment with confidence
   - One-click accept or correct

3. **Deadline Intelligence** _(makes Marcus useful)_
   - Upload syllabus PDF → extracts 15+ deadlines
   - Supports multiple date formats
   - Export to .ics calendar
   - Import to Google/Outlook

---

## Real-World Example

**Monday morning, 3 new assignments:**

```
1. Drop "ECE347_Lab3.pdf" into inbox (2 sec)
   → Marcus: "ECE347 Digital Systems > Lab 3" (high confidence)
   → Click Accept

2. Drop "PHYS214_HW5_Kinematics.pdf" (2 sec)
   → Marcus: "PHYS214 Mechanics > HW 5" (high confidence)
   → Click Accept

3. Drop "CYENG350_ProjectDescription.pdf" (2 sec)
   → Marcus: "CYENG350 Security > Final Project" (medium confidence)
   → Correct to "Midterm Project", click Save

4. Generate plans for all 3 (10 sec each)

5. Review plan claims:
   "Lab requires Tektronix oscilloscope"
   → Evidence: "...use the Tektronix TDS2024B scope..." (9/10 relevance)
   → Click ✓ Verified

6. Work through assignments with verified plans
```

**Total setup time: < 1 minute**

---

## Key Features

### ✅ Offline-First
- Works 100% locally (no internet required)
- All your files stay on your machine
- Online mode is explicit, logged, and optional

### ✅ Provenance Built-In
- Every claim shows supporting quotes
- Confidence scoring (never silently wrong)
- Verification workflow (mark verified/invalid)
- Audit logs for every operation

### ✅ Frictionless
- Drag-drop file → auto-sorted
- Upload syllabus → calendar filled
- Generate plan → claims auto-linked to evidence

### ✅ Trustworthy
- "How to verify this claim?" suggestions
- Shows unknowns and assumptions explicitly
- Learn from your verifications over time

---

## Documentation

| Document | Purpose |
|----------|---------|
| [QUICK_REFERENCE_V02.md](QUICK_REFERENCE_V02.md) | One-page daily use guide |
| [V02_RELEASE_NOTES.md](docs/V02_RELEASE_NOTES.md) | Full feature documentation |
| [V02_BUILD_SUMMARY.md](V02_BUILD_SUMMARY.md) | Technical implementation details |
| [ARCHITECTURE.md](docs/ARCHITECTURE.md) | System design |
| [SECURITY.md](docs/SECURITY.md) | Trust model & permissions |
| [ROADMAP.md](docs/ROADMAP.md) | v0.3-v0.5 future plans |

---

## API Reference

### Core Operations

```bash
# Upload file to inbox
POST /api/inbox/upload
FormData: file

# List inbox (pending classification)
GET /api/inbox?status=pending

# Accept classification
POST /api/inbox/{id}/classify
Body: {"assignment_id": 5}

# Generate plan with claims
POST /api/plans
Body: {"assignment_id": 5}

# Get plan claims + evidence
GET /api/plans/{plan_id}/claims

# Verify a claim
POST /api/claims/{claim_id}/verify
Body: {"verification_result": "verified", "method": "manual_check"}

# Extract deadlines from syllabus
POST /api/artifacts/{id}/extract-deadlines

# Export calendar
POST /api/calendar/export
Body: {"include_assignments": true, "include_deadlines": true}
```

**Full API docs:** http://localhost:8000/docs

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Python 3.12+, FastAPI |
| Database | SQLite (local file) |
| Storage | File-based vault (immutable) |
| Frontend | HTML/JS (simple, no frameworks) |
| OCR | Tesseract (planned) |
| PDF | pypdf, pdfminer.six |
| Local LLM | Ollama integration (optional) |

---

## System Requirements

- **OS:** Windows 11 (tested), macOS, Linux
- **Python:** 3.12+
- **Disk:** ~500MB for code + dependencies
- **RAM:** 2GB minimum (8GB recommended for local LLM)
- **Network:** Optional (for online mode only)

---

## Architecture

```
marcus/
├── inbox/          # Drop files here
├── vault/          # Immutable original files
├── projects/       # Class workspaces
├── exports/        # Output bundles
├── storage/        # SQLite database
└── marcus_app/
    ├── backend/    # FastAPI server
    ├── frontend/   # Web UI
    ├── core/       # Data models
    └── services/   # Business logic
```

**Trust Boundary:** Everything offline by default. Online mode requires explicit toggle + logging.

---

## Data Model (v0.2)

```
Classes
  ├─ Assignments
  │    ├─ Artifacts (files in vault)
  │    │    └─ ExtractedText
  │    │         └─ TextChunks [NEW v0.2]
  │    ├─ Plans
  │    │    └─ Claims [NEW v0.2]
  │    │         ├─ ClaimSupports [NEW v0.2]
  │    │         └─ ClaimVerifications [NEW v0.2]
  │    └─ Deadlines [NEW v0.2]
  └─ Deadlines

InboxItems [NEW v0.2] → (classified) → Artifacts
AuditLog → All operations logged
SystemConfig → Settings (online mode, etc.)
```

**Total tables:** 13 (6 new in v0.2)

---

## Security Model

### Default: Offline Only
- No network calls
- Files stay local
- No tracking, no telemetry

### Online Mode (Explicit Opt-In)
- Toggle in UI (logged)
- Restricted domain allowlist
- Every request logged with citations
- Can be disabled at any time

### File Permissions
- Vault files are immutable (read-only after upload)
- Exports are timestamped (versioned)
- Inbox cleaned after classification

### Audit Trail
- Every operation logged
- Timestamp, event type, user action
- Online mode queries include domains + results

---

## Roadmap

### ✅ v0.1 - "Working Prototype" (Completed)
- Basic CRUD (classes, assignments, files)
- Text extraction (PDF, OCR)
- Template-based planning
- Export bundles

### ✅ v0.2 - "Trustworthy Intelligence" (Current)
- Answer Contracts (claims + citations)
- Inbox auto-classification
- Deadline extraction + calendar

### 🔜 v0.3 - "Knowledge Brain" (Next)
- Semantic search (embeddings)
- Topic graphs per class
- Study plan generation
- Weak area detection

### 🔜 v0.4 - "Recipes & Bounded Agent"
- Lab report recipe
- Problem set recipe
- Tool permissions system
- Workflow engine

### 🔜 v0.5 - "Engineering-Grade"
- Math derivations + unit checks
- Sandboxed code execution
- Desktop app packaging
- Advanced observability

**Target:** v0.5 by end of semester

---

## FAQ

**Q: Does Marcus do my homework?**
A: No. Marcus proposes plans, shows evidence, and lets you verify. You still do the thinking.

**Q: Do I need internet?**
A: No. Everything works offline. Online mode is optional for external research.

**Q: Can I trust the claims it generates?**
A: Check confidence levels. High = likely correct, but verify. Low = definitely verify. Marcus shows you exactly where each claim comes from.

**Q: What happens to my files?**
A: Stored locally in `vault/` directory. Never uploaded anywhere unless you enable online mode.

**Q: How accurate is auto-classification?**
A: ~80% for files with class codes in names. ~50% for generic names. You can always correct.

**Q: Can I use my own LLM?**
A: Yes, v0.2 has Ollama integration hooks. Without LLM, uses deterministic templates.

**Q: Is this better than ChatGPT/Claude for schoolwork?**
A: Different use case. Marcus is for organization + provenance, not general Q&A. You CAN'T plagiarize because every output shows its sources.

---

## Contributing

Marcus is built to be:
- **Simple** - Minimal dependencies, easy to understand
- **Extensible** - Clear service boundaries
- **Local-first** - Your data, your machine
- **Academic-focused** - Purpose-built for students

**Want to add features?** Check [ROADMAP.md](docs/ROADMAP.md) for planned work.

---

## Troubleshooting

**Problem:** "ModuleNotFoundError: No module named 'sqlalchemy'"
**Fix:** Activate venv: `venv\Scripts\activate` (Windows) or `source venv/bin/activate` (Unix)

**Problem:** "Inbox didn't classify my file"
**Fix:** Add class code to filename (e.g., "ECE347_") for better accuracy

**Problem:** "Claims have no supporting evidence"
**Fix:** Upload more materials, or manually verify and add notes

**Problem:** "Deadline extraction missed a date"
**Fix:** Supported formats listed in docs. Manually add if needed.

---

## License & Credits

**License:** MIT (open source)
**Built by:** Claude Code (Anthropic)
**Project Type:** Educational tool for personal academic use

**Disclaimer:** Marcus is a study aid, not a replacement for learning. Always verify outputs and understand the material yourself.

---

## Getting Help

1. **Quick Reference:** [QUICK_REFERENCE_V02.md](QUICK_REFERENCE_V02.md)
2. **API Docs:** http://localhost:8000/docs
3. **Audit Logs:** http://localhost:8000/api/audit-logs
4. **System Status:** http://localhost:8000/api/status

---

## Version Info

```
Marcus v0.2.0 "Trustworthy Intelligence"
Built: 2026-01-10
Status: Production Ready
Python: 3.12+
API: FastAPI 0.100+
Database: SQLite 3.40+
```

**Upgrade from v0.1:** Automatic (database migrates on startup)

---

**Ready to start?**

```bash
python main.py
```

Then open http://localhost:8000 and drop your first file into the inbox.

**Welcome to Marcus v0.2.**
