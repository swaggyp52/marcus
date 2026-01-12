# V0.49: Final Lock - What Marcus Is & What It Isn't

**Document Type:** Canonical System Definition  
**Status:** ✅ LOCKED (No changes post-v0.49)  
**Audience:** Architects, long-term planners, future maintainers  
**Purpose:** Define permanent boundaries and extension points  

---

## 📌 What Marcus IS

### A Unified Daily Workflow OS

Marcus is a **single, offline-first command center** for managing:
- ✅ Next-action thinking (capture → clarify → execute)
- ✅ Time blocking (missions with linked boxes)
- ✅ Pattern visibility (life view graphs)
- ✅ Trust-safe undo (10-second revert window)
- ✅ Deterministic outputs (same DB state = same response always)

**You open it. You type. It handles the rest.**

---

### Keyboard-First, Not Mouse-Free

- ✅ Hotkeys for all common actions (j/k navigate, d delete, a accept, s snooze)
- ✅ Agent chat as primary interface
- ✅ Tabs/nav available but optional
- ✅ No forced mouse usage, but mouse works everywhere

---

### Offline-First, No Background Sync

- ✅ Starts with SQLite local-only
- ✅ All data remains on user's machine
- ✅ No cloud sync (intentional)
- ✅ No background processes
- ✅ Every action is explicit (user-initiated)

---

### Deterministic & Auditable

- ✅ Same database state → same response always
- ✅ Language consistent (same action type → same message)
- ✅ Defaults opinionated but overrideable
- ✅ Audit trail logs every action
- ✅ Undo tracks all state changes

---

### Explicit Actions Only

- ✅ User types or clicks (no automation)
- ✅ Agent suggests, user decides
- ✅ No scheduled background tasks
- ✅ No predictive actions
- ✅ No AI triggering anything without user consent

---

### Trust-Safe by Design

- ✅ Never deletes permanently (undo available)
- ✅ Never silently modifies items
- ✅ Shows all state changes clearly
- ✅ Consistent system voice (no confusion)
- ✅ Progressive disclosure (only shows complexity when needed)

---

## ❌ What Marcus IS NOT

### ❌ NOT Multi-User

- No collaboration
- No shared projects
- No team features
- No permissions system
- One person, one Marcus instance

**Reason:** Personal OS, not enterprise platform.

---

### ❌ NOT AI-Powered

- No ML models
- No neural networks
- No external LLM calls
- No "intelligent" automation
- Agent is rule-based (if-then logic only)

**Reason:** Trust requires understanding. Determinism requires no black boxes.

---

### ❌ NOT 3D/Visual

- No kanban boards
- No timeline visualizations
- No calendar widgets
- No 3D space exploration
- Text-primary interface

**Reason:** Keyboard-first means text-first. Text scales better.

---

### ❌ NOT Synced Across Devices

- No mobile app
- No web sync
- No iCloud/Dropbox integration
- No multi-device seamless experience

**Reason:** Offline-first + determinism = local-only. Syncing creates conflict complexity.

---

### ❌ NOT Extensible Runtime

- No plugins
- No custom scripting
- No webhook system
- No external integrations

**Reason:** Determinism requires controlled inputs. Open system breaks predictability.

---

### ❌ NOT a Scheduler

- No auto-scheduling
- No calendar integration
- No "find common time"
- No recurring event templates

**Reason:** Marcus handles tasks, not calendar. Different mental models.

---

### ❌ NOT a Social Network

- No activity feeds
- No sharing
- No public profiles
- No gamification

**Reason:** Personal workflow tool, not social platform.

---

### ❌ NOT a Document Editor

- No rich text
- No file attachments
- No embedded media
- No formatting options

**Reason:** Marcus links to files; doesn't contain them. Points to reality, doesn't duplicate it.

---

## 🧩 Extension Points (Forever Open)

These CAN change without breaking Marcus core:

### 1. Custom Agent Intents

**Add new command types:**
```python
# marcus_app/agent/intents/
# - custom_project_summary.py
# - custom_energy_level.py
# - custom_meeting_prep.py
```

**Rules:**
- Must return same structure (ActionType + items list)
- Must be deterministic
- Must not require external services
- Must fit in agent_chat UI

---

### 2. Custom Context Classes

