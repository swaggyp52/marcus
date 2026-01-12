"""
Artifact Routes - v0.46

API endpoints for artifact management.
Minimal wrappers to support Inbox Panel and Ask Panel operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from marcus_app.core.database import get_db
from marcus_app.core.models import Artifact, MissionArtifact


router = APIRouter(prefix="/api", tags=["artifacts"])


# ============================================================================
# AUTH DEPENDENCY (reuse existing)
# ============================================================================

def require_auth():
    """Require authentication - stub for development."""
    # TODO: Integrate with existing auth service
    return True


# ============================================================================
# ARTIFACT ENDPOINTS
# ============================================================================

@router.get("/artifacts")
async def list_artifacts(
    class_id: Optional[int] = None,
    assignment_id: Optional[int] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    List artifacts with optional filtering.

    Query params:
    - class_id: Filter by class (via assignment relationship)
    - assignment_id: Filter by assignment
    """
    query = db.query(Artifact)

    if assignment_id:
        query = query.filter(Artifact.assignment_id == assignment_id)
    elif class_id:
        # Filter by class via assignment
        from marcus_app.core.models import Assignment
        assignment_ids = [a.id for a in db.query(Assignment).filter(Assignment.class_id == class_id).all()]
        query = query.filter(Artifact.assignment_id.in_(assignment_ids))

    artifacts = query.order_by(Artifact.created_at.desc()).limit(100).all()

    return [
        {
            'id': artifact.id,
            'assignment_id': artifact.assignment_id,
            'filename': artifact.filename,
            'original_filename': artifact.original_filename,
            'file_type': artifact.file_type,
            'file_size': artifact.file_size,
            'created_at': artifact.created_at.isoformat()
        }
        for artifact in artifacts
    ]


class CreateNoteRequest(BaseModel):
    title: str
    content: str


@router.post("/missions/{mission_id}/artifacts/create-note")
async def create_note_artifact(
    mission_id: int,
    request: CreateNoteRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a note artifact for a mission.

    This is a convenience endpoint for "Pin as Note" functionality in Ask Panel.
    Creates a simple note-type mission artifact without running a box.
    """
    from marcus_app.core.models import Mission
    import json
    from datetime import datetime

    # Verify mission exists
    mission = db.query(Mission).filter(Mission.id == mission_id).first()
    if not mission:
        raise HTTPException(status_code=404, detail="Mission not found")

    # Create note artifact
    note = MissionArtifact(
        mission_id=mission_id,
        box_id=None,  # Not created by a specific box
        artifact_type='note',
        title=request.title[:200],
        content_md=request.content,
        content_json=json.dumps({'note': request.content}),
        created_at=datetime.utcnow()
    )

    db.add(note)
    db.commit()
    db.refresh(note)

    return {
        'id': note.id,
        'mission_id': note.mission_id,
        'type': note.artifact_type,
        'title': note.title,
        'created_at': note.created_at.isoformat()
    }
