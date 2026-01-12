# V0.48 Quick Reference Guide

**For**: Daily Marcus users  
**Audience**: Power users, keyboard-first workflows  
**Time to learn**: 5 minutes

---

## 🎯 Top 5 v0.48 Powers

### 1. Agent Chat History (⬆️⬇️)
```
Type command
Press ⬆️ (up arrow)     ← Recalls last command
Press ⬆️ again          ← Recalls command before that
Press ⬇️ (down arrow)   ← Moves forward in history
Press ⬆️ on empty       ← Loads command for editing
```

**Example:**
```
1. Type: "what's next?"
2. Press: Enter
3. Later, press: ⬆️  
   → "what's next?" reappears, ready to edit
4. Add: " PHYS214"
5. Press: Enter → Executes "what's next? PHYS214"
```

---

### 2. Tab Autocomplete (⭐ Game Changer)
```
Type partial:        Tab presses:         Result:
"PHYS"               Tab                  → "PHYS214"
"add"                Tab                  → "add task"
"what"               Tab                  → "what's next?"
"mark"               Tab                  → "marcus" (project)
```

**Three types of autocomplete:**
- **Classes:** CYENG, ECE347, PHYS214 (matches vault folders)
- **Projects:** marcus, markdown_parser, etc. (from DB)
- **Commands:** "add task", "what's next?", "create mission", etc.

**Keyboard flow (zero mouse):**
```
Type: "PHYS"
Press: Tab → suggests class codes
Press: Down arrow to navigate suggestions
Press: Enter to select → Input becomes "PHYS214"
Press: Space, continue typing...
```

---

### 3. Inbox Hotkeys (j/k Navigation)

#### Single Item Actions
```
Press j or ↓      → Move down to next item
Press k or ↑      → Move up to previous item
Press Enter       → Open current item
Press a           → Accept (move to current project)
Press c           → Change context (pick project)
Press s           → Snooze (specify minutes)
Press p           → Pin/unpin current item
Press d           → Delete with confirmation
```

#### Multi-Select Actions
```
Press Ctrl+Click     → Toggle item selection
Press Shift+Click    → Select range
Press Ctrl+A         → Select all items
```

#### Bulk Hotkeys (on selection)
```
Press a (on selected)  → Accept all selected to default project
Press s (on selected)  → Snooze all (pick duration)
Press p (on selected)  → Pin all selected
Press d (on selected)  → Delete all (with confirmation)
```

**Example Session:**
```
1. In Inbox tab
2. Press j three times            ← Move down 3 items
3. Press Ctrl+A                   ← Select all
4. Press s                        ← Snooze prompt
5. Type: 60                       ← Snooze 60 minutes
6. Press Enter                    ← Confirm

Result: All inbox items snoozed for 1 hour
```

---

### 4. "What's Next?" Smart Ranking

```
Command: "what's next?"

Response shows: Top 3 actionable items ranked by:
1. 🔴 Overdue (due yesterday → most urgent)
2. 🟡 Due soon (0-48 hours)
3. 📌 Pinned items (your priorities)
4. 🔗 Blocked missions (waiting on something)
5. ✅ Active tasks

+ Recommended action button to start
```

**Smart features:**
- Deterministic (same ranking every time)
- No AI randomness (you can predict it)
- Only shows actionable items (due/past due)
- Buttons for quick actions (Open, Mark Done, etc.)

---

### 5. Undo System (10-Second Window)

```
You: Delete item
↓ Toast appears: "Deleted item. [↩️ Undo (9s)]"
↓ Click [Undo] or press Ctrl+Z within 10 seconds
↓ Item restored

OR

Let 10 seconds pass → Undo button disappears → Item permanently deleted
```

**What can undo:**
- ✅ Create item
- ✅ Delete item
- ✅ File item (inbox → context)
- ✅ Snooze item
- ✅ Pin item

**What cannot undo:**
- ❌ Git push / PR operations (online)
- ❌ File edits (use git)

---

## 🎮 Complete Keyboard Map

| Key | In Agent Chat | In Inbox | In Other |
|-----|---------------|----------|----------|
| ⬆️/k | History up | Navigate up | N/A |
| ⬇️/j | History down | Navigate down | N/A |
| Tab | Autocomplete | - | - |
| Enter | Send command | Open item | - |
| Shift+Enter | Newline | - | - |
| a | - | Accept | - |
| c | - | Change context | - |
| s | - | Snooze | - |
| p | - | Pin/unpin | - |
| d | - | Delete | - |
| Ctrl+A | - | Select all | - |
| Ctrl+Click | - | Toggle select | - |
| Shift+Click | - | Range select | - |

---

## 🔐 Trust Bar (Always Visible)

```
📴 OFFLINE | ✓ No background actions | ↩️ Undo (8s) | 📋 Audit Log
```

**Read from left to right:**
1. **Mode Indicator:** 📴 OFFLINE or 🌐 ONLINE
2. **Safety Promise:** ✓ No background actions running
3. **Undo Status:** ↩️ Undo (Xs) - shows seconds remaining
4. **Audit Trail:** 📋 Click to see all actions

**What it means:**
- OFFLINE mode = all features work locally, nothing syncs
- ONLINE mode = careful, operations may sync to external services
- Undo countdown = your safety net (click to reverse last action)
- Audit Log = transparency (what happened? click to see)

---

## 📋 Command Examples

### Create Items
```
"add task PHYS214 Lab Report"
→ Creates task in PHYS214 context

"add note prepare for exam ECE347"
→ Creates note in ECE347 context

"create mission spring semester"
→ Creates new mission with boxes
```

