# ✅ Marcus v0.44-alpha — Missions + Boxes Data Model — COMPLETE

**Status:** 🔒 **LOCKED**
**Delivery Date:** 2026-01-11
**Phase:** v0.44-alpha (1 of 3)
**Previous:** v0.43 (PR Autopilot)

---

## Overview

Marcus v0.44-alpha establishes the **Missions + Boxes workflow engine** data model. This is the foundation for turning Marcus into a "Flight Deck" for managing life workflows, not just a tutoring app.

**Key Innovation:** Everything becomes a mission made of boxes. Each box creates artifacts, updates state, or produces verifiable claims.

---

## What Was Delivered

### 1. Database Models (5 new tables)

**Core Tables:**
- `missions` - Workflow containers (exam_prep, code_review, research)
- `mission_boxes` - Workflow nodes (inbox, extract, ask, practice, checker, citations)
- `mission_artifacts` - Box outputs (documents, QA, sessions, verifications, citations, notes)
- `practice_sessions` - Practice question sets
- `practice_items` - Individual questions with state tracking

**Enums:**
- `MissionState`: draft, active, blocked, done
- `BoxState`: idle, ready, running, blocked, done, error

### 2. MissionService

**Location:** [marcus_app/services/mission_service.py](marcus_app/services/mission_service.py)

**Capabilities:**
- `create_mission()` - Manual mission creation
- `list_missions()` - Filter by class/type/state
- `get_mission()` - Fetch single mission
- `get_mission_detail()` - Full detail with boxes/artifacts/sessions
- `update_mission_state()` - State transitions
- `delete_mission()` - Cascade delete
- `create_from_template()` - Template-based creation

**Templates Implemented:**
- ✅ **exam_prep** - 6 boxes (Inbox → Extract → Ask → Practice → Checker → Citations)
- 🔲 **code_review** - Stub (v0.44-beta+)
- 🔲 **research** - Stub (v0.44-beta+)

### 3. API Endpoints

**Location:** [marcus_app/backend/mission_routes.py](marcus_app/backend/mission_routes.py)

**Endpoints:**
- `POST /api/missions/create` - Create mission manually
- `POST /api/missions/create-from-template` - Create from template
- `GET /api/missions` - List missions (filterable)
- `GET /api/missions/{id}` - Get mission detail
- `PATCH /api/missions/{id}` - Update state
- `DELETE /api/missions/{id}` - Delete mission
- `GET /api/missions/{id}/boxes/{box_id}` - Get box detail (read-only in alpha)

**Security:**
- All endpoints require authentication (stub in alpha)
- Data stored in encrypted volume
- No background execution

### 4. Integration Tests

**Location:** [tests/test_v044_alpha_missions.py](tests/test_v044_alpha_missions.py)

**Tests (8/8 passing):**
- ✅ Mission CRUD operations
- ✅ Mission listing with filters
- ✅ Mission detail retrieval
- ✅ State transitions
- ✅ Mission deletion with cascades
- ✅ Exam prep template creation
- ✅ Invalid template error handling
- ✅ Box ordering preservation

---

## Exam Prep Mission Template

When you create an exam prep mission, Marcus creates 6 boxes in this order:

| Order | Box Type | Purpose | State |
|-------|----------|---------|-------|
| 0 | **InboxBox** | Ingest PDFs, screenshots, materials | idle |
| 1 | **ExtractBox** | Chunk and index documents | idle |
| 2 | **AskBox** | Scoped Q&A with citations | idle |
| 3 | **PracticeBox** | Generate practice questions | idle |
| 4 | **CheckerBox** | Verify answers, create claims | idle |
| 5 | **CitationsBox** | Show sources used | idle |

**Box execution in v0.44-beta.**

---

## Data Model Details

### Mission

