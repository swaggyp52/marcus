"""
V0.40: ONLINE MODE ROUTES

Push and PR creation - GATED BEHIND Online Mode permissions.

These endpoints:
- Check if Online Mode is enabled
- Require explicit user action (not auto-triggered)
- Log all network operations to audit_log
- Show confirmation modals with operation details
"""

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
import subprocess

from marcus_app.core.database import get_db
from marcus_app.core.models import DevChangeSet, AuditLog, SystemConfig
from marcus_app.core.schemas import GitPushRequest, GitHubPRCreateRequest
from marcus_app.services.project_service import ProjectService
from marcus_app.services.git_service import LocalGitClient, GitOperationError
from marcus_app.services.token_service import TokenService


router = APIRouter(prefix="/api/projects", tags=["online"])


def require_auth(session_token: Optional[str] = Cookie(None, alias="marcus_session")):
    """Require authentication."""
    from marcus_app.backend.api import auth_service
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


def require_online_mode(db: Session) -> None:
    """Check if Online Mode is enabled."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'online_mode'
    ).first()
    
    if not config or config.value != 'online':
        raise HTTPException(
            status_code=403,
            detail="Online Mode must be explicitly enabled. Go to Settings → Online Mode."
        )


# ============================================================================
# GIT PUSH ENDPOINT (Gated)
# ============================================================================

@router.post("/{project_id}/git/push")
async def push_branch(
    project_id: int,
    request: GitPushRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Push branch to remote (GitHub, etc).
    
    REQUIRES:
    - Online Mode explicitly enabled
    - User confirmation via frontend
    - Remote URL configured
    """
    # Check Online Mode
    require_online_mode(db)
    
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        # Check for remote
        remote_url = client.get_remote_url('origin')
        if not remote_url:
            raise HTTPException(
                status_code=400,
                detail="No remote configured. Add remote URL first."
            )
        
        # Perform push (may require credentials)
        cmd = ['git', 'push', 'origin', request.branch_name]
        if request.force:
            cmd.insert(2, '--force-with-lease')
        
        result = subprocess.run(
            cmd,
            cwd=str(project.root_path),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode != 0:
            raise GitOperationError(result.stderr)
        
        # Log the push
        audit = AuditLog(
            timestamp=datetime.utcnow(),
            event_type='git_push',
            online_mode='online',
            query=f"Project {project_id}, Branch {request.branch_name}",
            user_action=f"Pushed to {remote_url}"
        )
        db.add(audit)
        db.commit()
        
        return {
            "status": "pushed",
            "branch": request.branch_name,
            "remote": "origin",
            "message": result.stdout
        }
    
    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=408, detail="Push timed out")
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# GITHUB PR CREATION (Gated)
# ============================================================================

@router.post("/{project_id}/github/create-pr")
async def create_github_pr(
    project_id: int,
    request: GitHubPRCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Create PR on GitHub.
    
    REQUIRES:
    - Online Mode explicitly enabled
    - GitHub auth token (via gh CLI or stored token)
    - User confirmation
    """
    # Check Online Mode
    require_online_mode(db)
    
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        # Try gh CLI first (easiest, least storage)
        pr_url = _create_pr_with_gh_cli(
            project.root_path,
            request.title,
            request.body or "",
            request.target_branch or "",
            request.base_branch
        )
        
        if pr_url:
            # Log the PR creation
            audit = AuditLog(
                timestamp=datetime.utcnow(),
                event_type='github_pr_created',
                online_mode='online',
                query=f"Project {project_id}",
                user_action=f"Created PR: {pr_url}"
            )
            db.add(audit)
            db.commit()
            
            # Update changeset if exists
            changeset = db.query(DevChangeSet).filter(
                DevChangeSet.project_id == project_id,
                DevChangeSet.status == 'pushed'
            ).order_by(DevChangeSet.created_at.desc()).first()
            
            if changeset:
                changeset.pr_url = pr_url
                changeset.status = 'pr_created'
                db.commit()
            
            return {
                "status": "pr_created",
                "pr_url": pr_url,
                "title": request.title
            }
        
        # Fallback: suggest manual creation
        raise HTTPException(
            status_code=400,
            detail="gh CLI not found. Install GitHub CLI or create PR manually."
        )
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


def _create_pr_with_gh_cli(
    project_root: str,
    title: str,
    body: str,
    target_branch: str,
    base_branch: str
) -> Optional[str]:
    """
    Create PR using GitHub CLI (gh).
    
    Returns:
        PR URL if successful, None otherwise
    """
    try:
        cmd = [
            'gh', 'pr', 'create',
            '--title', title,
            '--body', body or "(No description)",
            '--base', base_branch
        ]
        
        if target_branch:
            cmd.extend(['--head', target_branch])
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            # Extract PR URL from output
            output = result.stdout.strip()
            if output.startswith('https://'):
                return output
            # Otherwise try to parse it
            for line in output.split('\n'):
                if line.startswith('https://'):
                    return line
        
        return None
    
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return None


# ============================================================================
# ONLINE MODE STATUS
# ============================================================================

@router.get("/dev-mode/online-status")
async def get_online_status(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Check if Online Mode is currently enabled."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'online_mode'
    ).first()
    
    is_online = config and config.value == 'online'
    
    return {
        "online_mode": is_online,
        "message": "Online Mode is " + ("enabled" if is_online else "disabled")
    }


@router.post("/dev-mode/enable-online")
async def enable_online_mode(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Explicitly enable Online Mode.
    This is NOT automatic - requires user action.
    """
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'online_mode'
    ).first()
    
    if not config:
        config = SystemConfig(key='online_mode', value='online')
        db.add(config)
    else:
        config.value = 'online'
    
    db.commit()
    
    # Audit log
    audit = AuditLog(
        timestamp=datetime.utcnow(),
        event_type='online_mode_enabled',
        online_mode='offline',  # This action itself doesn't require network
        user_action="User explicitly enabled Online Mode"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "online_mode_enabled"}


@router.post("/dev-mode/disable-online")
async def disable_online_mode(
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Disable Online Mode (return to offline-first)."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == 'online_mode'
    ).first()
    
    if config:
        config.value = 'offline'
        db.commit()
    
    # Audit log
    audit = AuditLog(
        timestamp=datetime.utcnow(),
        event_type='online_mode_disabled',
        online_mode='offline',
        user_action="User disabled Online Mode"
    )
    db.add(audit)
    db.commit()
    
    return {"status": "online_mode_disabled"}