### Query & Filter
```
"what's next?"
→ Top 3 actionable items + recommended action

"show inbox"
→ Open Inbox tab with keyboard ready

"what's due tomorrow?"
→ Filter items due in next 24 hours

"show PHYS214"
→ Filter to PHYS214 context
```

### Organization
```
"snooze PHYS214 Lab 2 hours"
→ Snooze specific item

"pin PHYS214"
→ Mark as priority

"complete PHYS214 Lab Report"
→ Move to completed
```

---

## ⚡ Power User Combos

### Combo 1: Clean Inbox Fast
```
1. Ctrl+A (select all)
2. s (snooze prompt)
3. 60 (60 minutes)
4. Enter
→ Result: All 15 items snoozed for 1 hour
```

### Combo 2: Find & Open
```
1. "show PHYS214" (or type ⬆️ to recall similar)
2. j j j (navigate to item)
3. Enter (open)
→ Result: Item opened in 2 seconds, zero mouse
```

### Combo 3: Recall Last Command & Edit
```
1. ⬆️ (history up)
2. Edit the command
3. Enter (execute)
→ Result: 1 second faster than retyping
```

### Combo 4: Bulk Delete with Reversal
```
1. Ctrl+A (select all)
2. d (delete with confirm)
3. Confirm
4. [↩️ Undo (8s)] appears
5. Click Undo or Ctrl+Z
→ Result: Fear-free bulk operations
```

---

## 🐛 Troubleshooting

### History not loading?
```
Clear browser storage: DevTools → Application → Local Storage → Clear
Reload page (Ctrl+R)
Try again: ⬆️
```

### Autocomplete not working?
```
Check: Is DB running? (backend should be active)
Try: Type more characters (3+ chars)
Check: Browser console for errors (F12 → Console)
```

### Hotkeys not responding in Inbox?
```
Make sure: Inbox tab is active (click on it)
Check: Is text input focused? (click away from input box)
Try: Refresh page (Ctrl+R)
```

### Undo button disappeared?
```
Reason: 10 seconds passed (undo window expired)
Solution: That's correct behavior - no more undo available
Next time: Click Undo faster (or use Ctrl+Z)
```

---

## 💡 Tips & Tricks

### Tip 1: Use Shift+Enter in Chat
```
Great for multi-line commands:
"add task
- Part 1
- Part 2"

Press Shift+Enter to newline
Press Enter when done to send
```

### Tip 2: Navigate Autocomplete with Arrows
```
Type: "ad"
Tab: Shows suggestions
⬇️: Highlight next suggestion
Enter: Select highlighted
```

### Tip 3: Check Undo Status Before Risky Operations
```
Look at Trust Bar: ↩️ Undo (Xs)
If (Xs) shows 0s, your previous action undo expired
Safe to proceed with new operation
```

### Tip 4: Use Pinning for Your Top 3
```
Press p on 3 most important inbox items
They'll rank high in "what's next?"
Pin acts as "I care about this" signal
```

### Tip 5: Snooze Instead of Delete
```
Unsure about deleting?
Press s (snooze) instead of d (delete)
Item comes back in 1 hour - no undo needed
```

---

## 📊 Keyboard Speed Comparisons

| Task | Mouse | Keyboard | Speedup |
|------|-------|----------|---------|
| Snooze 5 inbox items | 15 sec | 3 sec | 5x |
| Open item | 2 sec | 0.5 sec | 4x |
| Accept all inbox | 20 sec | 5 sec | 4x |
| Recall command | 5 sec | 0.2 sec | 25x |
| Delete with undo | 10 sec | 1 sec | 10x |

---

## 🎓 Learning Path (5 Minutes)

**Minute 1:** Learn ⬆️/⬇️ history recall
- Type command, press Enter
- Wait 10 seconds, press ⬆️
- Edit it, press Enter

**Minute 2:** Learn Tab autocomplete
- Type "PHYS", press Tab
- Edit if needed, press Enter

**Minute 3:** Go to Inbox, learn j/k
- Press j, k, j, k to move around
- Press Enter to open an item

**Minute 4:** Learn a/s/d
- Press a to accept (moves to context)
- Press s to snooze
- Press d to delete (watch the undo appear)

**Minute 5:** Learn Ctrl+A bulk
- Press Ctrl+A (select all)
- Press s to snooze all
- Type duration, press Enter

**Result:** You're a Marcus power user!

---

## 🚀 Next Steps

1. **Bookmark this guide** for quick reference
2. **Try Combo 1** (clean inbox in 5 seconds)
3. **Practice history recall** (type something, wait, ⬆️, done)
4. **Pin your top 3 items** and try "what's next?"
5. **Report bugs** if hotkeys feel wrong

---

## FAQ

**Q: Can I customize hotkeys?**  
A: Not in v0.48, but planned for v0.49. Submit preferences!

**Q: What if Undo doesn't work?**  
A: Check if 10 seconds have passed. If so, undo expired. Keep undo button visible - click fast!

**Q: Can I have multi-level undo?**  
A: v0.48 has single undo (last action only). Multi-level undo in v0.49+ based on feedback.

**Q: Works offline?**  
A: Yes! All keyboard features work 100% offline. Only "push" and "PR" need network.

**Q: Can I undo git pushes?**  
A: No - git operations don't use our undo system. Use git commands to revert.

---

## Support

**Found a bug?** → Create issue with keyboard sequence + expected vs actual behavior  
**Want a feature?** → Suggest in feature tracker  
**Have a tip?** → Share in #marcus-tips channel

---

**Last Updated:** v0.48  
**Status:** ✅ Production Ready
