# Marcus v0.2 - Quick Reference Card

**One-page guide for daily use**

---

## 🚀 Starting Marcus

```bash
cd marcus
python main.py
# Opens browser → http://localhost:8000
```

---

## 📥 Inbox Workflow (NEW in v0.2)

### Drop Files Fast
1. **Drag file** into the purple "Inbox" drop zone
2. **Marcus suggests** class + assignment (with confidence)
3. **Click "Accept"** or correct if needed
4. **Done** - File is now attached to assignment

### File Naming Tips for Better Auto-Classification
```
Good: "ECE347_Lab2_Oscilloscope.pdf"       → Detects class, lab number
Good: "PHYS214_HW5_Kinematics.pdf"         → Detects class, homework
Good: "CYENG350_Syllabus_Spring2024.pdf"   → Detects class, type

Okay: "Lab2.pdf"                           → Suggests most recent class
Okay: "Homework_Due_Friday.pdf"            → Guesses based on keywords
```

---

## 📋 Plan Generation with Claims (NEW in v0.2)

### Generate a Trustworthy Plan
1. **Upload materials** to assignment (or via inbox)
2. **Click "Generate Plan"**
3. **Review claims section:**
   - Each claim shows confidence (🟢 high, 🟡 medium, 🔴 low)
   - Click claim → See supporting quotes
   - Click "How to verify?" → Get steps

### Verify Claims
- **✓ Verified** - You confirmed it's correct
- **✗ Invalid** - You found it's wrong
- **Uncertain** - Need more investigation

**Why verify?** Future plans learn from your feedback.

---

## 📅 Calendar & Deadlines (NEW in v0.2)

### Extract Deadlines from Syllabus
1. **Upload syllabus** PDF to class
2. **Click "Extract Deadlines"**
3. **Review extracted dates** (confidence shown)
4. **Correct any mistakes**
5. **Click "Export Calendar"** → Download .ics
6. **Import to Google/Outlook** calendar

### Supported Date Formats
```
✅ "Due: January 15, 2024"
✅ "Assignment 1 - 1/15/2024"
✅ "Exam on 2024-01-15"
✅ "Submit by March 10th"
```

---

## 🎯 Typical Daily Workflow

### Monday Morning: New Week Setup
```
1. Drop this week's assignment PDFs into inbox (5 sec each)
2. Accept auto-classification suggestions
3. Generate plans for 2-3 assignments
4. Review claims and mark high-confidence ones as verified
```

### During Assignment Work
```
1. Open assignment in Marcus
2. Read the plan
3. Click claims to see supporting quotes from materials
4. Work through steps
5. Export final deliverable
```

### End of Semester
```
1. Review audit logs (what worked, what didn't)
2. Check claim verification stats (accuracy tracking)
3. Export all assignments
4. Archive class
```

---

## 🔍 Finding Things

### View All Deadlines
- **Navigate to:** Calendar section
- **Filter by:** Class, upcoming only
- **Sort by:** Due date

### Search Claims
- **Go to:** Assignment → Plan → Claims tab
- **Filter by:** Confidence, verification status
- **Jump to source:** Click supporting evidence quote

### Check Inbox
- **Pending items:** Shows unclassified files
- **Classified items:** Shows recent auto-sorts
- **Stats:** Classification confidence over time

---

## 📊 Understanding Confidence Levels

### Classification Confidence
| Level | Meaning | Action |
|-------|---------|--------|
| 🟢 High | Pattern matched class code + keywords | Accept confidently |
| 🟡 Medium | Found keywords or recent class | Review suggestion |
| 🔴 Low | Guessed based on recency | Probably need to correct |

### Claim Confidence
| Level | Meaning | Evidence |
|-------|---------|----------|
| 🟢 High | 3+ supporting quotes, 8+ relevance | Trust, but verify important ones |
| 🟡 Medium | 1-2 quotes, 5-7 relevance | Verify before relying on it |
| 🔴 Low | Assumption, no direct evidence | Always verify |

### Deadline Confidence
| Level | Meaning | Indicator |
|-------|---------|-----------|
| 🟢 High | Found "Due:" or "Deadline:" keyword | Accurate date |
| 🟡 Medium | Date near assignment mention | Probably correct |
| 🔴 Low | Date only, no context | Double-check |

---

## 🛠️ Common Tasks

### Create New Class
```
POST /api/classes
{
  "code": "ECE347",
  "name": "Digital Systems Design"
}
```

