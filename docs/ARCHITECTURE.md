# Marcus Architecture

## System Overview

Marcus is a local-first academic operating environment designed with a clear separation of concerns, offline-first architecture, and strict trust boundaries.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────┐
│                        User Browser                          │
│                   (HTML/CSS/JavaScript)                      │
└──────────────────────┬──────────────────────────────────────┘
                       │ HTTP/REST API
                       │
┌──────────────────────▼──────────────────────────────────────┐
│                    FastAPI Backend                           │
│  ┌────────────────────────────────────────────────────────┐ │
│  │                  API Endpoints                         │ │
│  │  - Classes    - Artifacts    - Plans                   │ │
│  │  - Assignments - Extraction  - Exports                 │ │
│  └─────────┬──────────────────────────────┬───────────────┘ │
│            │                               │                 │
│  ┌─────────▼─────────┐         ┌─────────▼─────────┐       │
│  │   Services Layer  │         │   Core Models     │       │
│  │  - FileService    │         │   (SQLAlchemy)    │       │
│  │  - ExtractionSvc  │         │   - Class         │       │
│  │  - PlanService    │         │   - Assignment    │       │
│  │  - ExportService  │         │   - Artifact      │       │
│  └─────────┬─────────┘         │   - ExtractedText │       │
│            │                    │   - Plan          │       │
│            │                    │   - AuditLog      │       │
│            │                    └─────────┬─────────┘       │
│            │                              │                 │
└────────────┼──────────────────────────────┼─────────────────┘
             │                              │
             │                              │
     ┌───────▼────────┐           ┌────────▼────────┐
     │  File System   │           │  SQLite Database│
     │                │           │                 │
     │  vault/        │           │  storage/       │
     │  projects/     │           │  marcus.db      │
     │  exports/      │           │                 │
     └────────────────┘           └─────────────────┘
```

## Component Layers

### 1. Frontend Layer

**Technology**: Vanilla HTML/CSS/JavaScript

**Responsibilities**:
- Render user interface
- Handle user interactions
- Make API calls to backend
- Display data from API responses

**Files**:
- [marcus_app/frontend/index.html](../marcus_app/frontend/index.html)
- [marcus_app/frontend/app.js](../marcus_app/frontend/app.js)

**Why not React/Vue?**
- Simplicity: No build step, no bundling
- Speed: Faster to develop MVP
- Local-first: Works without npm/node dependencies
- Easy to understand and modify

### 2. API Layer

**Technology**: FastAPI

**Responsibilities**:
- HTTP request handling
- Request validation (Pydantic schemas)
- Response serialization
- Routing
- Error handling

**Files**:
- [marcus_app/backend/api.py](../marcus_app/backend/api.py)

**Endpoints**:
- `/api/status` - System status
- `/api/online-mode` - Toggle online mode
- `/api/classes` - Class management
- `/api/assignments` - Assignment management
- `/api/artifacts` - File uploads
- `/api/extract` - Text extraction
- `/api/plans` - Plan generation
- `/api/audit-logs` - Security audit logs
- `/api/export` - Export bundles

### 3. Core Layer

**Technology**: SQLAlchemy ORM

**Responsibilities**:
- Data modeling
- Database schema definition
- Database connections
- Session management

**Files**:
- [marcus_app/core/models.py](../marcus_app/core/models.py) - ORM models
- [marcus_app/core/database.py](../marcus_app/core/database.py) - DB setup
- [marcus_app/core/schemas.py](../marcus_app/core/schemas.py) - Pydantic schemas

**Data Models**:
- **Class**: Course information
- **Assignment**: Assignment details
- **Artifact**: File metadata
- **ExtractedText**: Extracted content
- **Plan**: Generated plans
- **AuditLog**: Security logging
- **SystemConfig**: App settings

### 4. Services Layer

**Responsibilities**:
- Business logic
- File operations
- Text extraction
- Plan generation
- Export creation

**Files**:
- [marcus_app/services/file_service.py](../marcus_app/services/file_service.py)
- [marcus_app/services/extraction_service.py](../marcus_app/services/extraction_service.py)
- [marcus_app/services/plan_service.py](../marcus_app/services/plan_service.py)
- [marcus_app/services/export_service.py](../marcus_app/services/export_service.py)

#### FileService

- Handles file uploads
- Computes SHA-256 hashes
- Stores files in vault
- Determines file types
- Creates artifact records

#### ExtractionService

- Extracts text from PDFs (pypdf)
- OCR from images (tesseract)
- Text from DOCX (python-docx)
- Plain text from code files
- Error handling and logging

#### PlanService

- Generates structured plans
- Analyzes assignment context
- Creates step-by-step breakdowns
- Estimates effort
- Identifies risks and assumptions
- Template-based (upgradeable to LLM)

#### ExportService

- Creates ZIP bundles
- Generates markdown exports
- Includes plans, files, extracted text
- Creates manifest.json
- Timestamped exports

### 5. Storage Layer

**Technologies**:
- SQLite (structured data)
- File system (binary files)

**Directories**:

```
vault/          # Immutable uploaded files (content-addressed)
  ├── {hash}.pdf
  ├── {hash}.png
  └── {hash}.docx