```python
class Mission(Base):
    id: int
    name: str  # "PHYS214 Midterm Prep"
    mission_type: str  # exam_prep, code_review, research
    state: str  # draft, active, blocked, done
    class_id: int | None
    assignment_id: int | None
    metadata_json: str | None
    created_at: datetime
    updated_at: datetime

    # Relationships
    boxes: List[MissionBox]
    artifacts: List[MissionArtifact]
    practice_sessions: List[PracticeSession]
```

### MissionBox

```python
class MissionBox(Base):
    id: int
    mission_id: int
    box_type: str  # inbox, extract, ask, practice, checker, citations
    order_index: int  # Execution order
    state: str  # idle, ready, running, blocked, done, error
    config_json: str  # Box-specific settings
    last_run_at: datetime | None
    last_error: str | None
    position_json: str | None  # For v0.45 canvas (unused in alpha)
    created_at: datetime
    updated_at: datetime

    # Relationships
    mission: Mission
    artifacts: List[MissionArtifact]
```

### MissionArtifact

```python
class MissionArtifact(Base):
    id: int
    mission_id: int
    box_id: int | None  # Null if ingested externally
    artifact_type: str  # document, qa, practice_session, verification, citation, note
    title: str
    content_json: str  # Artifact data (JSON or markdown)
    source_refs_json: str  # Citations/chunk IDs/artifact IDs
    created_at: datetime

    # Relationships
    mission: Mission
    box: MissionBox | None
```

### PracticeSession

```python
class PracticeSession(Base):
    id: int
    mission_id: int
    state: str  # active, completed
    score_json: str  # {attempted: N, correct: N, incorrect: N}
    notes: str | None
    created_at: datetime
    completed_at: datetime | None

    # Relationships
    mission: Mission
    items: List[PracticeItem]
```

### PracticeItem

```python
class PracticeItem(Base):
    id: int
    session_id: int
    prompt_md: str  # Question text (markdown)
    expected_answer: str | None
    user_answer: str | None
    state: str  # unanswered, correct, incorrect
    checks_json: str  # Unit checks, reasoning checks
    citations_json: str  # Citations for this question
    created_at: datetime
    answered_at: datetime | None

    # Relationships
    session: PracticeSession
```

---

## API Examples

### Create Exam Prep Mission

**Request:**
```bash
POST /api/missions/create-from-template
Content-Type: application/json

{
  "template_name": "exam_prep",
  "mission_name": "PHYS214 Midterm Prep",
  "class_id": 1,
  "assignment_id": null
}
```

**Response:**
```json
{
  "id": 1,
  "name": "PHYS214 Midterm Prep",
  "mission_type": "exam_prep",
  "state": "draft",
  "boxes": [
    {"id": 1, "type": "inbox", "order": 0, "state": "idle"},
    {"id": 2, "type": "extract", "order": 1, "state": "idle"},
    {"id": 3, "type": "ask", "order": 2, "state": "idle"},
    {"id": 4, "type": "practice", "order": 3, "state": "idle"},
    {"id": 5, "type": "checker", "order": 4, "state": "idle"},
    {"id": 6, "type": "citations", "order": 5, "state": "idle"}
  ],
  "created_at": "2026-01-11T15:30:00Z"
}
```

### List Missions

**Request:**
```bash
GET /api/missions?mission_type=exam_prep&state=active
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "PHYS214 Midterm Prep",
    "mission_type": "exam_prep",
    "state": "active",
    "class_id": 1,
    "assignment_id": null,
    "box_count": 6,
    "artifact_count": 0,
    "created_at": "2026-01-11T15:30:00Z",
    "updated_at": "2026-01-11T15:30:00Z"
  }
]
```

### Get Mission Detail

**Request:**
```bash
GET /api/missions/1
```

**Response:**
```json
{
  "mission": {
    "id": 1,
    "name": "PHYS214 Midterm Prep",
    "mission_type": "exam_prep",
    "state": "draft",
    "class_id": 1,
    "assignment_id": null,
    "created_at": "2026-01-11T15:30:00Z",
    "updated_at": "2026-01-11T15:30:00Z"
  },
  "boxes": [
    {
      "id": 1,
      "type": "inbox",
      "order": 0,
      "state": "idle",
      "last_run_at": null,
      "last_error": null
    },
    ...
  ],
  "artifacts": [],
  "practice_sessions": []
}
```