**Add new context types:**
```python
# marcus_app/core/contexts.py - add to CONTEXT_TYPES
contexts = [
    "PHYS214",  # existing course
    "side_projects",  # new custom
    "health",  # new custom
]
```

**Rules:**
- Must integrate with items.context field
- Must work with default system (last_active_context)
- Must be queryable in Life View
- User can create any string (schema-less)

---

### 3. Custom Box Templates

**Add new mission box types:**
```python
# marcus_app/core/missions/templates.py
TEMPLATES = {
    "14_day_sprint": {...existing...},
    "weekly_review": {...new...},
    "exam_cram": {...new...},
}
```

**Rules:**
- Must follow mission schema (boxes list, total duration)
- Must integrate with mission state machine
- Must work with "last_used_template" default

---

### 4. Custom Filters in Life View

**Add new graph visualizations:**
```python
# marcus_app/services/life_view_service.py
# Add new filter methods:
# - filter_by_energy_level()
# - filter_by_context_cluster()
# - filter_by_completion_rate()
```

**Rules:**
- Must work with existing items data
- Must return visualizable graph structure
- Must respect progressive disclosure (only show if density > threshold)

---

## 🔒 Permanent Freeze (Forever Locked)

These CANNOT change post-v0.49 without breaking compatibility:

### Schema Freeze
**Database models (immutable):**
- `items` table (id, type, title, context, state, due_date, ...)
- `missions` table (id, title, boxes, state, created_at, ...)
- `boxes` table (id, mission_id, title, status, ...)
- `contexts` table (id, name, frequency, last_used, ...)
- `undo_events` table (id, action, data, timestamp, ...)

**Migration rules:** Only ADD columns, never REMOVE or CHANGE types.

---

### API Endpoints (Immutable)
```
POST /api/suggest
POST /api/accept
POST /api/next
POST /api/undo
POST /api/inbox
GET  /api/items
GET  /api/missions
POST /api/item/{id}/update
POST /api/item/{id}/delete
```

**Extension rule:** New endpoints must not break existing ones.

---

### Agent Intent Types (Fixed at 11)
1. `suggest_next_action`
2. `list_inbox`
3. `show_missions`
4. `add_task`
5. `add_note`
6. `add_file`
7. `update_item`
8. `delete_item`
9. `snooze_item`
10. `undo_last_action`
11. `show_life_view`

**Extension rule:** Create new intents via Custom Intent system, don't modify these.

---

### Item State Machine (Fixed)
```
active → completed
active → snoozed → active
active → blocked → active
snoozed → active
snoozed → completed
blocked → active
blocked → completed
```

**Never add states. Ever.**

---

### Determinism Guarantee
- Same database state must produce same response
- No randomness in output
- No timestamp-dependent rendering
- Same user action → same message always

**This is non-negotiable.**

---

## 📋 What's Intentionally Deferred Forever

These decisions are **permanent NO's**:

| Feature | Reason | When |
|---------|--------|------|
| Multi-user collaboration | Would require sync engine (breaks determinism) | Never |
| Cloud sync | Would require conflict resolution (violates trust) | Never |
| AI/ML predictions | Would require black boxes (breaks understanding) | Never |
| Real-time scheduling | Too much complexity for daily tool | Never |
| Mobile apps | Would require sync system first | Never |
| Plugins/extensions | Would break determinism guarantee | Never |
| Websocket streaming | Would enable background actions | Never |
| Calendar integration | Different mental model (Marcus is task-first) | Never |
| Rich text editing | Would make Marcus a document tool | Never |
| Performance rewrites | Already fast enough (SQLite sufficient) | Never |

---

## 🎯 After v0.49: What Happens Next

### Short Term (Months)
- Bug fixes only
- Performance tweaks if needed
- User-reported fixes

### Medium Term (Months-Years)
- Maintenance mode
- Documentation updates
- No feature development

### Long Term (Years+)
- If changes are needed, **new project**
- Don't fork/extend Marcus
- Start fresh with lessons learned

### Philosophy
**Marcus is frozen in time as a complete, working system.** Future work that requires fundamental changes is a new project, not an extension.

---

## 🗂️ How to Extend Marcus (Without Breaking It)

### DO ✅
- Add custom agent intents
- Create custom contexts
- Add new mission templates
- Add graph filters to Life View
- Fix bugs without changing schema
- Improve performance without changing behavior
- Add documentation

