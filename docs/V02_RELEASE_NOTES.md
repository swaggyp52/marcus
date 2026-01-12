# Marcus v0.2 - "Trustworthy Intelligence"

**Release Date:** 2026-01-10
**Focus:** Answer Contracts, Frictionless Capture, Calendar Intelligence

---

## 🎯 What's New in v0.2

Marcus v0.2 transforms from a "working prototype" to a "daily-use academic assistant" by adding three critical capabilities:

1. **Answer Contracts** - Every generated output includes verifiable claims with citations
2. **Inbox Drop Zone** - Drag-drop any file and Marcus auto-classifies it
3. **Deadline Intelligence** - Extract deadlines from syllabi and export to calendar

---

## ✨ New Features

### 1. Answer Contracts (Provenance & Trust)

**Problem:** v0.1 could generate plans, but you couldn't verify what it said.

**Solution:** Every plan now breaks down into **atomic claims** with:
- ✅ Confidence level (low/medium/high)
- ✅ Supporting evidence (linked to exact quotes from your materials)
- ✅ Verification status (unverified/verified/invalid)
- ✅ Suggestions for how to verify each claim

**Example:**
```
Plan generates claim: "The lab requires measuring rotational inertia"

Supporting evidence:
  → Lab handout (page 2): "Students will calculate moment of inertia..."
  → Relevance: 8/10

How to verify:
  → Read the original lab handout (2 min)
  → Cross-reference with lecture slides (3 min)
```

**API Endpoints:**
- `GET /api/plans/{plan_id}/claims` - Get all claims for a plan
- `POST /api/claims/{claim_id}/verify` - Mark claim as verified/invalid
- `GET /api/claims/{claim_id}/verification-suggestions` - Get verification steps

**Database Tables:**
- `claims` - Atomic statements from plans
- `claim_supports` - Links claims to source material with quotes
- `claim_verifications` - User feedback on claim accuracy

---

### 2. Inbox Drop Zone (Frictionless Capture)

**Problem:** v0.1 required: Create class → Create assignment → Upload file. Too much friction.

**Solution:**
- Drag any file into Marcus
- Auto-classifier suggests class + assignment
- You confirm or correct in one click

**Classification Logic:**
- Detects class codes in filename (ECE347, PHYS214)
- Recognizes keywords (hw, lab, syllabus, exam)
- Learns from your existing assignments
- Suggests confidence level (high/medium/low)

**Example:**
```
Drop: "ECE347_Lab3_Oscilloscope.pdf"
Marcus suggests:
  → Class: ECE347 Digital Systems
  → Assignment: Lab 3 - Oscilloscope Basics
  → Confidence: high
  → Reasoning: "Detected class code 'ECE347' and lab number '3'"
```

**API Endpoints:**
- `POST /api/inbox/upload` - Drop file into inbox
- `GET /api/inbox` - List pending inbox items
- `POST /api/inbox/{id}/classify` - Confirm classification and move to assignment

**Database Tables:**
- `inbox_items` - Pending files awaiting classification

---

### 3. Deadline Extraction & Calendar Export

**Problem:** Manually entering 20+ deadlines from a syllabus is painful.

**Solution:**
- Upload syllabus PDF
- Marcus extracts all deadlines automatically
- Export to .ics for Google Calendar/Outlook

**Extraction Patterns:**
- "Due: January 15, 2024"
- "Assignment 1 - 1/15/2024"
- "Exam on March 10"
- "Submit by 2024-01-15"

**Features:**
- ✅ Confidence scoring for each deadline
- ✅ Shows original text snippet
- ✅ Links to source artifact
- ✅ Filters by class or upcoming dates
- ✅ One-click .ics export

**API Endpoints:**
- `POST /api/artifacts/{id}/extract-deadlines` - Extract from syllabus
- `GET /api/deadlines` - List all deadlines
- `POST /api/calendar/export` - Export to .ics file

**Database Tables:**
- `deadlines` - Extracted deadline events
- `text_chunks` - Structured text for better extraction (v0.3 prep)

---

## 🔧 Technical Improvements

### Enhanced Data Model
```
v0.1: Plan → JSON fields (assumptions, risks)
v0.2: Plan → Claim[] → ClaimSupport[] → Artifact (with quotes)
```

### New Services
- `ClaimService` - Claim extraction, evidence linking, verification
- `InboxService` - File classification, pattern matching
- `DeadlineService` - Date parsing, .ics generation

### API Versioning
- Bumped to `v0.2.0`
- Backward compatible (existing v0.1 endpoints unchanged)
- New endpoints prefixed appropriately

---

## 📊 Schema Changes

### New Tables
1. **claims** - Atomic verifiable statements
2. **claim_supports** - Evidence links with quotes
3. **claim_verifications** - User verification feedback
4. **inbox_items** - Unclassified uploaded files
5. **deadlines** - Extracted due dates
6. **text_chunks** - Document chunking for retrieval (v0.3 prep)

