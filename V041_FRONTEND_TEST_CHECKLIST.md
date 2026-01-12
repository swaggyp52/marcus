# V0.41 Frontend Testing Checklist

**Version:** V0.41  
**Date Created:** 2024  
**Status:** Ready for Testing  
**Estimated Time:** 30-45 minutes per test run

---

## Pre-Test Setup

### Environment Checklist
- [ ] Marcus backend v0.40 running (`python main.py`)
- [ ] Database initialized with test data
- [ ] User authenticated and logged in
- [ ] Browser: Chrome/Firefox/Safari (latest version)
- [ ] Network: Internet connection (for online mode tests)
- [ ] Console: DevTools open for error monitoring

### Test Data Preparation
```bash
# Create test project/repo in database
# (Or use existing project-1)
```

---

## Test Suite 1: Offline Workflow (No Internet Required)

### 1.1 Interface & Navigation
- [ ] **Projects tab exists** - Click Projects tab in navigation
  - Expected: Dev Mode panel appears
  - Result: _______________
- [ ] **Dev Mode panel layout** - Check grid layout (2 columns)
  - Expected: Git Status (left top), File List (left middle), Commit (left bottom), Diff (right top), ChangeSets (right middle), Online Mode (right bottom)
  - Result: _______________
- [ ] **Tab switching** - Classes → Projects → Assignments → Audit
  - Expected: Smooth transitions, content changes
  - Result: _______________

### 1.2 Git Status
- [ ] **Initialize Dev Mode** - Click "Initialize Dev Mode" button
  - Expected: devModeUI instantiated, git status loaded
  - Result: _______________
- [ ] **Status display** - Check git status panel
  - Expected: Shows branch name, clean/dirty status, file counts
  - Result: _______________
- [ ] **Refresh status** - Make a file change, click "Refresh" button
  - Expected: Unstaged files count updates
  - Result: _______________
- [ ] **Color coding** - Check status colors
  - Expected: Clean=green (✓), Dirty=red (✗)
  - Result: _______________

### 1.3 File List Management
- [ ] **File grouping** - Check files appear in correct groups
  - Expected: Three sections (Staged, Unstaged, Untracked)
  - Result: _______________
- [ ] **Status badges** - Check file type badges
  - Expected: MODIFIED=orange, NEW=green, STAGED=blue, DELETED=red
  - Result: _______________
- [ ] **Click to select** - Click a file in the list
  - Expected: File highlights, diff viewer updates
  - Result: _______________
- [ ] **Stage single file** - Click "Stage" button on unstaged file
  - Expected: File moves to Staged group, counts update
  - Result: _______________
- [ ] **Stage all** - Create 3+ unstaged files, click "Stage All"
  - Expected: All files move to Staged group
  - Result: _______________
- [ ] **Revert file** - Click "Revert" on staged file
  - Expected: File removed from staging, goes back to unstaged
  - Result: _______________
- [ ] **Discard all** - Click "Discard All" with unstaged changes
  - Expected: All unstaged changes reverted (or confirmation dialog)
  - Result: _______________

### 1.4 Diff Viewer
- [ ] **Diff display** - Select file and check diff viewer
  - Expected: Shows unified diff format with proper syntax highlighting
  - Result: _______________
- [ ] **Syntax highlighting** - Verify line colors
  - Expected: Added=green, Removed=red, Context=gray, Headers=blue
  - Result: _______________
- [ ] **Staged only toggle** - Check "Show staged only" checkbox
  - Expected: Diff updates to show only staged changes
  - Result: _______________
- [ ] **Scrollable** - Create large diff (50+ lines)
  - Expected: Diff scrolls, not expanding container
  - Result: _______________
- [ ] **Copy to clipboard** - Click "Copy Diff" button
  - Expected: Toast "Diff copied to clipboard", can paste in text editor
  - Result: _______________

### 1.5 Commit Workflow
- [ ] **Commit form fields** - Check message, author, email inputs
  - Expected: All three fields present and editable
  - Result: _______________
- [ ] **Author persistence** - Fill author/email, commit, check next form
  - Expected: Author name persists, email persists
  - Result: _______________
