"""
V0.39: PROJECT MANAGEMENT API ROUTES

These are the API endpoints for project management.
Import this module in api.py to register all routes.
"""

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
from datetime import datetime

from marcus_app.core.database import get_db
from marcus_app.core.schemas import (
    ProjectCreateRequest, ProjectResponse, ProjectUpdateRequest,
    ProjectFileCreateRequest, ProjectFileResponse,
    ProjectNoteCreateRequest, ProjectNoteResponse, ProjectNoteUpdateRequest
)
from marcus_app.services.project_service import ProjectService
from marcus_app.services.auth_service import AuthService
from fastapi.responses import FileResponse

# Create router
router = APIRouter(prefix="/api/projects", tags=["projects"])

# Auth service (get from api.py context)
def require_auth(session_token: Optional[str] = Cookie(None, alias="marcus_session")):
    """Dependency to require valid session."""
    from marcus_app.backend.api import auth_service
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


# ============================================================================
# PROJECT CRUD ENDPOINTS
# ============================================================================

@router.post("", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Create a new project."""
    try:
        project = ProjectService.create_project(db, request)
        return project
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """List all active projects."""
    projects = ProjectService.list_projects(db)
    return projects


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get a specific project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Update project metadata."""
    from marcus_app.core.models import Project
    
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    if request.description is not None:
        project.description = request.description
    if request.status is not None:
        project.status = request.status
    
    project.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(project)
    
    return project


@router.delete("/{project_id}")
async def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Delete a project."""
    success = ProjectService.delete_project(db, project_id)
    if not success:
        raise HTTPException(status_code=404, detail="Project not found")
    return {"status": "deleted"}


# ============================================================================
# PROJECT FILE ENDPOINTS
# ============================================================================

@router.post("/{project_id}/files", response_model=ProjectFileResponse)
async def create_project_file(
    project_id: int,
    request: ProjectFileCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Create or update a file in a project."""
    try:
        file = ProjectService.create_file(db, project_id, request)
        return file
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/files", response_model=List[ProjectFileResponse])
async def list_project_files(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """List all files in a project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    files = ProjectService.list_files(db, project_id)
    return files


@router.get("/{project_id}/files/{file_path:path}")
async def read_project_file(
    project_id: int,
    file_path: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Read a file from a project."""
    try:
        content, db_file = ProjectService.read_file(db, project_id, file_path)
        return {
            "path": file_path,
            "content": content,
            "file_type": db_file.file_type,
            "file_size": db_file.file_size,
            "modified_at": db_file.modified_at
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{project_id}/files/{file_path:path}")
async def delete_project_file(
    project_id: int,
    file_path: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Delete a file from a project."""
    success = ProjectService.delete_file(db, project_id, file_path)
    if not success:
        raise HTTPException(status_code=404, detail="File not found")
    return {"status": "deleted"}


# ============================================================================
# PROJECT NOTES ENDPOINTS
# ============================================================================

@router.post("/{project_id}/notes", response_model=ProjectNoteResponse)
async def create_project_note(
    project_id: int,
    request: ProjectNoteCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Create a new project note."""
    try:
        note = ProjectService.create_note(db, project_id, request)
        return note
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/notes", response_model=List[ProjectNoteResponse])
async def list_project_notes(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """List all notes for a project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    notes = ProjectService.list_notes(db, project_id)
    return notes


@router.put("/{project_id}/notes/{note_id}", response_model=ProjectNoteResponse)
async def update_project_note(
    project_id: int,
    note_id: int,
    request: ProjectNoteUpdateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Update a project note."""
    note = ProjectService.get_note(db, note_id)
    if not note or note.project_id != project_id:
        raise HTTPException(status_code=404, detail="Note not found")
    
    updated_note = ProjectService.update_note(db, note_id, request.title, request.content)
    return updated_note


@router.delete("/{project_id}/notes/{note_id}")
async def delete_project_note(
    project_id: int,
    note_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Delete a project note."""
    note = ProjectService.get_note(db, note_id)
    if not note or note.project_id != project_id:
        raise HTTPException(status_code=404, detail="Note not found")
    
    ProjectService.delete_note(db, note_id)
    return {"status": "deleted"}


# ============================================================================
# PROJECT PREVIEW ENDPOINT (Static File Serving)
# ============================================================================

def get_media_type(file_extension: str) -> str:
    """Get MIME type for file extension."""
    media_types = {
        ".html": "text/html",
        ".htm": "text/html",
        ".css": "text/css",
        ".js": "application/javascript",
        ".json": "application/json",
        ".xml": "application/xml",
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".gif": "image/gif",
        ".svg": "image/svg+xml",
        ".ico": "image/x-icon",
        ".woff": "font/woff",
        ".woff2": "font/woff2",
        ".ttf": "font/ttf",
        ".txt": "text/plain",
        ".md": "text/markdown",
    }
    return media_types.get(file_extension.lower(), "application/octet-stream")


# We'll add the preview endpoint to main api.py manually to avoid router prefix issues
# Because /preview/ should be at root, not /api/projects/preview/
