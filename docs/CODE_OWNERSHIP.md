# Code Ownership Map

Folder-level responsibility assignments for Marcus v052.

---

## marcus_v052/

**Primary Owner**: Main Development Team  
**Purpose**: Standalone desktop app (self-contained, buildable)

### marcus_v052/launcher.py
**Owner**: Build/Desktop Specialist  
**Responsibility**:
- App lifecycle (startup, shutdown)
- Backend process management
- PyWebView integration
- Error handling & logging
- Platform-specific behavior (Windows)

**When to edit**:
- Port configuration changes
- Backend startup logic
- GUI window properties

---

### marcus_v052/backend/

**Owner**: Backend Developer  
**Purpose**: REST API + business logic

#### backend/api.py
**Responsibility**:
- FastAPI application setup
- Route handlers (GET/POST/etc)
- Static file mounting
- Request/response handling
- Database session management
- Integration with models & ollama_adapter

**When to edit**:
- Add/modify API routes
- Change request/response schemas
- Fix bugs in request handling
- Optimize query performance

#### backend/models.py
**Responsibility**:
- SQLModel entity definitions
- Database schema (ClassModel, TaskModel, FileModel, etc)
- Validation rules (via Pydantic)
- Relationships between entities

**When to edit**:
- Add new entity types
- Change field types or constraints
- Add database migrations (if schema changes)

#### backend/ollama_adapter.py
**Responsibility**:
- LLM integration (Ollama client)
- Chat completions API
- Model availability detection
- Error handling for LLM failures

**When to edit**:
- Change Ollama host/port
- Add new LLM models
- Modify chat prompt engineering
- Fix LLM integration bugs

---

### marcus_v052/frontend/

**Owner**: Frontend Developer  
**Purpose**: User interface (HTML, CSS, JavaScript)

#### frontend/index.html
**Responsibility**:
- DOM structure (semantic HTML5)
- Accessibility markup (aria-labels, etc)
- Form elements & layout
- Script & stylesheet references

**When to edit**:
- Restructure UI layout
- Add new sections/components
- Fix accessibility issues
- Update meta tags

#### frontend/style.css
**Responsibility**:
- Visual design (colors, fonts, spacing)
- Animations & transitions
- Responsive layout (desktop, tablet, mobile)
- Component styling (buttons, modals, cards, etc)
- CSS variables (design system)

**When to edit**:
- Change colors/branding
- Add animations
- Fix responsive breakpoints
- Adjust spacing/alignment
- Update design tokens

#### frontend/app.js
**Responsibility**:
- Application logic (state management, API calls)
- DOM manipulation & event handling
- Async workflows (uploads, chat, etc)
- Local storage (settings persistence)
- User feedback (toasts, modals, etc)

**When to edit**:
- Add new features
- Fix interactivity bugs
- Change API integration
- Optimize performance
- Improve user experience

---

### marcus_v052/data/

**Owner**: None (runtime-generated)  
**Purpose**: User data at runtime

- `marcus_v052.db` - SQLite database (created by backend)
- `files/` - Uploaded documents (managed by backend)

**Git**: Ignored in `.gitignore` (not committed)

---

### marcus_v052/build/, marcus_v052/dist/

**Owner**: Build System  
**Purpose**: Temporary & output artifacts

- `build/` - PyInstaller intermediate files
- `dist/Marcus_v052.exe` - Final executable

**Git**: Ignored in `.gitignore` (not committed)

---

## Root-Level Supporting Files

### marcus_v052/requirements.txt
**Owner**: Build/Platform Specialist  
**Responsibility**: Python package dependencies  
**When to edit**:
- Add/remove/upgrade packages
- Lock versions for reproducibility

---

### marcus_v052/Marcus_v052.spec
**Owner**: Build Specialist  
**Responsibility**: PyInstaller configuration (EXE generation)  
**When to edit**:
- Include new data files (assets, config, etc)
- Change entry point
- Modify icon or metadata
- Add/remove hidden imports

**Warning**: Requires rebuild after changes.

---

### marcus_v052/scripts/

**Owner**: Build/DevOps Specialist  
**Responsibility**: Build automation, testing, deployment

#### scripts/build_windows_exe.ps1
- Compiles Python → EXE via PyInstaller

#### scripts/do_v052_all.ps1
- Orchestrates full build pipeline (install → compile → test → bundle)

#### scripts/smoke_test.ps1
- Integration test (backend health, API endpoints, etc)

**When to edit**:
- Change build steps
- Add new test checks
- Optimize pipeline

---

## Agent-Driven Tooling (New in Session 12+)

### .agent/scripts/

**Owner**: Agent Maintainer  
**Purpose**: Automated workflows (build doctor, bug hunter, refactorer, test writer, doc indexer, release sheriff)

See [docs/AGENTS.md](AGENTS.md) for detailed agent responsibilities.

---

## Documentation

### docs/

**Owner**: Tech Writer / Product Manager  
**Responsibility**: Keep docs synced with code

#### docs/REPO_MAP.md
- High-level architecture overview

#### docs/DEPENDENCIES.md
- Runtime & build dependencies, version matrix

#### docs/ENTRYPOINTS.md
- How to run (build, test, develop locally)

#### docs/CODE_OWNERSHIP.md (this file)
- Folder responsibility map

#### docs/SETUP_WINDOWS.md
- Step-by-step Windows setup guide

#### docs/AGENTS.md
- Agent specifications & workflows

---

## Cross-Cutting Concerns

### Performance
- **Owner**: Backend Developer (API optimization)  
- **Owner**: Frontend Developer (UI smoothness, animation perf)

### Security
- **Owner**: Backend Developer (API security, data validation)
- **Owner**: Build Specialist (dependency security scanning)

### User Experience
- **Owner**: Frontend Developer (UI design, interactions)
- **Owner**: Backend Developer (API response times, reliability)

### Reliability & Testing
- **Owner**: QA / Build Specialist (test coverage, smoke tests)
- **Owner**: Backend Developer (unit tests for API)

---

## Decision Log

| Date | Owner | Decision | Impact |
|------|-------|----------|--------|
| 2025-01-12 | Main Team | Switched to vanilla JS (no frameworks) | Faster load, smaller EXE |
| 2025-01-12 | Main Team | FastAPI + SQLModel | Type-safe backend, good DX |
| 2025-01-12 | Main Team | PyInstaller bundling | Single .EXE, no installer needed |

---

## How Ownership Works

### When You Own a File/Folder:
1. **Be the gatekeeper** - Reviews/approves changes
2. **Document intent** - Explain your design decisions
3. **Maintain tests** - Ensure your code is well-tested
4. **Fix bugs** - First line of defense for issues in your area
5. **Mentor others** - Help team understand your code

### When You Want to Change Someone Else's Code:
1. **Open a PR** - Link to issue/feature
2. **Get review** - Owner or designated reviewer
3. **Address feedback** - Iterate until approved
4. **Merge** - Follow branch naming conventions

### Escalation:
If owner is unavailable, escalate to Main Team lead.

---

## Contact

For questions on code ownership:
- Backend: Contact Backend Developer
- Frontend: Contact Frontend Developer  
- Build: Contact Build Specialist
- Overall architecture: Contact Main Team Lead