- [ ] **Validation** - Try commit with empty message
  - Expected: Error "Commit message required"
  - Result: _______________
- [ ] **Validation** - Try commit with no staged files
  - Expected: Error "No staged changes" or button disabled
  - Result: _______________
- [ ] **Successful commit** - Stage files, fill form completely, click commit
  - Expected: Success toast, file list clears, status updates
  - Result: _______________
- [ ] **Clear form after commit** - Check message field is cleared
  - Expected: Message empty, author/email persist
  - Result: _______________

### 1.6 ChangeSet Management
- [ ] **ChangeSet list** - Check initial state
  - Expected: Shows "No changesets" or list of existing changesets
  - Result: _______________
- [ ] **Create ChangeSet** - Click "+ New ChangeSet" with staged changes
  - Expected: Modal appears with name/notes form
  - Result: _______________
- [ ] **Create validation** - Click create with empty name
  - Expected: Error or validation message
  - Result: _______________
- [ ] **Create success** - Fill name/notes, click create
  - Expected: Modal closes, changeset appears in list
  - Result: _______________
- [ ] **ChangeSet display** - Check changeset item shows:
  - Expected: Name, timestamp, notes, three action buttons
  - Result: _______________
- [ ] **Restore ChangeSet** - Click "Restore" button on changeset
  - Expected: Files from changeset applied to working directory (or modal if multiple)
  - Result: _______________
- [ ] **Export patch** - Click "Export" button
  - Expected: Browser downloads `.patch` file with changeset contents
  - Result: _______________
- [ ] **Delete ChangeSet** - Click "Delete" button (with confirmation)
  - Expected: Changeset removed from list
  - Result: _______________

### 1.7 Error Handling
- [ ] **Network error handling** - Simulate network failure during git status refresh
  - Expected: Error message displayed, UI remains functional
  - Result: _______________
- [ ] **Invalid branch** - Try operations on deleted branch
  - Expected: Error message with context
  - Result: _______________
- [ ] **Error message disappears** - Trigger error, wait 5 seconds
  - Expected: Error toast auto-disappears
  - Result: _______________
- [ ] **Success message disappears** - Successful operation, wait 3 seconds
  - Expected: Success toast auto-disappears
  - Result: _______________

---

## Test Suite 2: Online Workflow (Requires Internet & Remote Repo)

### 2.1 Online Mode Toggle
- [ ] **Toggle visibility** - Check "🌐 Online Mode" section
  - Expected: Toggle switch + badge visible
  - Result: _______________
- [ ] **Toggle OFF state** - Default state
  - Expected: Badge shows "OFFLINE", push/PR buttons disabled (gray)
  - Result: _______________
- [ ] **Toggle ON state** - Click toggle to enable
  - Expected: Badge shows "ONLINE", push/PR buttons enabled (blue)
  - Result: _______________
- [ ] **Toggle persistence** - Disable, wait, check state after refresh
  - Expected: State persisted to backend
  - Result: _______________
- [ ] **Auth check** - Logout, try to enable online mode
  - Expected: Error "Not authenticated" or automatic re-login
  - Result: _______________

### 2.2 Push Workflow
- [ ] **Button disabled when offline** - Check push button state
  - Expected: Disabled (grayed out) when Online Mode OFF
  - Result: _______________
- [ ] **Button enabled when online** - Toggle Online Mode ON
  - Expected: Button enabled (blue)
  - Result: _______________
- [ ] **No commits to push** - With clean repo, try push
  - Expected: Error "No commits to push" or modal shows 0 commits
  - Result: _______________
- [ ] **Show push confirmation** - Make commit, click "Push to Remote"
  - Expected: Modal appears with summary
  - Result: _______________
- [ ] **Confirmation content** - Check modal fields
  - Expected: Repository, Remote, Branch, Commits count, Files count all visible
  - Result: _______________
- [ ] **Cancel push** - Click "Cancel" in confirmation
  - Expected: Modal closes, nothing happens
  - Result: _______________
