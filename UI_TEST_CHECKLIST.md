# Marcus UI - Interactive Test Checklist

**Run this immediately after starting Marcus.exe to verify all features work**

---

## Pre-Test Setup
- [ ] Mount VeraCrypt to M:\Marcus (or simulate with env var)
- [ ] Run: `dist\Marcus.exe`
- [ ] Wait 3-5 seconds for window to open
- [ ] Open browser DevTools (F12) for Network inspection

---

## Phase 1: Login & Dashboard Load

### Login Page (Initial)
- [ ] UI opens to login.html
- [ ] Login form has username and password fields
- [ ] Password field is masked (not visible)
- [ ] "Login" button is clickable
- [ ] Credentials from previous session work
- [ ] **Incorrect credentials** show error message (if expected)
- [ ] **Correct credentials** allow login

### Home Dashboard (After Login)
- [ ] Page title shows "🏠 Home"
- [ ] 4 stat cards visible and readable:
  - [ ] Classes count
  - [ ] Assignments count
  - [ ] Due This Week count
  - [ ] Inbox badge count
- [ ] Dashboard loads without console errors
- [ ] **Check Network tab**: See GET `/api/health`, `/api/classes`, `/api/assignments`, `/api/inbox` calls
- [ ] No blank sections or loading spinners stuck

---

## Phase 2: Sidebar Navigation

### Visual Check
- [ ] Sidebar visible on left with 8 nav items
- [ ] Current tab ("Home") has highlight/active state
- [ ] Tab icons visible (or text labels clear)
- [ ] Sidebar doesn't overlap main content

### Click Each Tab
#### Inbox Tab
- [ ] Page title changes to "📥 Inbox"
- [ ] Inbox tab highlight updates in sidebar
- [ ] List of inbox items appears (or "No items" message if empty)
- [ ] Items show type badge (e.g., "message", "notification")
- [ ] **Network**: GET `/api/inbox` call visible

#### Classes Tab
- [ ] Page title: "📖 My Classes"
- [ ] List of courses appears (or "No classes" if empty)
- [ ] Each class shows name, term, credits
- [ ] "Add Class" button visible and clickable
- [ ] **Network**: GET `/api/classes` call visible

#### Assignments Tab
- [ ] Page title: "✓ Assignments"
- [ ] List with due dates appears
- [ ] Color coding: Red for overdue, Yellow for due soon, Green for future
- [ ] "Add Assignment" button visible
- [ ] **Network**: GET `/api/assignments` call visible

#### Quick Add Tab
- [ ] Page title: "➕ Quick Add"
- [ ] Form with input fields appears
- [ ] Text input for new item visible
- [ ] "Add" button clickable
- [ ] (Clicking "Add" should POST to `/api/inbox`)

#### Search Tab
- [ ] Page title: "🔍 Search"
- [ ] Search input field visible
- [ ] Type text → results filter across classes/assignments/inbox
- [ ] Clicking result highlights it
- [ ] (No backend call needed; client-side filtering)

#### Missions Tab
- [ ] Page title: "🎯 Missions"
- [ ] Tab loads without error
- [ ] (May be empty if no backend missions endpoint)

#### Audit Tab
- [ ] Page title: "📋 Audit Log"
- [ ] Tab loads without error
- [ ] (May be empty if no backend audit endpoint)

---

## Phase 3: Modal Dialogs

### Upload Syllabi Modal
- [ ] Find "Upload Syllabi" button (usually on Classes or Inbox tab)
- [ ] Click it → Modal opens with title "Upload Syllabi"
- [ ] File input field appears
- [ ] "Choose File" button clickable
- [ ] "Upload" and "Cancel" buttons visible
- [ ] Click "Cancel" → modal closes
- [ ] Modal doesn't prevent interaction (not fullscreen overlay)

### Add Class Modal
- [ ] Find "Add Class" button
- [ ] Click → Modal opens with title "Add Class"
- [ ] Form fields appear (name, term, credits, instructor)
- [ ] "Save" and "Cancel" buttons clickable
- [ ] Click "Cancel" → modal closes without saving
- [ ] (Clicking "Save" should POST to `/api/classes` if endpoint exists)

### Other Modals (similar checks)
- [ ] "Add Assignment" → opens modal, has form, Cancel works
- [ ] "Add Mission" → opens modal, has form, Cancel works

---

## Phase 4: Form Interactions

### Test Form Submit (if backend has endpoints)
#### Quick Add Form
1. Click "Quick Add" tab
2. Type text in input field
3. Click "Add" button
4. **Success case**:
   - [ ] Alert message shows "Item added successfully"
   - [ ] Alert auto-dismisses after 5 seconds
   - [ ] Form clears (input field empty)
   - [ ] Inbox updates with new item
5. **Error case** (if backend returns error):
   - [ ] Error message displays in red
   - [ ] Error text shows endpoint response
   - [ ] Alert dismissible via X button