projects/       # Per-class workspaces
  ├── 26SPECE34701/
  └── 26SPBIOL10302/

exports/        # Generated export bundles
  ├── Assignment_Name_20260110_123456.zip
  └── ...

storage/        # SQLite database
  └── marcus.db
```

## Data Flow Examples

### File Upload Flow

1. User selects file in browser
2. Frontend sends multipart/form-data POST to `/api/assignments/{id}/artifacts`
3. API receives upload, extracts bytes
4. FileService:
   - Computes SHA-256 hash
   - Determines file type from extension
   - Saves to vault/{hash}.{ext}
   - Creates Artifact record in DB
5. AuditLog entry created
6. API returns Artifact JSON
7. Frontend updates UI

### Text Extraction Flow

1. User clicks "Extract Text" on an artifact
2. Frontend POST to `/api/artifacts/{id}/extract`
3. API loads Artifact from DB
4. ExtractionService:
   - Checks file type
   - Routes to appropriate extractor (PDF/OCR/DOCX/Plain)
   - Extracts text
   - Creates ExtractedText record
   - Stores extraction status and errors
5. AuditLog entry created
6. API returns ExtractedText JSON
7. Frontend displays content

### Plan Generation Flow

1. User clicks "Generate Plan"
2. Frontend POST to `/api/plans` with assignment_id
3. API checks online mode status
4. API loads Assignment, Artifacts, ExtractedTexts
5. PlanService:
   - Analyzes available context
   - Builds template-based plan
   - Creates steps, materials list, outline
   - Estimates effort and confidence
   - Identifies risks and assumptions
   - Creates Plan record
6. AuditLog entry created
7. API returns Plan JSON
8. Frontend renders plan sections

## Trust Boundary

### Offline Zone (Default)

- File operations
- Database operations
- Text extraction
- Plan generation (template-based)
- All core features

### Online Zone (Gated)

- Must be explicitly enabled via toggle
- Every online action logged to audit_log
- Future: Web search, LLM API calls
- Can be disabled any time

### Audit Trail

Every significant action creates an AuditLog entry:

```python
{
    "timestamp": "2026-01-10T12:34:56",
    "event_type": "file_uploaded",
    "online_mode": "offline",
    "user_action": "Uploaded file: assignment.pdf",
    "metadata": {...}
}
```

## Extensibility Points

### 1. LLM Integration

Current: Template-based plan generation
Future:
- Local LLM via Ollama/llama.cpp
- Optional cloud LLM with explicit permission
- Prompt templates in `marcus_app/prompts/`

### 2. Online Research

Current: Online mode toggle infrastructure
Future:
- Web search with domain allowlist
- Citation tracking
- Result caching
- Confidence scoring

### 3. Export Formats

Current: ZIP bundles with markdown
Future:
- PDF generation
- DOCX generation
- HTML reports
- Custom templates

### 4. File Types

Current: PDF, images, DOCX, text, code
Future:
- PowerPoint/slides
- Excel/CSV
- Audio transcription
- Video frame extraction

## Performance Considerations

### Database

- SQLite is sufficient for single-user local app
- Indexed on common query fields
- Connection pooling via SQLAlchemy

### File Storage

- Content-addressed (hash-based) prevents duplicates
- No file size limits enforced (trust user)
- Extraction happens on-demand, not automatically

### Frontend

- Vanilla JS - no framework overhead
- Minimal CSS - fast rendering
- API calls are lazy-loaded per tab

## Scalability

Marcus is designed for **single-user, local operation**. It is NOT designed for:
- Multi-user
- Concurrent access
- Network deployment
- Large teams

If you need those, consider:
- Move to PostgreSQL
- Add authentication
- Implement user management
- Deploy with nginx/gunicorn

## Testing Strategy

Current: Manual testing
Future (v0.2+):
- Unit tests for services
- Integration tests for API endpoints
- E2E tests for critical flows
- Test fixtures with sample data

## Deployment

Current: Local only via `run.bat`
Future options:
- Docker container
- Standalone executable (PyInstaller)
- Desktop app wrapper (Electron/Tauri)

---

**Key Design Principles**:
1. Local-first, offline-capable
2. Clear trust boundaries
3. Explicit over implicit
4. Simple before clever
5. Privacy by default
6. Fail safely and visibly