---

## Verification

**Run tests:**
```bash
python tests/test_v044_alpha_missions.py
```

**Expected output:**
```
======================================================================
MARCUS v0.44-ALPHA INTEGRATION TESTS
======================================================================
[PASS] test_create_mission
[PASS] test_list_missions
[PASS] test_get_mission_detail
[PASS] test_update_mission_state
[PASS] test_delete_mission
[PASS] test_create_exam_prep_template
[PASS] test_invalid_template
[PASS] test_box_order_preserved
======================================================================
RESULTS: 8 passed, 0 failed
======================================================================
```

---

## Acceptance Criteria

**v0.44-alpha deliverables:**
- [x] 5 new database tables (missions, boxes, artifacts, sessions, items)
- [x] MissionService with CRUD operations
- [x] Template creation (exam_prep with 6 boxes)
- [x] API endpoints (7 routes)
- [x] Router registration in main API
- [x] Integration tests (8/8 passing)
- [x] Documentation

**Not in v0.44-alpha (deferred to beta/final):**
- [ ] Box execution (run_box endpoint)
- [ ] InboxBox/ExtractBox/AskBox implementations
- [ ] PracticeBox/CheckerBox/CitationsBox implementations
- [ ] Mission detail UI
- [ ] Practice session UI
- [ ] Life Graph integration

---

## What Changed from v0.43

| Component | v0.43 | v0.44-alpha |
|-----------|-------|-------------|
| **Data model** | PR Autopilot service | + 5 mission/box tables |
| **Workflow engine** | None | Mission/box framework |
| **Templates** | None | exam_prep template |
| **API** | PR autopilot | + 7 mission endpoints |

---

## Database Migration

Marcus uses SQLAlchemy's `Base.metadata.create_all()`, so new tables are created automatically on next startup.

**No manual migration required.**

To initialize database:
```python
from marcus_app.core.database import init_db
init_db()
```

---

## Known Limitations

1. **No box execution** - Boxes exist but can't be run (v0.44-beta)
2. **No UI** - API-only (v0.44-beta adds UI)
3. **Auth stub** - Authentication not enforced in alpha
4. **Single template** - Only exam_prep fully implemented

---

## Design Decisions

### Why "Missions + Boxes" not "Workflows + Nodes"?

**Emotional framing matters.** "Mission" feels like ops, not homework. "Box" feels like a tool, not an abstract concept.

### Why separate artifacts from boxes?

**Artifacts are first-class entities.** They can be ingested externally (uploaded PDFs) or produced by boxes (QA sessions). Boxes operate on artifacts.

### Why order_index instead of edges?

**v0.44-alpha assumes sequential execution.** Graph edges come in v0.45 with canvas UI. For now, boxes run in order.

### Why separate practice sessions/items?

**Reusable pattern.** Practice sessions are artifacts produced by PracticeBox, consumed by CheckerBox. Items track individual question state.

---

## Next Steps (v0.44-beta)

v0.44-beta will implement:

1. **BoxRunner framework** - Execute boxes with state transitions
2. **3 box implementations:**
   - InboxBox (link existing artifacts)
   - ExtractBox (chunk + index via existing pipeline)
   - AskBox (retrieval + cited Q&A)
3. **Minimal mission detail UI** - List boxes, run boxes, view outputs
4. **Integration tests** - End-to-end mission execution

---

## ✅ v0.44-alpha STATUS: LOCKED

Marcus now has a workflow engine data model. Missions can be created, boxes exist, state is tracked.

**Production-Ready:** Data model only
**API-Ready:** Yes (read-only + template creation)
**UI-Ready:** No (v0.44-beta)
**Box Execution:** No (v0.44-beta)

---

**Signed:** Claude Sonnet 4.5
**Date:** 2026-01-11
**Version:** v0.44-alpha-LOCKED
