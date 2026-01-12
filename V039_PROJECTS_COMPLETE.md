# v0.39: PROJECTS MODULE - Local Development Workspace

## Overview

v0.39 introduces the **Projects Module**, transforming Marcus into a secure, encrypted local development workspace. Users can now create, edit, and preview web projects (HTML/CSS/JS), software projects, and documentation directly within the Marcus vault at `M:\Marcus\projects\`.

This is **NOT** a full IDE. It's a focused, offline-first workspace designed specifically for local ownership and safety.

## What's New

### Project Management
- **Create projects** with names, descriptions, and type (web, software, docs)
- **Organize files** hierarchically within each project
- **Store metadata** about all files (size, type, modification time)
- **Add project notes** in Markdown for architecture, TODOs, design decisions

### File Operations
- **Create/update files** with text content (HTML, CSS, JS, JSON, MD, TXT, etc.)
- **Read files** from projects programmatically via API
- **Delete files** with cascade cleanup from disk and database
- **Preview web projects** via HTTP at `/preview/{project_name}/path/to/file.html`

### Storage & Security
- All projects stored in `M:\Marcus\projects\` on encrypted VeraCrypt drive
- Directory structure automatically created per project
- Path traversal attacks prevented via strict validation
- Requires authentication for all operations
- Audit logging via existing Marcus audit system

### Database Schema

Three new tables added:

#### `projects`
```sql
id (PK)
name (UNIQUE)
description (TEXT)
project_type (web|software|docs)
root_path (M:\Marcus\projects\ProjectName\)
status (active|archived)
created_at, updated_at
```

#### `project_files`
```sql
id (PK)
project_id (FK)
relative_path (index.html, css/style.css, etc)
file_type (html, css, js, etc)
file_size (bytes)
created_at, modified_at
```

#### `project_notes`
```sql
id (PK)
project_id (FK)
title
content (Markdown)
created_at, updated_at
```

## API Endpoints

### Project CRUD
- `POST /api/projects` - Create new project
- `GET /api/projects` - List all projects
- `GET /api/projects/{id}` - Get project details
- `PUT /api/projects/{id}` - Update project metadata
- `DELETE /api/projects/{id}` - Delete project (removes directory)

### File Operations
- `POST /api/projects/{id}/files` - Create/update file
- `GET /api/projects/{id}/files` - List project files
- `GET /api/projects/{id}/files/{path}` - Read file content
- `DELETE /api/projects/{id}/files/{path}` - Delete file

### Project Notes
- `POST /api/projects/{id}/notes` - Create note
- `GET /api/projects/{id}/notes` - List notes
- `PUT /api/projects/{id}/notes/{note_id}` - Update note
- `DELETE /api/projects/{id}/notes/{note_id}` - Delete note

### Web Preview
- `GET /preview/{project_name}/{file_path}` - Serve file for preview
  - Example: `/preview/RedByte/index.html`
  - Content types auto-detected (HTML, CSS, JS, images, etc)
  - Static file serving only (no server-side execution)

## Pydantic Schemas

- `ProjectResponse` - Full project with files and notes
- `ProjectCreateRequest` - Create project
- `ProjectUpdateRequest` - Update metadata
- `ProjectFileResponse` - File metadata
- `ProjectFileCreateRequest` - Create/update file
- `ProjectNoteResponse` - Note metadata
- `ProjectNoteCreateRequest` - Create note
- `ProjectNoteUpdateRequest` - Update note

## Service Layer

**`marcus_app/services/project_service.py`**

Core `ProjectService` class provides all project operations:
- `create_project(db, request)` - Create with directory
- `get_project(db, id)` - Retrieve by ID
- `list_projects(db)` - List active projects
- `delete_project(db, id)` - Delete with cleanup
- `create_file(db, project_id, request)` - Create file on disk + DB
- `read_file(db, project_id, path)` - Read file content
- `list_files(db, project_id)` - List all files
- `delete_file(db, project_id, path)` - Delete file
- `create_note(db, project_id, request)` - Create note
- `list_notes(db, project_id)` - List notes
- `update_note(db, note_id, ...)` - Update note
- `delete_note(db, note_id)` - Delete note

**Security Features:**
- `ensure_base_dir()` - Verify M:\Marcus\projects\ accessible
- `get_project_root(name)` - Sanitize project names, prevent traversal
- Path validation on all file operations
- Authorization checks on all endpoints

## Implementation Details

### Database Migration
File: `scripts/migrate_to_v039.py`
- Runs `Base.metadata.create_all()` to create new tables
- Creates M:\Marcus\projects\ directory structure
- Idempotent (safe to run multiple times)

### File I/O
- Files stored on disk at `M:\Marcus\projects\{ProjectName}\{relative_path}`
- Metadata tracked in database for quick lookups
- Subdirectories automatically created as needed
- UTF-8 encoding for all text files
- File size tracked for UI display

### Authentication
- All endpoints require valid session token (15-min timeout)
- Dependency: `require_auth()` enforces on every request
- Returns 401 if not authenticated

### Error Handling
- 404 if project/file/note not found
- 400 if invalid request (bad paths, missing fields)
- 403 if path traversal detected
- Clear error messages for API consumers

## Usage Examples

### Create a Web Project
```bash
curl -X POST http://localhost:8000/api/projects \
  -H "Content-Type: application/json" \
  -b "marcus_session=<token>" \
  -d '{
    "name": "RedByte",
    "description": "Company website redesign",
    "project_type": "web"
  }'
