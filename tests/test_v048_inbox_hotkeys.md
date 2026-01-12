# v0.48: Inbox Keyboard Hotkeys - Manual Test Checklist

**Status:** Ready for Manual Testing  
**Estimated Time:** 15-20 minutes  
**Prerequisites:** v0.48 deployed, populated inbox with 5+ items

---

## Test Setup

### Pre-Test
- [ ] Start Marcus: `python marcus_app/backend/api.py`
- [ ] Navigate to Inbox tab
- [ ] Create 5+ test items in inbox (mix of statuses)
- [ ] Open browser DevTools (F12)

---

## Navigation Tests

### Test N1: Arrow Down Navigation
- [ ] Click on first inbox item
- [ ] Press Down arrow key
- **Expected:** Focus moves to next item (highlighted row)
- **Result:** ☐ Pass ☐ Fail

### Test N2: Arrow Up Navigation
- [ ] Press Down arrow 2x times
- [ ] Press Up arrow key
- **Expected:** Focus moves to previous item
- **Result:** ☐ Pass ☐ Fail

### Test N3: j/k Navigation (Vim-style)
- [ ] Press 'j' key
- **Expected:** Focus moves down (like Down arrow)
- **Result:** ☐ Pass ☐ Fail

- [ ] Press 'k' key
- **Expected:** Focus moves up (like Up arrow)
- **Result:** ☐ Pass ☐ Fail