### Create New Assignment
```
POST /api/assignments
{
  "class_id": 1,
  "title": "Lab 3 - Oscilloscope Basics",
  "due_date": "2024-01-20T23:59:00"
}
```

### Generate Plan with Claims
```
POST /api/plans
{
  "assignment_id": 5,
  "use_online_mode": false
}

GET /api/plans/{plan_id}/claims
→ Returns claims with supporting evidence
```

### Verify a Claim
```
POST /api/claims/{claim_id}/verify
{
  "verification_result": "verified",
  "verification_method": "manual_check",
  "notes": "Confirmed in textbook section 4.2"
}
```

### Export Calendar
```
POST /api/calendar/export
{
  "class_id": 1,              # Optional: null = all classes
  "include_assignments": true,
  "include_deadlines": true
}
→ Downloads marcus_calendar_TIMESTAMP.ics
```

---

## 🚨 Troubleshooting

### "Inbox didn't auto-classify correctly"
- **Fix:** Click the item, select correct class/assignment manually
- **Learn:** Marcus learns from your corrections over time
- **Tip:** Use consistent file naming patterns

### "Claim has no supporting evidence"
- **Why:** Extracted text doesn't contain keywords from claim
- **Fix:** Upload more materials or manually add notes
- **Confidence:** Will show as 🔴 low

### "Deadline extraction missed dates"
- **Why:** Date format not recognized
- **Fix:** Manually add deadline via assignments
- **Report:** File an issue with example text

### "How do I delete a bad claim?"
- **Option 1:** Mark as ✗ Invalid (keeps for learning)
- **Option 2:** Regenerate plan (new claims extracted)

---

## 🎓 Best Practices

### File Organization
```
✅ Name files with class code
✅ Include assignment number/type
✅ Use consistent date formats
✅ Drop into inbox immediately after receiving
```

### Verification Strategy
```
✅ Verify ALL low-confidence claims
✅ Verify CRITICAL high-confidence claims
✅ Skip obvious/trivial medium claims
✅ Add notes when you verify
```

### Deadline Management
```
✅ Extract from syllabus on day 1
✅ Cross-check with online course portal
✅ Set reminders for 🔴 low-confidence deadlines
✅ Re-export .ics if dates change
```

---

## 📞 Getting Help

### Built-in Help
- **API Docs:** http://localhost:8000/docs
- **Audit Logs:** http://localhost:8000/api/audit-logs
- **System Status:** http://localhost:8000/api/status

### Documentation
- [V02_RELEASE_NOTES.md](docs/V02_RELEASE_NOTES.md) - Full feature list
- [ARCHITECTURE.md](docs/ARCHITECTURE.md) - System design
- [SECURITY.md](docs/SECURITY.md) - Trust model

### Debug Mode
```bash
# Check database
venv/Scripts/python.exe -c "from marcus_app.core.database import init_db; init_db()"

# View recent logs
curl http://localhost:8000/api/audit-logs?limit=20
```

---

## 📈 Power User Tips

### Keyboard Shortcuts (if implemented in UI)
- `Ctrl+U` - Upload to inbox
- `Ctrl+P` - Generate plan
- `Ctrl+E` - Export assignment

### Bulk Operations
```python
# Upload multiple files
import requests
for file in ["hw1.pdf", "hw2.pdf", "hw3.pdf"]:
    with open(file, 'rb') as f:
        requests.post('http://localhost:8000/api/inbox/upload',
                      files={'file': f})
```

### Custom Workflows
```javascript
// Auto-accept high-confidence classifications
const inbox = await fetch('/api/inbox?status=pending');
const items = await inbox.json();

for (const item of items) {
    if (item.classification_confidence === 'high') {
        await fetch(`/api/inbox/${item.id}/classify`, {
            method: 'POST',
            body: JSON.stringify({
                assignment_id: item.suggested_assignment_id
            })
        });
    }
}
```

---

## 🎯 Remember

**Marcus v0.2 Philosophy:**
1. **Offline first** - Online mode is explicit and logged
2. **Provenance always** - Every output shows where it came from
3. **Human in the loop** - Marcus proposes, you verify
4. **Trust through transparency** - Confidence levels, not silent certainty

**When in doubt:**
- ✅ Check confidence level
- ✅ Read supporting evidence
- ✅ Verify critical claims
- ✅ Review audit logs

---

**Quick Start Command:**
```bash
python main.py && open http://localhost:8000
```

**v0.2 Motto:** _"Drop, Review, Verify, Trust."_
