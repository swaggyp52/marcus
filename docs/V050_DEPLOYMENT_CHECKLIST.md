# V0.50 Deployment Checklist

**Version:** 0.50  
**Status:** Launch Pack  
**Date:** January 11, 2026  

---

## Pre-Deployment (2 hours before)

### Code Quality
- [ ] Run `python scripts/verify_v050.py` → all sections passing
- [ ] Run `python -m pytest tests/test_v050_intake.py -v` → all tests passing
- [ ] Run `python -m pytest tests/test_v049*.py -v` → no regressions
- [ ] Review any new files for typos, syntax errors
- [ ] Check git status: no uncommitted changes

### Environment Setup
- [ ] Python 3.8+ installed
- [ ] `pip install -r requirements.txt` successful
- [ ] Flask app starts: `python main.py`
- [ ] http://localhost:5000 loads without errors

### Storage & Security
- [ ] VeraCrypt container mounted
- [ ] Storage path writable (check Diagnostics)
- [ ] Database backup taken
- [ ] No secrets in code (API keys, passwords)

---

## Deployment (on production server)

### Code Deployment
- [ ] Pull latest code: `git pull origin main`
- [ ] No conflicts or merge issues
- [ ] `pip install -r requirements.txt` (if new deps)
- [ ] All 8 new v0.50 files present:
  - [ ] `marcus_app/services/intake_service.py`
  - [ ] `marcus_app/services/ollama_adapter.py`
  - [ ] `marcus_app/services/runbook_service.py`
  - [ ] `marcus_app/frontend/intake.js`
  - [ ] `marcus_app/frontend/intake.css`
  - [ ] `marcus_app/backend/intake_routes.py`
  - [ ] `tests/test_v050_intake.py`
  - [ ] `scripts/verify_v050.py`

### Service Startup
- [ ] Stop current Marcus instance
- [ ] Clear any old cache/temp files
- [ ] Start Marcus: `python main.py`
- [ ] Wait for startup message: "Marcus running on http://localhost:5000"
- [ ] Check logs for errors

### Smoke Tests
- [ ] Open http://localhost:5000
- [ ] Land in Agent Chat (v0.49 still working)
- [ ] Click 📚 Intake tab (new tab visible)
- [ ] Intake tab loads without JS errors (check browser console)
- [ ] Click 📊 Diagnostics (if added)
- [ ] Diagnostics show Storage/DB/LLM status

### First Intake Operation
- [ ] Create test syllabus (or use existing PDF)
- [ ] Upload to Intake wizard
- [ ] Click "Process"
- [ ] Verify classification appears
- [ ] Confirm class code/name
- [ ] Click "Confirm & Create"
- [ ] Wait for receipt
- [ ] Verify "Intake complete" message
- [ ] Check that new class appears in Inbox/Context list

### Verify Intake Receipt
- [ ] Receipt shows correct format
- [ ] Receipt ID present
- [ ] Files processed count correct
- [ ] Classes created count correct
- [ ] No unexpected errors

### Check Runbook
- [ ] Intake → Runbook loads
- [ ] All 6 sections present (First Run, Backup, Update, etc.)
- [ ] Markdown renders correctly
- [ ] Links work

### Verify Agent Chat Commands
- [ ] Type "What's next?" → shows items
- [ ] Type "Show inbox" → shows inbox items
- [ ] Type "Undo last action" → works
- [ ] Type "Diagnostics" → shows status (if integrated)

### Database & Storage Checks
- [ ] `sqlite3 marcus_app/storage/database.db ".tables"` → all expected tables present
- [ ] No errors in audit log
- [ ] Storage capacity normal (not 100% full)
- [ ] Backup completed successfully

---

## Post-Deployment (1 hour after)

### Monitor for Errors
- [ ] Check application logs for warnings/errors
- [ ] Watch first 10 minutes of operation
- [ ] No crashes or hangs observed
- [ ] Network calls (if any) only to configured endpoints

### Production Usage Test
- [ ] Load 3-5 real syllabi
- [ ] Confirm classes extracted correctly
- [ ] Check deadlines appear in Inbox
- [ ] Verify items are undoable within 10s window
- [ ] Test "Undo" on a deletion

### Audit Trail Verification
- [ ] Check audit log (via Diagnostics or manual DB query)
- [ ] Intake operations logged
- [ ] User actions recorded
- [ ] Timestamps reasonable

### LLM (If Ollama installed)
- [ ] Check if Ollama auto-detected
- [ ] Diagnostics shows "LLM: available" or "unavailable"
- [ ] If available: classification confidence should be higher
- [ ] If unavailable: heuristic classification still works

---

## Rollback Plan (if problems)

### If v0.50 is unstable:

**Option 1: Revert to v0.49** (fast, safe)
```bash
git checkout HEAD~1  # Back to v0.49
python main.py
```

**Option 2: Disable Intake tab** (keep v0.50)
```
Comment out intake.js/intake.css loading in index.html
Restart Marcus
```

**Option 3: Debug and fix**
```bash
python scripts/verify_v050.py --debug
python -m pytest tests/test_v050_intake.py -v --tb=long
```

---

## Success Criteria

**v0.50 is deployed successfully if:**

✅ Marcus starts without errors  
✅ Agent Chat still works (v0.49 unbroken)  
✅ Intake tab appears and loads  
✅ Intake wizard classifies files correctly  
✅ Classes/items created without errors  
✅ Intake receipts generated and viewable  
✅ Runbook displays correctly  
✅ Diagnostics panel shows healthy status  
✅ At least 1 syllabus ingested end-to-end  
✅ Undo works on intake operations  
✅ No unexpected online calls detected  
✅ Audit trail complete  

---

## Sign-Off

| Role | Name | Date | Status |
|------|------|------|--------|
| Developer | - | - | [ ] Ready to deploy |
| Operator | - | - | [ ] Deployment complete |
| User | - | - | [ ] Smoke tests passed |

---

## Notes

**Gotchas to watch for:**
- Intake tab won't appear if `intake.js` doesn't load (check browser console for 404)
- Ollama adapter will silently fail if Ollama not running (this is OK, heuristic fallback activates)
- File uploads may timeout on very large PDFs (>10MB) — limit to 5MB chunks in production
- Receipt IDs are short UUIDs — they're unique but not cryptographically secure (fine for audit trail)

**Known limitations in v0.50:**
- OCR is simple regex-based (works for clean PDFs, struggles with poor scans)
- Classification confidence is heuristic (0-100%, not ML-based, so always deterministic)
- LLM integration uses Ollama only (no other local LLM support yet)
- No auto-save of draft intakes (refresh loses unsaved work)

---

**Deployment target:** Production  
**Estimated downtime:** 2-3 minutes (stop/start)  
**Rollback time:** <1 minute  
**Confidence level:** High (v0.49 frozen, v0.50 additive-only)  

**Ready to deploy v0.50 Launch Pack.**
