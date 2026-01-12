# Marcus v0.46 - Mission Operations Panels - Manual Test Checklist

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local (http://localhost:8000)

---

## Pre-Test Setup

1. [ ] Marcus backend running (`python marcus_app/backend/api.py`)
2. [ ] Logged into Marcus UI
3. [ ] At least 1 class exists in system
4. [ ] At least 1 artifact exists (uploaded PDF or document)

---

## Test 1: Create Mission

**Steps:**
1. [ ] Navigate to Mission Control tab
2. [ ] Click "+ Create Mission" button
3. [ ] Enter mission name: "Test v0.46 Full Mission"
4. [ ] Select template: "Exam Prep"
5. [ ] Select a class from dropdown (if available)
6. [ ] Click "Create Mission"
7. [ ] Verify mission appears in left panel list

**Expected Result:** Mission created successfully, shows "draft" state

**Status:** ☐ PASS  ☐ FAIL
**Mission ID:** _____________
**Notes:** ___________________________________________________

---

## Test 2: Open Mission Detail with Operation Panels

**Steps:**
1. [ ] Select the newly created mission
2. [ ] Click "Open Full Detail" button
3. [ ] Mission Detail modal opens
4. [ ] Verify tabs are visible: Inbox, Extract, Ask, Practice, Checker, Citations, All Artifacts
5. [ ] Verify "Inbox" tab is active by default

**Expected Result:** Modal opens with tabbed operation panels

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 3: Inbox Panel - Link Artifacts (NO API REQUIRED)

**Steps:**
1. [ ] In Inbox tab, verify "Add Artifacts" section visible
2. [ ] Type filename in search box to filter
3. [ ] Verify available artifacts list loads
4. [ ] Check checkbox next to at least 1 artifact
5. [ ] Click "Link Selected Artifacts" button
6. [ ] Wait for success message
7. [ ] Verify linked artifact appears in "Linked Artifacts" section

**Expected Result:** Artifact linked successfully via UI only

**Status:** ☐ PASS  ☐ FAIL
**Artifacts linked:** _____________
**Notes:** ___________________________________________________

---

## Test 4: Extract Panel - Run Extract Box

**Steps:**
1. [ ] Click "Extract" tab
2. [ ] Verify extract panel shows linked documents count
3. [ ] Verify "Run Extract Box" button is visible
4. [ ] Click "Run Extract Box"
5. [ ] Wait for execution (may take 1-2 seconds)
6. [ ] Verify success message appears
7. [ ] Verify status changes to "done"

**Expected Result:** ExtractBox runs successfully, creates note artifact

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 5: Ask Panel - Submit Question (NO API REQUIRED)

**Steps:**
1. [ ] Click "Ask" tab
2. [ ] Type question in text area: "What are the main topics covered in this document?"
3. [ ] Verify "Use mission sources" checkbox is checked
4. [ ] Click "Ask Question" button
5. [ ] Wait for response
6. [ ] Verify answer is displayed
7. [ ] Verify citations are shown (if available)
8. [ ] Verify confidence and method badges appear

**Expected Result:** Question answered with citations via UI only

**Status:** ☐ PASS  ☐ FAIL
**Question asked:** _____________
**Answer received:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 6: Ask Panel - Pin as Note

**Steps:**
1. [ ] After receiving answer, click "Pin as Note" button
2. [ ] Wait for success message
3. [ ] Click "All Artifacts" tab
4. [ ] Verify new note artifact appears in list

**Expected Result:** QA pinned as note successfully

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 7: Ask Panel - Copy Citations

**Steps:**
1. [ ] Return to "Ask" tab
2. [ ] Verify citations section visible (if citations exist)
3. [ ] Click "Copy Citations" button
4. [ ] Open a text editor
5. [ ] Paste (Ctrl+V)
6. [ ] Verify citations are formatted correctly

**Expected Result:** Citations copied to clipboard

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 8: Practice Panel - Create Session (NO API REQUIRED)

**Steps:**
1. [ ] Click "Practice" tab
2. [ ] Enter question count: 5
3. [ ] Click "Create Session" button
4. [ ] Wait for execution
5. [ ] Verify success message
6. [ ] Verify practice session appears in list
7. [ ] Click "Open Session" button
8. [ ] Verify practice questions are displayed

**Expected Result:** Practice session created with 5 questions via UI only

**Status:** ☐ PASS  ☐ FAIL
**Session ID:** _____________
**Questions generated:** _____________
**Notes:** ___________________________________________________

---

## Test 9: Practice Panel - Submit Answer (NO API REQUIRED)

**Steps:**
1. [ ] In practice session, locate first question
2. [ ] Type answer in text area
3. [ ] Click "Submit Answer" button
4. [ ] Wait for confirmation
5. [ ] Verify "Check Answer" button becomes enabled
6. [ ] Verify answer input is disabled after submission

**Expected Result:** Answer submitted successfully via UI only

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 10: Practice Panel - Check Answer (NO API REQUIRED)

**Steps:**
1. [ ] Click "Check Answer" button on submitted question
2. [ ] Wait for checker to run
3. [ ] Verify check result appears (Correct/Incorrect)
4. [ ] Verify explanation is shown
5. [ ] Verify citations/sources are shown (if available)
6. [ ] Verify "Mark Verified" and "Disagree" buttons appear

**Expected Result:** Answer checked with explanation + sources via UI only

**Status:** ☐ PASS  ☐ FAIL
**Result:** ☐ CORRECT  ☐ INCORRECT
**Notes:** ___________________________________________________

---

## Test 11: Practice Panel - Mark Verification Feedback

**Steps:**
1. [ ] Click "Mark Verified" button (or "Disagree")
2. [ ] Verify success message appears
3. [ ] Verify score updates in session header

**Expected Result:** Verification feedback recorded

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 12: Citations Panel - Generate Report (NO API REQUIRED)

**Steps:**
1. [ ] Click "Citations" tab
2. [ ] Click "Generate Citation Snapshot" button
3. [ ] Wait for execution
4. [ ] Verify success message
5. [ ] Verify citation report is displayed with:
   - Top sources list
   - Total citations count
   - Chunk usage statistics (if available)
6. [ ] Click "Copy Report" button
7. [ ] Paste into text editor
8. [ ] Verify report is formatted correctly

**Expected Result:** Citation report generated and copyable via UI only

**Status:** ☐ PASS  ☐ FAIL
**Total citations:** _____________
**Notes:** ___________________________________________________

---

## Overall Test Results

**Total Tests:** 12
**Passed:** _____________
**Failed:** _____________
**Blocked:** _____________

**CRITICAL ACCEPTANCE CRITERION:**

From UI alone (no curl/API calls), can you run the full six-box mission end-to-end?

- [ ] Create mission
- [ ] Link artifacts (Inbox UI)
- [ ] Run Extract (Extract panel)
- [ ] Ask question (Ask panel)
- [ ] Create practice session (Practice panel)
- [ ] Submit answer (Practice panel)
- [ ] Check answer (Checker via Practice panel)
- [ ] Generate citations (Citations panel)

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

## Recommendations

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Sign-Off:**

Tester: _________________________ Date: _____________

---

## Notes for Future Enhancements (v0.47+)

- [ ] Canvas editor (drag/drop box arrangement)
- [ ] Mission scheduling (reminders, recurring missions)
- [ ] 3D visualization (if 2D proves useful)
- [ ] Enhanced artifact viewer (preview PDF/images inline)
- [ ] Bulk artifact operations
- [ ] Practice session history/analytics
- [ ] Citation graph visualization