- [ ] **Confirm push** - Click "✓ Confirm Push"
  - Expected: Push executed, success message, modal closes
  - Result: _______________
- [ ] **Push success** - Verify commits in remote (check GitHub/GitLab)
  - Expected: New commits visible on remote
  - Result: _______________
- [ ] **Push failure handling** - Try push to invalid remote
  - Expected: Error message with context (auth failed, network error, etc.)
  - Result: _______________

### 2.3 Pull Request Workflow
- [ ] **Button disabled when offline** - Check PR button state
  - Expected: Disabled (grayed out) when Online Mode OFF
  - Result: _______________
- [ ] **Button enabled when online** - Toggle Online Mode ON
  - Expected: Button enabled (blue)
  - Result: _______________
- [ ] **Show PR confirmation** - Click "Create Pull Request"
  - Expected: Modal appears with form + summary
  - Result: _______________
- [ ] **Confirmation content** - Check modal fields
  - Expected: Title input, Description textarea, Repository, Source/Base branches, Files/Commits count
  - Result: _______________
- [ ] **Title validation** - Try create PR with empty title
  - Expected: Error "PR title required"
  - Result: _______________
- [ ] **Fill form** - Enter title and description
  - Expected: Form values display in modal
  - Result: _______________
- [ ] **Cancel PR** - Click "Cancel" in confirmation
  - Expected: Modal closes, nothing happens
  - Result: _______________
- [ ] **Confirm PR** - Click "✓ Create PR"
  - Expected: PR created, success message, modal closes
  - Result: _______________
- [ ] **PR created** - Verify PR in remote (check GitHub/GitLab)
  - Expected: New PR visible with title and description
  - Result: _______________
- [ ] **PR failure handling** - Try PR with auth issues
  - Expected: Error message with context
  - Result: _______________

---

## Test Suite 3: UI/UX & Responsiveness

### 3.1 Modal Behavior
- [ ] **Modal visibility** - When modal open, check background
  - Expected: 80% opacity dark background, modal centered
  - Result: _______________
- [ ] **Close button (X)** - Click X on any modal
  - Expected: Modal closes, background cleared
  - Result: _______________
- [ ] **Click outside modal** - Click background (if not blocked)
  - Expected: Modal may or may not close (depending on implementation)
  - Result: _______________
- [ ] **Keyboard (ESC)** - Press Escape key with modal open
  - Expected: Modal closes (if implemented)
  - Result: _______________
- [ ] **Modal z-index** - Open modal, check it's always on top
  - Expected: Modal visible above all other content
  - Result: _______________

### 3.2 Form Behavior
- [ ] **Input focus** - Click input field
  - Expected: Border color changes to #667eea (purple), cursor visible
  - Result: _______________
- [ ] **Text area behavior** - Type in textarea, check line wrapping
  - Expected: Text wraps properly, scrollbar appears if needed
  - Result: _______________
- [ ] **Button states** - Check button hover effect
  - Expected: Color lightens, slight upward transform
  - Result: _______________
- [ ] **Disabled button** - Check button with `disabled` attribute
  - Expected: Grayed out, cursor not-allowed
  - Result: _______________

### 3.3 Visual Theme
- [ ] **Dark theme** - Check background colors
  - Expected: Primary background #0a0a0a (very dark), cards #1a1a1a
  - Result: _______________
- [ ] **Accent color** - Check primary action buttons
  - Expected: Gradient purple #667eea to #764ba2
  - Result: _______________
- [ ] **Status colors** - Check status badges
  - Expected: Success=green, Error=red, Warning=orange, Info=purple
  - Result: _______________
- [ ] **Text contrast** - Read all text clearly
  - Expected: White text on dark backgrounds (WCAG AA compliant)
  - Result: _______________

### 3.4 Responsive Design
- [ ] **Desktop view (1400px)** - Check at full width
  - Expected: 2-column dev panel side-by-side
  - Result: _______________
- [ ] **Tablet view (768px)** - Resize browser to 768px
  - Expected: Grid adjusts (single column or stacked)
  - Result: _______________