### Test N4: Navigation Boundaries
- [ ] Navigate to last item
- [ ] Press Down arrow
- **Expected:** Focus stays on last item (doesn't wrap or error)
- **Result:** ☐ Pass ☐ Fail

- [ ] Navigate to first item
- [ ] Press Up arrow
- **Expected:** Focus stays on first item
- **Result:** ☐ Pass ☐ Fail

---

## Single Item Actions

### Test A1: Enter Opens Item
- [ ] Focus an item
- [ ] Press Enter
- **Expected:** Item opens in detail view
- **Result:** ☐ Pass ☐ Fail

### Test A2: Accept Action (A)
- [ ] Focus an inbox item
- [ ] Press 'a' key
- **Expected:** Item accepted (disappears from inbox or marked as accepted)
- **Result:** ☐ Pass ☐ Fail

### Test A3: Change Context (C)
- [ ] Focus an inbox item
- [ ] Press 'c' key
- **Expected:** Prompt for new context
- [ ] Enter new context (e.g., "projects", "personal")
- **Expected:** Item context changed
- **Result:** ☐ Pass ☐ Fail

### Test A4: Snooze Action (S)
- [ ] Focus an inbox item
- [ ] Press 's' key
- **Expected:** Prompt for snooze time
- [ ] Enter "30" (minutes)
- **Expected:** Item snoozed (hidden or marked with time)
- **Result:** ☐ Pass ☐ Fail

### Test A5: Pin Action (P)
- [ ] Focus an unpinned item
- [ ] Press 'p' key
- **Expected:** Item is pinned (visual indicator shows, e.g., ⭐)
- **Result:** ☐ Pass ☐ Fail

- [ ] Press 'p' key again
- **Expected:** Item is unpinned
- **Result:** ☐ Pass ☐ Fail

### Test A6: Delete Action (D)
- [ ] Focus an item
- [ ] Press 'd' key
- **Expected:** Confirmation dialog: "Delete item? (This can be undone for 10 seconds)"
- [ ] Click "Cancel"
- **Expected:** Item not deleted
- **Result:** ☐ Pass ☐ Fail

- [ ] Press 'd' key again
- [ ] Click "Confirm"
- **Expected:** Item deleted (soft delete)
- **Expected:** Undo notification appears: "Deleted. [Undo]"
- **Result:** ☐ Pass ☐ Fail

---

## Multi-Select Tests

### Test M1: Ctrl+Click Multi-Select
- [ ] Click first item (focus)
- [ ] Hold Ctrl, click third item
- **Expected:** Both items highlighted as "selected" (different from "focused")
- **Result:** ☐ Pass ☐ Fail

### Test M2: Shift+Click Range Select
- [ ] Click first item
- [ ] Hold Shift, click fourth item
- **Expected:** Items 1-4 all selected
- **Result:** ☐ Pass ☐ Fail

### Test M3: Ctrl+A Select All
- [ ] Press Ctrl+A (or Cmd+A on Mac)
- **Expected:** All items in inbox selected
- **Result:** ☐ Pass ☐ Fail

---

## Bulk Actions

### Test B1: Bulk Accept
- [ ] Select 3 items (Ctrl+Click or Shift+Click)
- [ ] Press 'a'
- **Expected:** Toast: "Accepted 3 item(s)"
- **Expected:** All 3 items accepted/removed
- **Result:** ☐ Pass ☐ Fail

### Test B2: Bulk Snooze
- [ ] Select 3 items
- [ ] Press 's'
- **Expected:** Prompt for snooze time
- [ ] Enter "60"
- **Expected:** Toast: "Snoozed 3 item(s)"
- **Result:** ☐ Pass ☐ Fail

### Test B3: Bulk Pin
- [ ] Select 2 items
- [ ] Press 'p'
- **Expected:** Both items pinned (or unpinned if already pinned)
- **Result:** ☐ Pass ☐ Fail

### Test B4: Bulk Delete
- [ ] Select 2 items
- [ ] Press 'd'
- **Expected:** Confirmation: "Delete 2 item(s)?"
- [ ] Confirm
- **Expected:** Toast: "Deleted 2 item(s). [Undo]"
- **Result:** ☐ Pass ☐ Fail

---

## Undo Integration

### Test U1: Undo Delete (10 seconds)
- [ ] Delete an item with 'd' + confirm
- [ ] Immediately click [Undo] button (or press Ctrl+Z if implemented)
- **Expected:** Item restored to inbox
- **Result:** ☐ Pass ☐ Fail

### Test U2: Undo Expires
- [ ] Delete an item
- [ ] Wait 11 seconds
- [ ] Try to click [Undo]
- **Expected:** Undo button disabled or "Undo expired" message
- **Result:** ☐ Pass ☐ Fail

### Test U3: Undo Bulk Actions
- [ ] Accept 3 items
- [ ] Click [Undo] within 10 seconds
- **Expected:** All 3 items restored to inbox
- **Result:** ☐ Pass ☐ Fail

---

## Edge Cases

### Test E1: Empty Inbox
- [ ] Clear all inbox items
- [ ] Press arrow keys, 'a', etc.
- **Expected:** No errors, graceful handling
- **Result:** ☐ Pass ☐ Fail

### Test E2: Single Item
- [ ] Leave only 1 item in inbox
- [ ] Press 'd' + confirm
- [ ] Navigation should still work (focus at position 0)
- **Expected:** No errors
- **Result:** ☐ Pass ☐ Fail

### Test E3: Rapid Key Presses
- [ ] Press arrow keys rapidly (10+ times)
- **Expected:** Smooth navigation, no lag
- **Result:** ☐ Pass ☐ Fail

### Test E4: Action During Navigation
- [ ] Start navigating with arrow keys
- [ ] While focused on item, press 'a'
- **Expected:** Action applies to focused item
- **Result:** ☐ Pass ☐ Fail

---

## Integration Tests

### Test I1: Keyboard Doesn't Interfere with Text Input
- [ ] Open item in detail view (shows textarea for notes)
- [ ] Type in textarea: "hello"
- [ ] Press 'a' in textarea
- **Expected:** 'a' is typed (not interpreted as "accept")
- **Result:** ☐ Pass ☐ Fail

### Test I2: Keyboard Works After Mouse Click
- [ ] Click an item with mouse
- [ ] Press 'd'
- **Expected:** Item deleted (keyboard works after mouse)
- **Result:** ☐ Pass ☐ Fail

### Test I3: Context Preservation
- [ ] Select multiple items
- [ ] Perform bulk action
- [ ] Inbox refreshes
- [ ] Selection should clear (or be preserved - design decision)
- **Result:** ☐ Pass ☐ Fail

---

## Performance & Responsiveness

### Test P1: Response Time < 100ms
- [ ] Focus an item
- [ ] Press 'a' (accept action)
- [ ] Measure time to response (DevTools > Performance tab)
- **Expected:** < 100ms for heuristic commands (excluding network)
- **Result:** ☐ Pass ☐ Fail

### Test P2: No UI Freezing
- [ ] Select 100+ items (create test data if needed)
- [ ] Perform bulk delete
- [ ] UI should remain responsive
- **Expected:** No visible lag or freezing
- **Result:** ☐ Pass ☐ Fail

### Test P3: Large Inbox Virtualization
- [ ] Create 200+ items in inbox
- [ ] Scroll through list with keyboard
- [ ] Check DevTools > Memory
- **Expected:** Memory usage < 50MB (virtualization working)
- **Result:** ☐ Pass ☐ Fail

---

## Accessibility

### Test Acc1: Focus Indicator Visible
- [ ] Navigate with keyboard
- [ ] Focused item should have clear visual indicator (border, highlight, etc.)
- **Expected:** Can see which item has focus at all times
- **Result:** ☐ Pass ☐ Fail

### Test Acc2: No Keyboard Trap
- [ ] Tab through entire page
- [ ] Should eventually exit inbox and move to next page element
- **Expected:** Not trapped in keyboard navigation
- **Result:** ☐ Pass ☐ Fail

### Test Acc3: Screen Reader Compatibility
- [ ] (Optional) Use screen reader (NVDA, JAWS, VoiceOver)
- [ ] Navigate inbox with keyboard
- **Expected:** Items read aloud with context
- **Result:** ☐ Pass ☐ Fail

---

## Browser Compatibility

### Test B1: Chrome/Edge
- [ ] Run all tests in Chrome
- **Result:** ☐ Pass ☐ Fail

### Test B2: Firefox
- [ ] Run all tests in Firefox
- **Result:** ☐ Pass ☐ Fail

### Test B3: Safari
- [ ] Run all tests in Safari
- **Result:** ☐ Pass ☐ Fail

---

## Overall Assessment

### Summary
- **Total Tests:** 40+
- **Passed:** ___
- **Failed:** ___
- **Skipped:** ___

### Sign-Off
- **Tester Name:** _________________
- **Date:** _________________
- **Status:** ☐ Ready ☐ Needs Fixes ☐ Blocked

### Issues Found
1. _________________________________________________
2. _________________________________________________
3. _________________________________________________

### Recommendation
☐ Deploy to Production  
☐ Deploy with Caution  
☐ Do Not Deploy (needs fixes)

---

**End of Checklist**

For automated tests, see: `tests/test_v048_agent_history.py`