#### Upload Syllabi
1. Click "Upload Syllabi" button
2. Click "Choose File" → file picker opens
3. Select a PDF or document file
4. Click "Upload"
5. **Success**:
   - [ ] "Syllabi uploaded successfully" message
   - [ ] New classes appear in Classes tab
   - [ ] Dashboard stat for Classes increases
6. **Error**:
   - [ ] Error message with reason (file too large, wrong format, etc.)

---

## Phase 5: Responsive Behavior

### Resize Window (Desktop Testing)
- [ ] Drag window edges to make it narrower
- [ ] At ~1024px width:
  - [ ] Layout remains functional (no horizontal scroll needed)
  - [ ] Sidebar may collapse or sidebar items stack
  - [ ] Main content still readable
- [ ] At ~768px width:
  - [ ] Grid layouts adapt (2 columns → 1 column)
  - [ ] Cards stack vertically
  - [ ] Still readable and functional

### Check Console for Errors
- [ ] Open DevTools (F12) → Console tab
- [ ] Perform all test actions above
- [ ] Console should show:
  - [ ] No red "Error" messages
  - [ ] Possible yellow "Warn" messages are acceptable
  - [ ] API responses logged (if fetch debug enabled)
- [ ] **Critical errors** (TypeError, ReferenceError): FAIL test

---

## Phase 6: Stress & Edge Cases

### No Data Handling
- [ ] If Classes tab is empty: "No classes yet" message appears (not blank)
- [ ] If Inbox is empty: "No items" placeholder shows
- [ ] If Assignments empty: "No assignments" placeholder shows
- [ ] No console errors when empty

### Multiple Rapid Clicks
- [ ] Switch tabs quickly 10 times
- [ ] Click buttons rapidly
- [ ] Data still loads correctly (no race conditions)
- [ ] UI remains responsive

### Long Load Times
- [ ] Simulate slow backend (open Network tab, throttle connection)
- [ ] Click a tab
- [ ] Loading spinner or "Loading..." text appears
- [ ] After data arrives, spinner disappears
- [ ] Content displays correctly

---

## Phase 7: Session Management

### Lock Session
- [ ] Find "Lock Session" button (usually in top-right or menu)
- [ ] Click it
- [ ] Redirected to login.html
- [ ] Session is now locked
- [ ] Must re-login to access dashboard
- [ ] **Network**: POST `/api/auth/lock` call visible

### Session Timeout (Optional)
- [ ] If idle for 15 minutes, session auto-locks
- [ ] Redirected to login.html
- [ ] Accessing any page without login redirects to login

---

## Final Checks

### Visual Polish
- [ ] Colors are consistent (indigo/slate theme throughout)
- [ ] No misaligned elements or broken layouts
- [ ] Typography is readable (font sizes, weights consistent)
- [ ] Hover states work (buttons change color on hover)
- [ ] Buttons have visible focus states (for accessibility)

### Performance
- [ ] Dashboard loads in <2 seconds
- [ ] Tab switches are instant (<200ms)
- [ ] Modal opens without lag
- [ ] No stuttering or jank during animations
- [ ] Memory usage stable (check Task Manager)

### No Crashes
- [ ] EXE doesn't crash during tests
- [ ] Closing window gracefully (no forced stop needed)
- [ ] Can restart and re-login
- [ ] All features remain available across sessions

---

## Test Result Summary

**Pass Criteria**: ✅ All checkboxes in Phases 1-5 checked  
**Optional**: Phases 6-7 (stress testing, edge cases, session management)

### Mark Result:
- [ ] **ALL PASS** - UI is production-ready ✅
- [ ] **MINOR ISSUES** - List below, non-blocking
- [ ] **BLOCKERS** - List below, needs fixes

### Issues Found (if any):
```
1. [Issue Title]
   - Description
   - Impact
   - Workaround

2. [Issue Title]
   ...
```

### Notes:
```
[Add any observations, feature requests, or suggestions]
```

---

## Debugging Tips

If tests fail:

1. **Blank Page**: 
   - Check Network tab for 404 errors on `/app.js` or CSS files
   - Verify PyInstaller included frontend assets with `--add-data`

2. **API Calls Fail (404/500)**:
   - Check if backend has the expected endpoints
   - View Network tab response for error details
   - Backend may need migration or endpoint implementation

3. **Form Submission Errors**:
   - Check Console tab for JavaScript errors
   - Verify API endpoint exists and accepts the request format
   - Check server logs for backend errors

4. **Styling Issues**:
   - Clear browser cache (Ctrl+Shift+Delete)
   - Check if CSS file (`/app.js` includes inline CSS) is loading
   - Inspect element (right-click → Inspect) to see applied styles

5. **Performance Issues**:
   - Check Network tab for slow API calls
   - Reduce dataset size for testing (few classes/assignments)
   - Check Task Manager for high CPU/Memory usage

---

**Test Date**: ___________  
**Tester**: ___________  
**Result**: ✅ ✓ ✗  