- [ ] **Mobile view (375px)** - Resize to mobile width
  - Expected: All content visible, scrollable, touch-friendly buttons
  - Result: _______________
- [ ] **Modal responsiveness** - Check modal on small screen
  - Expected: Modal width 90%, not overflowing
  - Result: _______________

---

## Test Suite 4: Security & Data Handling

### 4.1 Token Security
- [ ] **No token display** - Check entire UI for any token text
  - Expected: NO tokens/secrets visible anywhere
  - Result: _______________
- [ ] **Browser console** - Open DevTools, check console logs
  - Expected: No tokens logged, only public data
  - Result: _______________
- [ ] **Network tab** - Open Network tab, make API call
  - Expected: Auth header sent via cookie (not visible in body)
  - Result: _______________

### 4.2 Input Validation
- [ ] **XSS prevention** - Enter `<script>alert('xss')</script>` in commit message
  - Expected: Treated as literal text, not executed
  - Result: _______________
- [ ] **Special characters** - Enter `'; DROP TABLE --` in filename
  - Expected: Treated as literal text, no SQL injection
  - Result: _______________
- [ ] **Unicode handling** - Enter emoji/non-ASCII in commit message
  - Expected: Displays correctly, saved correctly
  - Result: _______________

### 4.3 Session Management
- [ ] **Lock button** - Click "🔒 Lock" button
  - Expected: Session terminated, redirected to login
  - Result: _______________
- [ ] **Auth cookie present** - Check cookies (DevTools > Application > Cookies)
  - Expected: Auth cookie present, httpOnly flag set
  - Result: _______________
- [ ] **Session timeout** - Wait 30+ minutes without activity
  - Expected: Auto-logout or re-auth required (backend dependent)
  - Result: _______________

### 4.4 CSRF Protection
- [ ] **POST requests** - Monitor network tab during push/PR
  - Expected: CSRF token sent (via cookie, not header)
  - Result: _______________

---

## Test Suite 5: Life View (Experimental)

### 5.1 Feature Flag
- [ ] **Feature flag status** - Check app.js `loadLifeView()` function
  - Expected: Feature flag set (true/false)
  - Result: _______________
- [ ] **Hidden when disabled** - If featureFlag=false
  - Expected: Life View section not displayed
  - Result: _______________
- [ ] **Shown when enabled** - If featureFlag=true
  - Expected: Life View section visible below Dev Mode panel
  - Result: _______________

### 5.2 Graph Visualization
- [ ] **Canvas renders** - Check Life View canvas
  - Expected: Canvas visible, 600x400 size
  - Result: _______________
- [ ] **Graph data loads** - Check if nodes/edges appear
  - Expected: Circles (nodes) and lines (edges) visible
  - Result: _______________
- [ ] **Node types** - Check node colors
  - Expected: Commits=green, Branches=orange, Tags=red
  - Result: _______________

### 5.3 Interactivity
- [ ] **Click node** - Click on a node in the graph
  - Expected: Node highlights (white circle), logs to console
  - Result: _______________
- [ ] **Zoom** - Scroll wheel on canvas
  - Expected: Graph scales in/out (clamp 0.5x to 3x)
  - Result: _______________
- [ ] **Pan** - Drag on canvas
  - Expected: Graph translates in direction of drag
  - Result: _______________
- [ ] **Error handling** - If /api/life-graph fails
  - Expected: Graceful error (no crash), UI still functional
  - Result: _______________

---

## Test Suite 6: Edge Cases & Stress Testing

### 6.1 Large Data Sets
- [ ] **Many files** - Create 50+ file changes
  - Expected: File list scrollable, UI responsive
  - Result: _______________
- [ ] **Large diff** - View diff of 500+ line file
  - Expected: Diff viewer scrollable, not freezing
  - Result: _______________
- [ ] **Many changesets** - Create 20+ changesets
  - Expected: List scrollable, operations still responsive
  - Result: _______________

### 6.2 Edge Case Operations
- [ ] **Commit with multi-line message** - Commit with 5+ lines
  - Expected: Entire message saved and displayed
  - Result: _______________
