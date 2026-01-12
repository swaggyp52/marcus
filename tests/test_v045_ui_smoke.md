# Marcus v0.45 - Mission Control UI - Manual Test Checklist

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local (http://localhost:8000)

---

## Pre-Test Setup

1. [ ] Marcus backend running (`python marcus_app/backend/api.py`)
2. [ ] Logged into Marcus UI
3. [ ] At least 1 class and 1 artifact exist in system

---

## Test 1: Mission Control Tab Access

**Steps:**
1. [ ] Click "🎯 Mission Control" tab
2. [ ] Verify tab switches to missions view
3. [ ] Verify left panel shows "Missions" header
4. [ ] Verify right panel shows "Mission Summary" header
5. [ ] Verify "+ Create Mission" button visible

**Expected Result:** Mission Control UI loads without errors

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 2: Create Mission from Template

**Steps:**
1. [ ] Click "+ Create Mission" button
2. [ ] Modal opens with "Create New Mission" title
3. [ ] Enter mission name: "Test Exam Prep Mission"
4. [ ] Select template: "Exam Prep"
5. [ ] Optionally select a class
6. [ ] Click "Create Mission"
7. [ ] Modal closes
8. [ ] Mission appears in left panel list

**Expected Result:** Mission created successfully, appears in list

**Status:** ☐ PASS  ☐ FAIL
**Mission ID:** _____________
**Notes:** ___________________________________________________

---

## Test 3: Mission List Filtering

**Steps:**
1. [ ] Type text in search box
2. [ ] Verify list filters by mission name
3. [ ] Select "exam_prep" in Type filter
4. [ ] Verify only exam_prep missions show
5. [ ] Select "draft" in State filter
6. [ ] Verify only draft missions show
7. [ ] Clear all filters

**Expected Result:** Filters work correctly, list updates

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 4: Select Mission and View Summary

**Steps:**
1. [ ] Click on a mission in the left panel
2. [ ] Mission card highlights (border color changes)
3. [ ] Right panel updates with mission details
4. [ ] Mission name displayed
5. [ ] Mission type and state shown
6. [ ] Boxes list displayed (6 boxes for exam_prep)
7. [ ] Each box shows type and state badge

**Expected Result:** Mission summary displays correctly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 5: Run Next Box (InboxBox)

**Steps:**
1. [ ] Select a mission in draft state
2. [ ] Verify "Run Next: inbox" button visible
3. [ ] Verify blocker message shows: "link at least 1 artifact"
4. [ ] Click "Open Full Detail" button
5. [ ] Mission Detail modal opens
6. [ ] Modal shows mission name, boxes, artifacts

**Expected Result:** Mission detail modal opens correctly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 6: Link Artifact via InboxBox

**Steps:**
1. [ ] In mission detail modal, find InboxBox
2. [ ] Box shows state "idle" or "ready"
3. [ ] Click "Run" button on InboxBox
4. [ ] Wait for execution (should succeed or show artifact selection UI)
5. [ ] Close modal
6. [ ] Refresh mission summary
7. [ ] Verify InboxBox state changed to "done"
8. [ ] Verify artifact count > 0

**Expected Result:** InboxBox executes, state updates to done

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 7: Run ExtractBox

**Steps:**
1. [ ] Select mission with InboxBox done
2. [ ] Click "Run Next" button (should be ExtractBox)
3. [ ] Wait for execution
4. [ ] Success message appears
5. [ ] Mission summary refreshes
6. [ ] ExtractBox state = "done"
7. [ ] Verify "note" artifact created

**Expected Result:** ExtractBox runs successfully, creates note artifact

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 8: Life View Tab Access

**Steps:**
1. [ ] Click "🌐 Life View" tab
2. [ ] Tab switches to Life View
3. [ ] Canvas displays with graph visualization
4. [ ] Nodes visible (missions, boxes, artifacts, classes)
5. [ ] Edges connect nodes
6. [ ] Checkboxes for node types present
7. [ ] Control buttons visible (Refresh, Reset Layout, Center View)

**Expected Result:** Life View renders graph correctly

**Status:** ☐ PASS  ☐ FAIL
**Nodes displayed:** _____________
**Edges displayed:** _____________
**Notes:** ___________________________________________________

---

## Test 9: Life View Interactions

**Steps:**
1. [ ] Scroll mouse wheel on canvas
2. [ ] Verify zoom in/out works
3. [ ] Click and drag background
4. [ ] Verify pan works
5. [ ] Click on a mission node
6. [ ] Verify switches to Mission Control tab
7. [ ] Verify mission is selected

**Expected Result:** Pan/zoom work, node clicks navigate correctly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 10: Life View Filtering

**Steps:**
1. [ ] Return to Life View tab
2. [ ] Uncheck "Boxes" checkbox
3. [ ] Verify box nodes disappear
4. [ ] Uncheck "Artifacts" checkbox
5. [ ] Verify artifact nodes disappear
6. [ ] Re-check both
7. [ ] Verify nodes reappear
8. [ ] Click "Reset Layout" button
9. [ ] Verify nodes rearrange
10. [ ] Click "Center View" button
11. [ ] Verify view resets to center

**Expected Result:** Node filtering and controls work correctly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 11: Complete Mission Flow (End-to-End)

**Steps:**
1. [ ] Create new exam_prep mission
2. [ ] Run InboxBox (link 1 artifact)
3. [ ] Run ExtractBox
4. [ ] Run AskBox (ask question via API or future UI)
5. [ ] Run PracticeBox (create practice session)
6. [ ] Run CheckerBox (answer + check via API)
7. [ ] Run CitationsBox
8. [ ] Verify all boxes show "done" state
9. [ ] Verify mission has 6+ artifacts
10. [ ] Verify mission state updates

**Expected Result:** Full mission flow executes successfully

**Status:** ☐ PASS  ☐ FAIL
**Mission ID:** _____________
**Artifacts created:** _____________
**Notes:** ___________________________________________________

---

## Test 12: Error Handling

**Steps:**
1. [ ] Try to create mission with empty name
2. [ ] Verify error message appears
3. [ ] Try to run box that's already running (if possible)
4. [ ] Verify appropriate error shown
5. [ ] Try to run box that's blocked
6. [ ] Verify blocker message displayed

**Expected Result:** Errors handled gracefully with clear messages

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Overall Test Results

**Total Tests:** 12
**Passed:** _____________
**Failed:** _____________
**Blocked:** _____________

**Critical Issues Found:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Minor Issues Found:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Recommendations:**
_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

**Sign-Off:**

Tester: _________________________ Date: _____________

---

## Notes for Future Enhancements (v0.46+)

- [ ] Inbox UI: artifact selection interface
- [ ] Ask UI: question input panel
- [ ] Practice UI: question list with answer inputs
- [ ] Checker UI: answer verification panel
- [ ] Canvas editor: drag/drop box arrangement
- [ ] 3D visualization
- [ ] Mission scheduling
