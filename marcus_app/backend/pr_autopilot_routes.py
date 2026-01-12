"""
PR Autopilot Routes (v0.43)

Endpoint for generating PR text suggestions from staged diffs.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
import json

from marcus_app.core.database import get_db
from marcus_app.core.models import AuditLog
from marcus_app.services.pr_autopilot_service import PRAutopilotService, PRAutopilotError
from marcus_app.services.project_service import ProjectService


router = APIRouter(prefix="/api/projects", tags=["pr-autopilot"])


def require_auth(session_token: Optional[str] = None):
    """Require authentication."""
    from marcus_app.backend.api import auth_service
    from fastapi import Cookie

    session_token = Cookie(None, alias="marcus_session")
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


@router.post("/{project_id}/pr-autopilot")
async def suggest_pr_text(
    project_id: int,
    base_branch: str = 'main',
    current_branch: Optional[str] = None,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Analyze staged diff and propose PR title/body.

    Offline-first, read-only operation.

    Args:
        project_id: Project ID
        base_branch: Target branch (default: 'main')
        current_branch: Source branch (auto-detect if not provided)

    Returns:
        {
            "title": str,
            "body_md": str,
            "summary": str,
            "files_changed": List[str],
            "confidence": str,  # "low" | "medium" | "high"
            "method": str,  # "heuristic" | "llm"
            "diff_hash": str,
            "timestamp": str
        }

    Security:
        - Requires authentication
        - Read-only (no file modifications)
        - Offline operation (no network calls)
        - 200KB diff size limit enforced
        - Logs usage to audit log
    """
    # Get project
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        # Generate PR text suggestion
        result = PRAutopilotService.propose_pr_text(
            project_path=project.root_path,
            base_branch=base_branch,
            current_branch=current_branch
        )

        # Log to audit (offline action)
        audit_log = AuditLog(
            event_type='pr_autopilot_suggest',
            user_action=f"Generated PR text suggestion for {len(result['files_changed'])} files",
            online_mode='offline',
            metadata=json.dumps({
                'project_id': project_id,
                'base_branch': base_branch,
                'current_branch': current_branch or result.get('current_branch', 'unknown'),
                'file_count': len(result['files_changed']),
                'method': result['method'],
                'confidence': result['confidence'],
                'diff_hash': result['diff_hash']
            })
        )
        db.add(audit_log)
        db.commit()

        return result

    except PRAutopilotError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR autopilot failed: {str(e)}")
