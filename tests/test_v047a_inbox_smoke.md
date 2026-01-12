# Marcus v0.47a - Inbox + Quick Add - Manual Test Checklist

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local (http://localhost:8000)

---

## Pre-Test Setup

1. [ ] Marcus backend running (`python marcus_app/backend/api.py`)
2. [ ] Logged into Marcus UI
3. [ ] At least 1 class exists in system (for classification testing)
4. [ ] Database migration for Items table applied

---

## Test 1: Database Migration

**Steps:**
1. [ ] Stop Marcus backend if running
2. [ ] Check database has Items table
3. [ ] Verify Items table has correct schema (item_type, status, context_kind, etc.)
4. [ ] Verify FTS5 index exists (items_fts)

**Expected Result:** Items table created with all required columns and indexes

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 2: Home Dashboard Display

**Steps:**
1. [ ] Open Marcus UI (http://localhost:8000)
2. [ ] Verify Home tab is active by default
3. [ ] Verify three stat cards are visible: Inbox Items, Due Soon, Overdue
4. [ ] Verify Quick Add button is visible
5. [ ] Verify Quick Actions section appears

**Expected Result:** Home dashboard displays with stats and quick actions

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 3: Quick Add Keyboard Shortcut

**Steps:**
1. [ ] From any tab, press Ctrl+Shift+A (or Cmd+Shift+A on Mac)
2. [ ] Verify Quick Add overlay appears
3. [ ] Verify input field is focused and ready to type
4. [ ] Press Escape
5. [ ] Verify overlay closes

**Expected Result:** Ctrl+Shift+A opens Quick Add modal, Escape closes it

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 4: Quick Add - Auto-File with High Confidence

**Steps:**
1. [ ] Press Ctrl+Shift+A to open Quick Add
2. [ ] Type: "PHYS214 homework due tomorrow - Chapter 3 problems"
   (Replace PHYS214 with an actual class code from your system)
3. [ ] Click "Add" or press Ctrl+Enter
4. [ ] Wait for processing
5. [ ] Verify toast notification appears showing "Auto-filed"
6. [ ] Verify confidence percentage is shown (should be >= 90%)
7. [ ] Verify "Undo" button is visible in toast
8. [ ] Wait 10 seconds - verify toast disappears

**Expected Result:** Item auto-filed with high confidence, toast shown with undo option

**Status:** ☐ PASS  ☐ FAIL
**Confidence shown:** _____________
**Notes:** ___________________________________________________

---

## Test 5: Quick Add - Undo Auto-File

**Steps:**
1. [ ] Press Ctrl+Shift+A
2. [ ] Type: "CS101 lab report completed"
3. [ ] Click "Add"
4. [ ] When toast appears, quickly click "Undo" button (within 10 seconds)
5. [ ] Verify "Item removed" confirmation toast appears

**Expected Result:** Undo removes auto-filed item successfully

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 6: Quick Add - Send to Inbox (Low Confidence)

**Steps:**
1. [ ] Press Ctrl+Shift+A
2. [ ] Type: "Remember to email professor about the thing"
   (Vague text with no class code - should trigger low confidence)
3. [ ] Click "Add"
4. [ ] Verify message shows "Added to inbox for review"
5. [ ] Verify prompt asks "View now?"
6. [ ] Click "OK" or "Yes"
7. [ ] Verify redirected to Inbox tab

**Expected Result:** Low-confidence item sent to inbox for manual review

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 7: Inbox Tab - View Items

**Steps:**
1. [ ] Navigate to Inbox tab (or continue from Test 6)
2. [ ] Verify inbox badge shows count (if items exist)
3. [ ] Verify inbox items list is displayed
4. [ ] For each item, verify visible:
   - Title
   - Item type badge (Note/Task/Event/Document)
   - Confidence badge with color coding (high=green, medium=orange, low=red)
   - Suggested route (class/project/personal)
   - Action buttons: Accept, Change Route, Snooze, Pin, Delete

**Expected Result:** Inbox displays items with full classification info

**Status:** ☐ PASS  ☐ FAIL
**Items in inbox:** _____________
**Notes:** ___________________________________________________

---

## Test 8: Inbox - Accept Classification

**Steps:**
1. [ ] In Inbox tab, locate an item
2. [ ] Click "✓ Accept" button
3. [ ] Verify success toast appears
4. [ ] Verify item removed from inbox list
5. [ ] Verify inbox count badge decrements

**Expected Result:** Item filed to suggested context and removed from inbox

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 9: Inbox - Change Route

**Steps:**
1. [ ] In Inbox tab, click "↻ Change Route" on an item
2. [ ] Verify modal dialog opens
3. [ ] Verify "Context Type" dropdown shows: Class, Project, Personal, General
4. [ ] Select "Class"
5. [ ] Verify class dropdown appears
6. [ ] Select a different class
7. [ ] Click "Save"
8. [ ] Verify success toast appears
9. [ ] Verify item removed from inbox

**Expected Result:** Item rerouted to user-selected context

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 10: Inbox - Snooze Item

**Steps:**
1. [ ] Click "💤 Snooze" on an inbox item
2. [ ] Verify snooze dialog appears with preset options:
   - Later today (6pm)
   - Tomorrow morning (9am)
   - Next week
3. [ ] Select "Later today"
4. [ ] Verify success toast appears
5. [ ] Verify item removed from inbox
6. [ ] Verify item status is "snoozed"

**Expected Result:** Item snoozed until selected time

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 11: Inbox - Pin Item

**Steps:**
1. [ ] Click "📌 Pin" on an inbox item
2. [ ] Verify success toast appears
3. [ ] Verify item shows 📌 icon in title
4. [ ] Verify pinned item appears at top of list
5. [ ] Click "📌 Unpin"
6. [ ] Verify pin icon removed

**Expected Result:** Pinned items appear at top of inbox

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 12: Inbox - Delete Item

**Steps:**
1. [ ] Click "Delete" button on an inbox item
2. [ ] Verify confirmation dialog appears
3. [ ] Click "OK" to confirm
4. [ ] Verify success toast appears
5. [ ] Verify item removed from inbox list

**Expected Result:** Item deleted permanently from inbox

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 13: Classification Accuracy - Class Code Detection

**Steps:**
1. [ ] Press Ctrl+Shift+A
2. [ ] Type: "ECE347 lecture notes from today's class"
   (Use an actual class code from your system)
3. [ ] Add item
4. [ ] Check if correctly classified to ECE347 context
5. [ ] Repeat with variations:
   - "ECE 347 notes" (space between code and number)
   - "ece347 quiz" (lowercase)
   - "Physics 214" (spelled out department)

**Expected Result:** Class codes detected accurately in various formats

**Status:** ☐ PASS  ☐ FAIL
**Detection rate:** _____________
**Notes:** ___________________________________________________

---

## Test 14: Classification Accuracy - Item Type Detection

**Steps:**
1. [ ] Test task detection - Type: "Finish homework by Friday"
2. [ ] Verify classified as "Task"
3. [ ] Test event detection - Type: "Office hours tomorrow at 2pm"
4. [ ] Verify classified as "Event"
5. [ ] Test note detection - Type: "Learned about quantum mechanics today"
6. [ ] Verify classified as "Note"

**Expected Result:** Item types correctly detected based on keywords

**Status:** ☐ PASS  ☐ FAIL
**Task detection:** ☐ PASS  ☐ FAIL
**Event detection:** ☐ PASS  ☐ FAIL
**Note detection:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 15: Classification Accuracy - Date Parsing

**Steps:**
1. [ ] Type: "Submit report tomorrow"
2. [ ] Verify due_at is set to tomorrow's date
3. [ ] Type: "Meeting on Friday at 3pm"
4. [ ] Verify due_at is set to next Friday at 15:00
5. [ ] Type: "Exam next Monday"
6. [ ] Verify due_at is set to next Monday

**Expected Result:** Relative dates parsed correctly into due_at timestamps

**Status:** ☐ PASS  ☐ FAIL
**Tomorrow parsing:** ☐ PASS  ☐ FAIL
**Day-of-week parsing:** ☐ PASS  ☐ FAIL
**Time parsing:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 16: Home Dashboard Stats Update

**Steps:**
1. [ ] Navigate to Home tab
2. [ ] Note current inbox count
3. [ ] Add new items via Quick Add (send to inbox)
4. [ ] Return to Home tab
5. [ ] Verify inbox count increased
6. [ ] Accept items from inbox
7. [ ] Return to Home tab
8. [ ] Verify inbox count decreased

**Expected Result:** Home dashboard stats reflect real-time inbox changes

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 17: Inbox Badge on Tab

**Steps:**
1. [ ] Ensure inbox has items
2. [ ] Navigate to any non-Inbox tab
3. [ ] Verify Inbox tab shows badge with count
4. [ ] Accept/delete all inbox items
5. [ ] Verify badge disappears when inbox is empty

**Expected Result:** Inbox tab badge shows count when items present

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 18: API Endpoint - Quick Add

**Steps:**
1. [ ] Test via curl/Postman:
   ```
   curl -X POST http://localhost:8000/api/inbox/quick-add \
     -H "Content-Type: application/json" \
     -d '{"text": "CS101 assignment due tomorrow"}'
   ```
2. [ ] Verify response includes:
   - item_id
   - auto_filed (true/false)
   - classification (type, context_kind, confidence, etc.)

**Expected Result:** API returns classification results and auto-file status

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 19: API Endpoint - Inbox Stats

**Steps:**
1. [ ] Test via curl/Postman:
   ```
   curl http://localhost:8000/api/inbox/stats
   ```
2. [ ] Verify response includes:
   - inbox_count
   - due_soon_count
   - overdue_count

**Expected Result:** API returns accurate inbox statistics

**Status:** ☐ PASS  ☐ FAIL
**Stats returned:** _____________
**Notes:** ___________________________________________________

---

## Test 20: Edge Cases

**Steps:**
1. [ ] Test empty input in Quick Add
2. [ ] Verify error message shown
3. [ ] Test very long text (1000+ characters)
4. [ ] Verify item created successfully
5. [ ] Test special characters: <>@#$%&*
6. [ ] Verify handled without errors
7. [ ] Test multiple hashtags: "#physics #homework #chapter3"
8. [ ] Verify tags extracted correctly

**Expected Result:** Edge cases handled gracefully without crashes

**Status:** ☐ PASS  ☐ FAIL
**Empty input:** ☐ PASS  ☐ FAIL
**Long text:** ☐ PASS  ☐ FAIL
**Special chars:** ☐ PASS  ☐ FAIL
**Hashtags:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Overall Test Results

**Total Tests:** 20
**Passed:** _____________
**Failed:** _____________
**Blocked:** _____________

**CRITICAL ACCEPTANCE CRITERION:**

Can you use Quick Add + Inbox workflow end-to-end without API/curl?

- [ ] Press Ctrl+Shift+A anywhere in Marcus
- [ ] Add item with class code (auto-files)
- [ ] Add vague item (goes to inbox)
- [ ] Review and accept/reroute inbox items
- [ ] View stats on Home dashboard
- [ ] Snooze and pin items

**UI-Only Workflow:** ☐ PASS  ☐ FAIL

---

## Critical Issues Found

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

## Minor Issues Found

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

## Classification Accuracy Notes

**Class Code Detection Rate:** _____________
**Item Type Detection Rate:** _____________
**Date Parsing Accuracy:** _____________

**Most Common Misclassifications:**
_____________________________________________________________
_____________________________________________________________

---

## Recommendations

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Sign-Off:**

Tester: _________________________ Date: _____________

---

## Notes for Future Enhancements (v0.47b+)

- [ ] Central Agent Chat (conversational control layer)
- [ ] LLM-enhanced classification (fallback when heuristics fail)
- [ ] Bulk inbox operations
- [ ] Smart suggestions based on patterns
- [ ] Integration with Mission Control (create missions from inbox items)
- [ ] Mobile-responsive Quick Add overlay
- [ ] Voice input for Quick Add
- [ ] Keyboard navigation for inbox items