- [ ] **File with spaces/special chars** - Stage file named `test file (copy).py`
  - Expected: File handled correctly, no escaping issues
  - Result: _______________
- [ ] **Very long branch name** - Create branch with 100+ character name
  - Expected: Displayed correctly (truncate or scroll if needed)
  - Result: _______________
- [ ] **Rapid operations** - Stage, commit, stage, commit (5x quickly)
  - Expected: All operations complete without race conditions
  - Result: _______________

### 6.3 Network Issues
- [ ] **Slow network** - Throttle network to 1G (DevTools)
  - Expected: UI shows loading state, operations complete
  - Result: _______________
- [ ] **Network dropout during operation** - Kill network mid-push
  - Expected: Error message, graceful failure (not crash)
  - Result: _______________
- [ ] **Server timeout** - Backend doesn't respond
  - Expected: Timeout error after 30 seconds, user can retry
  - Result: _______________

---

## Test Suite 7: Cross-Browser Testing

### 7.1 Chrome/Chromium
- [ ] **Desktop (latest)** - Run full test suite
  - Expected: All tests pass
  - Result: _______________
- [ ] **DevTools** - Check console for errors
  - Expected: No errors, only informational logs
  - Result: _______________

### 7.2 Firefox
- [ ] **Desktop (latest)** - Run full test suite
  - Expected: All tests pass
  - Result: _______________
- [ ] **Inspector** - Check console for errors
  - Expected: No errors
  - Result: _______________

### 7.3 Safari
- [ ] **Desktop (latest)** - Run full test suite
  - Expected: All tests pass
  - Result: _______________
- [ ] **Web Inspector** - Check console
  - Expected: No errors
  - Result: _______________

---

## Test Suite 8: Integration Tests

### 8.1 Multi-step Workflows
- [ ] **Complete offline workflow** - Init → Stage → Commit → ChangeSet → Export
  - Expected: All steps work, data persists
  - Result: _______________
- [ ] **Complete online workflow** - Everything + Enable Online Mode → Push → PR
  - Expected: All steps work, changes on remote
  - Result: _______________
- [ ] **Interleaved workflow** - Offline work → Online Mode → Push → More offline → Push again
  - Expected: Seamless switching between modes
  - Result: _______________

### 8.2 State Consistency
- [ ] **After refresh** - Do full workflow, press F5, check state
  - Expected: All data reloaded correctly from backend
  - Result: _______________
- [ ] **After logout/login** - Complete workflow, lock session, login again
  - Expected: Data still available, can continue work
  - Result: _______________
- [ ] **Backend sync** - Do operation in UI, check backend database
  - Expected: Data matches (commit in git, changeset in DB)
  - Result: _______________

---

## Test Result Summary

### Test Execution

| Suite | Tests | Passed | Failed | Skipped | Notes |
|-------|-------|--------|--------|---------|-------|
| 1. Offline | 32 | ___ | ___ | ___ | ___ |
| 2. Online | 19 | ___ | ___ | ___ | ___ |
| 3. UI/UX | 15 | ___ | ___ | ___ | ___ |
| 4. Security | 10 | ___ | ___ | ___ | ___ |
| 5. Life View | 8 | ___ | ___ | ___ | ___ |
| 6. Edge Cases | 9 | ___ | ___ | ___ | ___ |
| 7. Cross-Browser | 6 | ___ | ___ | ___ | ___ |
| 8. Integration | 6 | ___ | ___ | ___ | ___ |
| **TOTAL** | **105** | **___** | **___** | **___** | |

### Overall Status
- **Passed:** _____ / 105
- **Failed:** _____ / 105
- **Success Rate:** _____%

### Known Issues Found
1. _____________________________________________
2. _____________________________________________
3. _____________________________________________

### Sign-Off
- **Tester Name:** _______________________
- **Test Date:** _______________________
- **Status:** ☐ Pass ☐ Pass with Issues ☐ Fail
- **Recommendation:** ☐ Deploy ☐ Deploy with Caution ☐ Do Not Deploy

---

**END OF CHECKLIST**

For additional details, see V041_UI_COMPLETE.md
