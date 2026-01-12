# Marcus v0.47b - Central Agent Chat - Manual Test Checklist

**Test Date:** _____________
**Tester:** _____________
**Environment:** Local (http://localhost:8000)

---

## Pre-Test Setup

1. [ ] Marcus backend running (`python marcus_app/backend/api.py`)
2. [ ] v0.47a (Inbox + Quick Add) verified working
3. [ ] Logged into Marcus UI
4. [ ] At least 1 class exists in system (for command testing)
5. [ ] Agent chat visible on Home tab

---

## Test 1: Agent Chat UI Display

**Steps:**
1. [ ] Navigate to Home tab (should be default)
2. [ ] Verify "Marcus Command Center" card is visible
3. [ ] Verify agent chat interface is displayed with:
   - Message area (empty initially)
   - Input textarea at bottom
   - Send button
   - Suggestion chips
4. [ ] Verify welcome message from Marcus appears
5. [ ] Verify suggestion chips show example commands

**Expected Result:** Agent chat UI displays correctly with welcome message

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 2: Create Task Command

**Steps:**
1. [ ] Type in chat: "add task finish homework by Friday"
2. [ ] Click Send or press Enter
3. [ ] Verify user message appears in chat
4. [ ] Verify processing indicator shows
5. [ ] Verify agent response appears
6. [ ] Verify action card shows:
   - "Task Created" header
   - Task title
   - Context (class or General)
   - Due date
   - View/Edit buttons

**Expected Result:** Task created and confirmed with action card

**Status:** ☐ PASS  ☐ FAIL
**Task created:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 3: Create Task with Class Code

**Steps:**
1. [ ] Type: "add task PHYS214 lab report due tomorrow"
   (Replace PHYS214 with actual class code)
2. [ ] Send command
3. [ ] Verify task created
4. [ ] Verify action card shows correct class context
5. [ ] Verify due date is set to tomorrow

**Expected Result:** Task created in correct class context with due date

**Status:** ☐ PASS  ☐ FAIL
**Context detected:** _____________
**Notes:** ___________________________________________________

---

## Test 4: Create Note Command

**Steps:**
1. [ ] Type: "add note learned about thermodynamics today"
2. [ ] Send command
3. [ ] Verify note created
4. [ ] Verify action card shows "Note Created"
5. [ ] Click "View" button
6. [ ] Verify note is accessible (or shows appropriate message)

**Expected Result:** Note created successfully

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 5: Create Event Command

**Steps:**
1. [ ] Type: "schedule meeting tomorrow at 2pm"
2. [ ] Send command
3. [ ] Verify event created
4. [ ] Verify action card shows:
   - Event type
   - Due date/time (tomorrow 2pm)

**Expected Result:** Event created with correct date/time

**Status:** ☐ PASS  ☐ FAIL
**Due time correct:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 6: Show Inbox Command

**Steps:**
1. [ ] Ensure inbox has at least 1 item (use Quick Add if needed)
2. [ ] Type: "show inbox"
3. [ ] Send command
4. [ ] Verify agent responds with inbox count
5. [ ] Verify action card shows:
   - List of inbox items (up to 5)
   - Item types and contexts
   - Confidence scores
   - "Open Inbox" button

**Expected Result:** Inbox items displayed in action card

**Status:** ☐ PASS  ☐ FAIL
**Inbox count correct:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 7: What's Next Command

**Steps:**
1. [ ] Type: "what's next?"
2. [ ] Send command
3. [ ] Verify agent responds with active items
4. [ ] Verify action card shows:
   - List of next items (up to 5)
   - Item types, contexts, and due dates
   - Sorted by due date

**Expected Result:** Next action items displayed

**Status:** ☐ PASS  ☐ FAIL
**Items shown:** _____________
**Notes:** ___________________________________________________

---

## Test 8: What's Due Command

**Steps:**
1. [ ] Type: "what's due today?"
2. [ ] Send command
3. [ ] Verify agent responds with items due today
4. [ ] Verify action card shows due dates
5. [ ] Try: "what's due this week?"
6. [ ] Verify response includes week's items

**Expected Result:** Due items filtered correctly by time

**Status:** ☐ PASS  ☐ FAIL
**Today filter:** ☐ PASS  ☐ FAIL
**Week filter:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 9: Create Mission Command

**Steps:**
1. [ ] Type: "create mission exam prep for PHYS214"
2. [ ] Send command
3. [ ] Verify confirmation prompt appears asking to confirm
4. [ ] Click "✓ Confirm" button
5. [ ] Verify mission created
6. [ ] Verify action card shows:
   - Mission name
   - Mission type (exam_prep)
   - State (draft)
   - "Open Mission Control" button

**Expected Result:** Mission created after confirmation

**Status:** ☐ PASS  ☐ FAIL
**Confirmation shown:** ☐ YES  ☐ NO
**Mission created:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 10: Mission Status Command

**Steps:**
1. [ ] Ensure at least 1 mission exists
2. [ ] Type: "mission status"
3. [ ] Send command
4. [ ] Verify agent responds with mission summary
5. [ ] Verify action card shows stats grid:
   - Active count
   - Blocked count
   - Done count
   - Draft count

**Expected Result:** Mission statistics displayed

**Status:** ☐ PASS  ☐ FAIL
**Stats accurate:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 11: Show Blocked Missions Command

**Steps:**
1. [ ] Type: "show blocked"
2. [ ] Send command
3. [ ] If no blocked missions, verify agent says "No missions are currently blocked"
4. [ ] If blocked missions exist, verify list shows in action card

**Expected Result:** Blocked missions displayed or appropriate message

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 12: Clear Inbox Command (Confirmation)

**Steps:**
1. [ ] Ensure inbox has items
2. [ ] Type: "clear inbox"
3. [ ] Send command
4. [ ] Verify confirmation prompt appears
5. [ ] Click "✗ Cancel" button
6. [ ] Verify agent says "Action cancelled"
7. [ ] Verify inbox items still exist

**Expected Result:** Confirmation works, cancellation prevents action

**Status:** ☐ PASS  ☐ FAIL
**Confirmation shown:** ☐ YES  ☐ NO
**Cancel worked:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 13: Clear Inbox Command (Execute)

**Steps:**
1. [ ] Type: "clear inbox"
2. [ ] Send command
3. [ ] Click "✓ Confirm" button
4. [ ] Verify agent confirms items were filed
5. [ ] Navigate to Inbox tab
6. [ ] Verify inbox is now empty (or count decreased)

**Expected Result:** Inbox items accepted and filed

**Status:** ☐ PASS  ☐ FAIL
**Items filed:** _____________
**Notes:** ___________________________________________________

---

## Test 14: Unknown Command Handling

**Steps:**
1. [ ] Type: "do something random and unrecognized"
2. [ ] Send command
3. [ ] Verify agent responds with clarification message
4. [ ] Verify message suggests valid commands

**Expected Result:** Graceful handling of unknown commands

**Status:** ☐ PASS  ☐ FAIL
**Clarification shown:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 15: Low Confidence Command

**Steps:**
1. [ ] Type: "maybe add task" (vague command)
2. [ ] Send command
3. [ ] Verify agent asks for clarification
4. [ ] Verify suggests more specific command

**Expected Result:** Low-confidence intents trigger clarification

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 16: Multi-Line Input

**Steps:**
1. [ ] Type command with Shift+Enter to add newline
2. [ ] Type multiple lines
3. [ ] Press Enter without Shift to send
4. [ ] Verify multi-line command sent correctly

**Expected Result:** Multi-line input supported

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 17: Suggestion Chips

**Steps:**
1. [ ] Click a suggestion chip (e.g., "What's next?")
2. [ ] Verify command automatically sent
3. [ ] Verify response appears

**Expected Result:** Suggestion chips work as shortcuts

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 18: Action Card Buttons

**Steps:**
1. [ ] Create any item via command
2. [ ] In action card, click "View" button (if available)
3. [ ] Verify appropriate navigation or action occurs
4. [ ] Try other action card buttons (e.g., "Open Inbox", "Open Mission Control")
5. [ ] Verify buttons navigate correctly

**Expected Result:** Action card buttons execute correctly

**Status:** ☐ PASS  ☐ FAIL
**View button:** ☐ PASS  ☐ FAIL  ☐ N/A
**Navigate buttons:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 19: Chat History Persistence

**Steps:**
1. [ ] Send multiple commands
2. [ ] Verify all messages remain visible in chat
3. [ ] Scroll through message history
4. [ ] Navigate to different tab and back to Home
5. [ ] Verify chat history is cleared (by design) or persisted

**Expected Result:** Chat history behaves as expected (currently clears on tab switch)

**Status:** ☐ PASS  ☐ FAIL
**History behavior:** _____________
**Notes:** ___________________________________________________

---

## Test 20: Rapid Commands (Stress Test)

**Steps:**
1. [ ] Type and send a command
2. [ ] Immediately type and send another command
3. [ ] Verify processing indicator prevents double-sending
4. [ ] Verify both commands execute in order

**Expected Result:** No race conditions, commands queue properly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 21: Integration with v0.47a (Quick Add)

**Steps:**
1. [ ] Use agent chat to create a task
2. [ ] Press Ctrl+Shift+A to open Quick Add
3. [ ] Add an item via Quick Add
4. [ ] Type "show inbox" in agent chat
5. [ ] Verify Quick Add item appears in inbox list

**Expected Result:** Agent chat and Quick Add work together seamlessly

**Status:** ☐ PASS  ☐ FAIL
**Notes:** ___________________________________________________

---

## Test 22: Integration with Manual UI

**Steps:**
1. [ ] Create task via agent chat
2. [ ] Navigate to Inbox or Classes tab (depending on context)
3. [ ] Verify task appears in manual UI
4. [ ] Edit task manually
5. [ ] Return to Home and type "what's next?"
6. [ ] Verify edited task shows updated info

**Expected Result:** Agent actions visible in manual UI, changes reflected

**Status:** ☐ PASS  ☐ FAIL
**Manual UI shows item:** ☐ YES  ☐ NO
**Updates reflected:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 23: API Endpoint - Command

**Steps:**
1. [ ] Test via curl/Postman:
   ```
   curl -X POST http://localhost:8000/api/agent/command \
     -H "Content-Type: application/json" \
     -d '{"text": "what'\''s next?"}'
   ```
2. [ ] Verify response includes:
   - intent
   - confidence
   - message
   - action_card (if applicable)
   - needs_confirmation

**Expected Result:** API returns structured response

**Status:** ☐ PASS  ☐ FAIL
**Response structure:** ☐ CORRECT  ☐ INCORRECT
**Notes:** ___________________________________________________

---

## Test 24: Error Handling

**Steps:**
1. [ ] Stop backend server
2. [ ] Send command in chat
3. [ ] Verify error message appears
4. [ ] Restart backend
5. [ ] Send command again
6. [ ] Verify works correctly

**Expected Result:** Graceful error handling when backend unavailable

**Status:** ☐ PASS  ☐ FAIL
**Error message shown:** ☐ YES  ☐ NO
**Recovery works:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Test 25: End-to-End Workflow

**Steps:**
1. [ ] Start from Home tab (agent chat)
2. [ ] Type: "add task PHYS214 homework due Friday"
3. [ ] Verify task created
4. [ ] Type: "what's next?"
5. [ ] Verify task appears in next items list
6. [ ] Type: "show inbox"
7. [ ] Verify inbox (should be empty if high confidence)
8. [ ] Type: "create mission exam prep for PHYS214"
9. [ ] Confirm mission creation
10. [ ] Type: "mission status"
11. [ ] Verify mission shows in stats

**Expected Result:** Complete workflow executes without manual UI

**Status:** ☐ PASS  ☐ FAIL
**All commands worked:** ☐ YES  ☐ NO
**Notes:** ___________________________________________________

---

## Overall Test Results

**Total Tests:** 25
**Passed:** _____________
**Failed:** _____________
**Blocked:** _____________

**CRITICAL ACCEPTANCE CRITERION:**

Can you run Marcus all day from the chat, and trust it because you can see and override everything?

- [ ] Create tasks, notes, events via chat
- [ ] Check inbox and due items via chat
- [ ] Create missions via chat
- [ ] All actions produce real objects
- [ ] All objects viewable in manual UI
- [ ] Manual UI remains authoritative fallback
- [ ] No data loss possible
- [ ] Confirmations prevent destructive actions

**Chat-Driven Workflow:** ☐ PASS  ☐ FAIL

---

## Critical Issues Found

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

## Minor Issues Found

_____________________________________________________________
_____________________________________________________________
_____________________________________________________________

## Command Recognition Accuracy

**Task commands:** _____________% accurate
**Status queries:** _____________% accurate
**Mission commands:** _____________% accurate

**Most Common Misinterpretations:**
_____________________________________________________________
_____________________________________________________________

---

## User Experience Notes

**Chat feels natural:** ☐ YES  ☐ SOMEWHAT  ☐ NO

**Faster than manual UI:** ☐ YES  ☐ SAME  ☐ SLOWER

**Trustworthy (shows what it does):** ☐ YES  ☐ SOMEWHAT  ☐ NO

**Would use daily:** ☐ YES  ☐ MAYBE  ☐ NO

**Comments:**
_____________________________________________________________
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

## Notes for Future Enhancements (v0.48+)

- [ ] Persistent chat history across sessions
- [ ] LLM fallback for unrecognized commands
- [ ] Voice input
- [ ] Slash commands (e.g., `/task`, `/inbox`)
- [ ] Command autocomplete
- [ ] Multi-turn conversations (context retention)
- [ ] Bulk operations (e.g., "clear all overdue tasks")
- [ ] Undo last command
- [ ] Command history (up arrow to recall)
- [ ] Smart suggestions based on patterns
- [ ] Integration with Mission Control (run mission steps from chat)