```

### Create a File
```bash
curl -X POST http://localhost:8000/api/projects/1/files \
  -H "Content-Type: application/json" \
  -b "marcus_session=<token>" \
  -d '{
    "relative_path": "index.html",
    "content": "<html>...</html>"
  }'
```

### Read a File
```bash
curl http://localhost:8000/api/projects/1/files/index.html \
  -b "marcus_session=<token>"
```

### Preview a Project
```
http://localhost:8000/preview/RedByte/index.html
```

### Add Project Notes
```bash
curl -X POST http://localhost:8000/api/projects/1/notes \
  -H "Content-Type: application/json" \
  -b "marcus_session=<token>" \
  -d '{
    "title": "Architecture",
    "content": "# Design Decisions\n\n- Use React for frontend\n- SQLite for state"
  }'
```

## Directory Structure

```
M:\Marcus\projects\
├── RedByte\
│   ├── index.html
│   ├── style.css
│   ├── app.js
│   └── assets\
│       └── logo.png
├── MyApp\
│   ├── main.py
│   ├── requirements.txt
│   └── README.md
└── Documentation\
    ├── architecture.md
    └── api-spec.md
```

## Limitations & Non-Features

This module **intentionally does NOT include:**
- ❌ Terminal/shell access
- ❌ Code execution/debugging
- ❌ Language servers (LSP)
- ❌ Git integration
- ❌ AI code generation
- ❌ Complex build systems
- ❌ Remote synchronization
- ❌ Package managers

It **IS** designed for:
- ✅ Text editing with syntax highlighting (frontend responsibility)
- ✅ Local file management
- ✅ Web preview (static files only)
- ✅ Notes and documentation
- ✅ Encrypted, offline-first storage
- ✅ Ownership and locality

## Testing

Run sanity checks:
```bash
cd C:\Users\conno\marcus
python -c "from marcus_app.services.project_service import ProjectService; ProjectService.ensure_base_dir(); print('✓ OK')"
```

Run full test suite:
```bash
pytest marcus_app/tests/test_v039_projects.py -v
```

## Backward Compatibility

✅ **No breaking changes** to existing features:
- Search (v0.37) - fully functional
- Study Packs (v0.38) - fully functional
- Classes, Assignments, Artifacts - fully functional
- Auth system - reused for projects
- Audit logging - applied to project operations

## Next Steps (v0.40+)

Potential future enhancements:
- UI for Projects page with file tree
- Monaco/Ace editor with syntax highlighting
- Better preview capabilities (markdown rendering)
- Project templates (starter files)
- Batch operations (upload multiple files)
- Version history for files
- Collaboration mode (future)

## Files Modified/Created

**New Files:**
- `marcus_app/services/project_service.py` (315 lines)
- `marcus_app/tests/test_v039_projects.py` (300+ lines)
- `scripts/migrate_to_v039.py` (migration script)

**Modified Files:**
- `marcus_app/core/models.py` (+100 lines, 3 new models)
- `marcus_app/core/schemas.py` (+60 lines, 8 new schemas)
- `marcus_app/backend/api.py` (+250 lines, 18 new endpoints)

**Total New Code:** ~1000 lines

## Acceptance Criteria Status

✅ **All Complete:**
1. Projects stored in M:\Marcus\projects\
2. Can create/edit/delete files via API
3. Can create/edit/delete project notes
4. Web projects previewable via /preview/ route
5. All operations require authentication
6. Path traversal prevented
7. Requires encrypted drive mounted
8. No regression in existing features

## Known Issues

None at release.

## Support & Debugging

Check base directory access:
```bash
python -c "from marcus_app.services.project_service import ProjectService; print(ProjectService.BASE_PROJECT_DIR)"
```

Check database tables:
```bash
sqlite3 storage/marcus.db ".tables"
```

Check project root path:
```bash
python -c "from marcus_app.services.project_service import ProjectService; print(ProjectService.get_project_root('Test'))"
```

---

**Version:** 0.39  
**Release Date:** 2024  
**Status:** ✅ COMPLETE  
**Stability:** Production-ready
