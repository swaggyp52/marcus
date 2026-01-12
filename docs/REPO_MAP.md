# Marcus v052 Repository Map

## Quick Overview

**Marcus** is a **local-first, offline AI research assistant** built as a Windows desktop application. It combines a FastAPI backend with a vanilla JavaScript frontend, bundled into a single .EXE via PyInstaller.

**Stack**: Python 3.12 + FastAPI | Vanilla JS (HTML5/CSS3) | SQLite | PyWebView | PyInstaller

---

## High-Level Architecture

```
USER LAUNCHES: Marcus_v052.exe
      ↓
launcher.py (Python entrypoint)
      ├─→ Starts FastAPI backend on localhost:8000
      │   └─→ backend/api.py (Uvicorn server)
      │       ├─→ Mounts /static (frontend files)
      │       ├─→ /api/* endpoints (chat, upload, graph)
      │       └─→ SQLite DB (marcus_v052.db)
      │
      └─→ Opens PyWebView desktop window
          └─→ Loads http://localhost:8000/ (frontend)
              ├─→ index.html (semantic HTML5)
              ├─→ style.css (design system + animations)
              └─→ app.js (modular JS app, async/await)
```

---

## Folder Structure & Ownership

### `marcus_v052/` (Root of standalone app)
- **Purpose**: Self-contained Windows desktop app
- **Buildable**: Yes, produces Marcus_v052.exe via PyInstaller
- **Owned by**: Main dev team

#### `marcus_v052/launcher.py`
- **Purpose**: Entry point. Starts backend thread, opens GUI window.
- **Tech**: Python, PyWebView
- **Responsibility**: Lifecycle management (backend startup, window open/close, error handling)

#### `marcus_v052/backend/`
- **Purpose**: REST API server + data layer
- **Tech**: FastAPI, SQLModel, Uvicorn
- **Files**:
  - `api.py` (~180 lines) - FastAPI app, route handlers, static file mounting
  - `models.py` - SQLModel entity definitions (ClassModel, TaskModel, FileModel)
  - `ollama_adapter.py` - LLM integration (chat completions)
  - `__init__.py` - Package marker

**Key Routes**:
  - `GET /` → Serves `index.html`
  - `GET /static/*` → Frontend assets (CSS, JS)
  - `GET /health` → Status check
  - `GET /api/graph` → Knowledge graph (nodes + edges)
  - `POST /api/upload` → File ingestion + parsing
  - `POST /api/chat` → Query LLM, get response

#### `marcus_v052/frontend/`
- **Purpose**: User interface (HTML + styling + interactivity)
- **Tech**: HTML5, CSS3, Vanilla ES6+ JavaScript (no frameworks)
- **Files**:
  - `index.html` (~160 lines) - Semantic markup, 3-pane layout
  - `style.css` (~3500 lines) - Design system, animations, responsive grid
  - `app.js` (~500 lines) - Modular JS: state, API calls, DOM updates

**Key UI Sections**:
  - Navbar: Brand icon, status indicator, settings button
  - Left sidebar: Knowledge graph canvas, statistics
  - Center: Upload zone, document grid, activity log
  - Right sidebar: Chat interface, message threading
  - Modal: Settings dialog with localStorage persistence

#### `marcus_v052/data/` (Runtime)
- **Purpose**: SQLite database, uploaded files storage
- **Files** (created at runtime):
  - `marcus_v052.db` - SQLite database
  - `files/` - Uploaded documents (PDFs, DOCX, TXT, etc.)
- **Not committed**: In .gitignore

#### `marcus_v052/scripts/`
- **Purpose**: Build, test, and deployment automation
- **Tech**: PowerShell (.ps1)
- **Files**:
  - `build_windows_exe.ps1` - Compiles with PyInstaller
  - `do_v052_all.ps1` - Full build + test pipeline
  - `smoke_test.ps1` - Integration test (health, root, graph, chat)

#### `marcus_v052/build/` & `marcus_v052/dist/`
- **Purpose**: PyInstaller outputs (temp and final)
- **Not committed**: In .gitignore
- **Artifacts**:
  - `dist/Marcus_v052.exe` - Final executable (~31.5 MB)
  - `build/Marcus_v052/` - Intermediate files

#### `marcus_v052/Marcus_v052.spec`
- **Purpose**: PyInstaller configuration
- **Defines**: Entry point, data files to bundle, icon, etc.
- **Key**: Must include `datas=[('frontend', 'frontend')]` to bundle frontend assets

#### `marcus_v052/requirements.txt`
- **Purpose**: Python package dependencies
- **Tool**: pip (standard Python package manager)
- **Key packages**:
  - `fastapi` (0.109.0) - Web framework
  - `uvicorn[standard]` (0.27.0) - ASGI server
  - `sqlmodel` (0.0.31) - ORM
  - `pywebview` (6.1) - Desktop GUI
  - `pyinstaller` (6.17.0) - EXE bundler