### DON'T ❌
- Modify database schema
- Remove API endpoints
- Add background processes
- Create new item states
- Add AI/ML logic
- Break determinism guarantee
- Change system voice patterns
- Require external services

---

## 📊 System Boundaries (For Architects)

```
┌─────────────────────────────────────────────┐
│           MARCUS v0.49 CORE                │
│                                             │
│  ✓ Task/Note/File/Mission management      │
│  ✓ Next-action ranking                    │
│  ✓ Trust-safe undo                        │
│  ✓ Audit trail                            │
│  ✓ Deterministic responses                │
│  ✓ Offline-first operations               │
│                                             │
│         ↓ EXTENSION POINTS ↓               │
│                                             │
│  • Custom agent intents (add commands)    │
│  • Custom contexts (add categories)       │
│  • Mission templates (add workflows)      │
│  • Life view filters (add visualizations) │
│                                             │
│      ↓ FOREVER FROZEN ↓                   │
│                                             │
│  ✗ Multi-user features                    │
│  ✗ Cloud sync                             │
│  ✗ AI/ML models                           │
│  ✗ Mobile apps                            │
│  ✗ External integrations                  │
│  ✗ New item states                        │
│  ✗ Background processes                   │
│                                             │
└─────────────────────────────────────────────┘
```

---

## 🎯 For Maintainers (Future You)

### If Asked: "Can we add X?"

**Feature: Multi-user collaboration**  
Answer: "No. Marcus is single-user by design. Different project."

**Feature: Mobile sync**  
Answer: "No. Would require cloud backend. Different project."

**Feature: AI predictions**  
Answer: "No. Would break determinism. Different project."

**Feature: New item state**  
Answer: "No. Would require schema change. Defer or new project."

**Feature: Custom script plugins**  
Answer: "No. Would break determinism. Use custom intent system instead."

**Feature: Performance rewrite**  
Answer: "Skip it. Already fast. Premature optimization."

**Feature: Rich text in notes**  
Answer: "No. Would make Marcus a document tool. Out of scope."

**New urgency: "We REALLY need X"**  
Answer: "Then it's a new project. Marcus doesn't change post-v0.49."

---

## ✅ Your Marcus Contract (v0.49 → Forever)

### Marcus Promises
- ✅ Will work offline
- ✅ Will undo deletions
- ✅ Will be keyboard-fast
- ✅ Will give consistent responses
- ✅ Will never auto-delete
- ✅ Will never break your data
- ✅ Will never require cloud
- ✅ Will never add background tasks

### You Promise
- ✅ Will not expect mobile access
- ✅ Will not expect multi-user features
- ✅ Will not expect AI/ML logic
- ✅ Will not expect cloud sync
- ✅ Will not ask for real-time scheduling

**This is the contract. It's locked. It's final.**

---

## 🎊 The Meaning of v0.49

**Before v0.49:** Marcus was "in development"  
**After v0.49:** Marcus is "in use"

The tool doesn't change. The relationship to the tool changes.

You stop thinking "What should Marcus do next?"  
You start thinking "How do I use Marcus for this?"

---

## 📝 Document Inventory

| Document | Purpose | Audience |
|----------|---------|----------|
| [V049_MARCUS_MODE_COMPLETE.md](V049_MARCUS_MODE_COMPLETE.md) | User guide to new features | Everyone |
| [V049_FINAL_LOCK.md](V049_FINAL_LOCK.md) | This file: canonical system def | Architects |
| V049_SCHEMA_FROZEN.md | Database schema freeze doc | Developers |
| V049_EXTENSION_POINTS.md | How to extend safely | Developers |
| [V049_HOW_TO_USE.md](#) | Daily workflows | Users |
| [V049_KEYBOARD_REFERENCE.md](#) | Hotkey guide | Users |

---

## 🏁 Closing Statement

**Marcus v0.49 is a complete, stable, offline-first daily workflow OS.**

It is not being built anymore. It is being used.

Extension is allowed within defined boundaries. Fundamental changes become new projects.

**This document defines those boundaries, forever.**

---

**Version:** 0.49  
**Status:** ✅ FINAL & LOCKED  
**Effective Date:** January 11, 2026  
**Review Schedule:** Never (locked permanently)  

**No changes post-v0.49. This is final.**