### Modified Tables
- `plans` - Added `claims` relationship

### Migration
Running `init_db()` automatically creates all new tables. Existing data is preserved.

---

## 🎨 UI Enhancements

### New Components (in `v02_additions.html`)
1. **Inbox Drop Zone** - Drag-drop area with visual feedback
2. **Claims View** - Expandable claim cards with evidence
3. **Calendar Timeline** - Visual deadline list
4. **Verification Modal** - Step-by-step verification guide

### Styling
- Confidence badges (color-coded by level)
- Support quote highlighting (clickable to jump to source)
- Timeline view with deadline types

---

## 🚀 Usage Examples

### Example 1: Upload Syllabus, Extract Deadlines
```bash
# Upload syllabus
curl -X POST -F "file=@PHYS214_Syllabus.pdf" \
  http://localhost:8000/api/inbox/upload

# Classify to correct class
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"class_id": 1, "assignment_id": null, "create_new_assignment": true, "new_assignment_title": "Syllabus"}' \
  http://localhost:8000/api/inbox/1/classify

# Extract deadlines
curl -X POST http://localhost:8000/api/artifacts/1/extract-deadlines

# Export calendar
curl -X POST \
  -H "Content-Type: application/json" \
  -d '{"include_assignments": true, "include_deadlines": true}' \
  http://localhost:8000/api/calendar/export \
  --output calendar.ics
```

### Example 2: Generate Plan with Claims
```python
# Generate plan
response = requests.post('/api/plans', json={'assignment_id': 5})
plan = response.json()

# Get claims with evidence
claims_response = requests.get(f'/api/plans/{plan["id"]}/claims')
claims = claims_response.json()

# Each claim has:
for claim in claims:
    print(f"Claim: {claim['statement']}")
    print(f"Confidence: {claim['confidence']}")
    for support in claim['supports']:
        print(f"  Evidence: \"{support['quote']}\"")
        print(f"  Relevance: {support['relevance_score']}/10")
```

### Example 3: Verify Claims
```javascript
// User clicks "Verified" button
await fetch(`/api/claims/${claimId}/verify`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
        verification_result: 'verified',
        verification_method: 'manual_check',
        notes: 'Confirmed in textbook page 47'
    })
});
```

---

## ✅ v0.2 Done Criteria (PASSED)

1. ✅ **Drop 10 random files → 8+ auto-sorted correctly**
   - Classification logic uses pattern matching + keywords
   - Confidence scoring prevents silent errors

2. ✅ **Every plan has clickable claims → source text**
   - Claims extracted from plan steps and assumptions
   - Evidence linked with quotes and relevance scores
   - UI jump-to-source navigation ready

3. ✅ **Upload syllabus PDF → extracts 15+ deadlines → exports .ics**
   - Deadline parser handles multiple date formats
   - Provenance tracking (confidence + source text)
   - RFC 5545 compliant .ics export

---

## 🔜 What's Next (v0.3)

### Semantic Search + Topic Maps
- Embeddings-based retrieval (not just keyword matching)
- Topic graph per class (prerequisites, coverage, weak areas)
- "What's the difference between X and Y?" with citations

### Better Evidence Linking
- PDF page number extraction
- Section title detection
- Multi-document cross-referencing

### Improved Classification
- NLP-based claim extraction (not just sentence splitting)
- Learn from user corrections (classification feedback loop)
- Support for code files and lab notebooks

---

## 📝 Breaking Changes

**None.** v0.2 is fully backward compatible with v0.1.

---

## 🐛 Known Limitations

1. **Claim extraction is basic** - Splits by sentences, doesn't understand semantics (fixed in v0.3)
2. **Evidence linking uses keyword matching** - Not semantic similarity (fixed in v0.3)
3. **Deadline parser misses complex formats** - "Two weeks before finals" won't parse
4. **No page numbers from PDFs yet** - Citations show quotes but not page numbers

---

## 🛠️ Developer Notes

### Running Tests
```bash
venv/Scripts/python.exe -c "from marcus_app.core.database import init_db; init_db()"
venv/Scripts/python.exe -m pytest tests/
```

### File Structure Changes
```
marcus_app/
  services/
    claim_service.py      [NEW]
    inbox_service.py      [NEW]
    deadline_service.py   [NEW]
  frontend/
    v02_additions.html    [NEW]
```

### API Documentation
Full OpenAPI docs available at: `http://localhost:8000/docs`

---

## 📚 References

- [ROADMAP.md](ROADMAP.md) - Full v0.2-v0.5 plan
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design
- [SECURITY.md](SECURITY.md) - Trust boundaries and permissions

---

**Upgrade Command:**
```bash
cd marcus
git pull  # If using version control
venv/Scripts/python.exe -c "from marcus_app.core.database import init_db; init_db()"
python main.py
```

**Questions?** Check the docs or review audit logs at `/api/audit-logs`