#### `marcus_v052/.venv/`
- **Purpose**: Python virtual environment (isolated packages)
- **Not committed**: In .gitignore
- **Setup**: Created via `python -m venv .venv`

---

## Dependencies Map

### Runtime Dependencies
```
FastAPI (REST server)
  └─ Starlette (ASGI framework)
     └─ Pydantic (data validation)
        └─ Pydantic-core (C extension)

SQLModel (ORM + data models)
  └─ SQLAlchemy (SQL toolkit)

Uvicorn (ASGI server)
  └─ asyncio (Python stdlib)

PyWebView (Desktop GUI)
  └─ Bottle (simple web server fallback)

PyInstaller (EXE bundler)
  └─ PyInstaller-hooks-contrib (auto-bundling)
```

### Build & Dev Tools
```
PyInstaller → Windows EXE generation
Python 3.12 → Language runtime
PowerShell → Script automation (CI/CD, testing)
Git → Version control
```

---

## Data Flow (Example: User uploads a document)

```
1. User drags file to upload zone (frontend)
   └─ app.js: setupDropZone() detects drop event

2. JavaScript reads file, creates FormData POST to /api/upload
   └─ POST http://localhost:8000/api/upload [binary file]

3. FastAPI backend receives upload
   └─ api.py: upload() handler
     ├─ Saves file to data/files/<filename>
     ├─ Extracts text + creates FileModel record
     ├─ Detects due dates, creates TaskModel entries
     └─ Returns JSON response

4. Frontend receives response, updates state
   └─ app.js: documents array updated
     ├─ renderDocuments() redraws grid
     ├─ showToast("Upload successful")
     └─ addActivityLog("Uploaded: filename")

5. User asks chat question → triggers loadGraphData()
   └─ GET http://localhost:8000/api/graph
   └─ Refreshes knowledge graph visualization
```

---

## Build Pipeline (High Level)

```
Phase 1: Validate Environment
  └─ Check Python 3.12, pip, PyInstaller installed
  └─ Verify requirements.txt can install

Phase 2: Install Dependencies
  └─ Create .venv if missing
  └─ pip install -r requirements.txt

Phase 3: Compile Backend
  └─ Python compile-check on backend/api.py

Phase 4: Backend Smoke Test
  └─ Spin up FastAPI server briefly
  └─ POST /health → expect OK

Phase 5: PyInstaller Build
  └─ pyinstaller Marcus_v052.spec
  └─ Output: dist/Marcus_v052.exe

Phase 6: Integration Test (Smoke Test)
  └─ Launch EXE in background
  └─ Hit /health, /api/graph, /api/chat endpoints
  └─ Verify responses are valid JSON

Phase 7: Package
  └─ ZIP EXE + minimal runtime
  └─ Upload to release storage
```

**Total build time**: ~5-7 minutes on modern Windows machine.

---

## Key Files at a Glance

| File | Lines | Purpose | Language |
|------|-------|---------|----------|
| `launcher.py` | ~50 | App entrypoint | Python |
| `backend/api.py` | ~180 | REST API server | Python |
| `backend/models.py` | ~50 | Data entities | Python |
| `backend/ollama_adapter.py` | ~80 | LLM client | Python |
| `frontend/index.html` | ~160 | DOM structure | HTML5 |
| `frontend/style.css` | ~3500 | Design + animations | CSS3 |
| `frontend/app.js` | ~500 | Interactive app | JavaScript |
| `Marcus_v052.spec` | ~20 | Build config | YAML-like |
| `requirements.txt` | ~9 | Dependencies | Plain text |
| `scripts/*.ps1` | ~200 total | Build automation | PowerShell |

---

## Quick Start Commands

```powershell
# Build the EXE
powershell -ExecutionPolicy Bypass -File marcus_v052/scripts/build_windows_exe.ps1

# Run full pipeline (build + test)
powershell -ExecutionPolicy Bypass -File marcus_v052/scripts/do_v052_all.ps1

# Run smoke test only
powershell -ExecutionPolicy Bypass -File marcus_v052/scripts/smoke_test.ps1

# Launch the app
.\marcus_v052\dist\Marcus_v052.exe
```

For full setup details, see [SETUP_WINDOWS.md](SETUP_WINDOWS.md).

---

## Design Philosophy

- **Simplicity over features**: Vanilla stack, no JS frameworks
- **Self-contained**: Single EXE, no installer, no dependencies at runtime
- **Offline-first**: All processing local, no cloud calls
- **User-focused**: Clear UI, intuitive workflows
- **Developer-friendly**: Well-organized backend, readable frontend code
