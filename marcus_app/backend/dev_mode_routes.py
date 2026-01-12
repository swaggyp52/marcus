"""
V0.40: DEV MODE API ROUTES

Git operations (local-only, offline):
- Branch creation/switching
- Status/diff viewing
- Staging/committing
- ChangeSets save/export

All operations require authentication but NO Online Mode permission needed.
"""

from fastapi import APIRouter, Depends, HTTPException, Cookie
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
import json
from datetime import datetime

from marcus_app.core.database import get_db
from marcus_app.core.models import DevChangeSet, DevChangeSetFile, Project
from marcus_app.core.schemas import (
    GitStatusResponse, GitDiffResponse, GitBranchCreateRequest,
    GitCommitRequest, GitStageRequest, DevChangeSetResponse,
    DevChangeSetCreateRequest, DevChangeSetExportRequest
)
from marcus_app.services.git_service import LocalGitClient, GitOperationError
from marcus_app.services.project_service import ProjectService


router = APIRouter(prefix="/api/projects", tags=["dev-mode"])


def require_auth(session_token: Optional[str] = Cookie(None, alias="marcus_session")):
    """Require authentication (but NOT Online Mode)."""
    from marcus_app.backend.api import auth_service
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    return session_token


def require_online_mode(
    session_token: str = Depends(require_auth),
    db: Session = Depends(get_db)
):
    """Require both authentication AND Online Mode enabled."""
    from marcus_app.core.models import SystemConfig

    # Check if Online Mode is enabled
    online_config = db.query(SystemConfig).filter(
        SystemConfig.key == "online_mode_enabled"
    ).first()

    if not online_config or online_config.value != "true":
        raise HTTPException(
            status_code=403,
            detail="Online Mode not enabled. Enable Online Mode to use network operations."
        )

    return session_token


# ============================================================================
# GIT STATUS & DIFF ENDPOINTS
# ============================================================================

@router.get("/{project_id}/git/status", response_model=GitStatusResponse)
async def get_git_status(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get git repository status."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        return client.get_status()
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/git/diff", response_model=GitDiffResponse)
async def get_git_diff(
    project_id: int,
    staged_only: bool = False,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get git diff."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        full_diff = client.get_diff(staged_only=staged_only)
        summary = client.get_diff_summary()
        
        return {
            "summary": summary,
            "full_diff": full_diff
        }
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# GIT BRANCH OPERATIONS
# ============================================================================

@router.post("/{project_id}/git/init")
async def init_git_repo(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Initialize git repo for project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        if client.is_repository():
            raise HTTPException(status_code=400, detail="Already a git repository")
        
        client.initialize()
        return {"status": "initialized"}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/git/branch", response_model=dict)
async def create_branch(
    project_id: int,
    request: GitBranchCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Create and switch to new branch."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        if not client.is_repository():
            raise HTTPException(status_code=400, detail="Not a git repository")
        
        branch = client.create_branch(request.branch_name, request.from_branch)
        return {"branch": branch, "status": "created"}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/git/branches", response_model=List[str])
async def list_branches(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """List all branches."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        return client.list_branches()
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/git/checkout", response_model=dict)
async def checkout_branch(
    project_id: int,
    branch_name: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Switch to a branch."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        if not client.is_repository():
            raise HTTPException(status_code=400, detail="Not a git repository")
        
        branch = client.switch_branch(branch_name)
        return {"branch": branch, "status": "switched"}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# GIT STAGING & COMMITTING
# ============================================================================

@router.post("/{project_id}/git/stage")
async def stage_files(
    project_id: int,
    request: GitStageRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Stage specific files."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        if not request.files:
            raise HTTPException(status_code=400, detail="No files to stage")
        
        client.stage_files(request.files)
        return {"status": "staged", "count": len(request.files)}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/git/stage-all")
async def stage_all(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Stage all changes."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        client.stage_all()
        return {"status": "staged", "message": "All changes staged"}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/{project_id}/git/commit")
async def commit_changes(
    project_id: int,
    request: GitCommitRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Commit staged changes."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        commit_hash = client.commit(
            request.message,
            request.author_name,
            request.author_email
        )
        
        return {
            "status": "committed",
            "hash": commit_hash,
            "message": request.message
        }
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# GIT FILE OPERATIONS
# ============================================================================

@router.post("/{project_id}/git/revert-file")
async def revert_file(
    project_id: int,
    filepath: str,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Revert a file to last commit."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        client.revert_file(filepath)
        return {"status": "reverted", "file": filepath}
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# CHANGESET OPERATIONS (Offline PR Preparation)
# ============================================================================

@router.post("/{project_id}/changesets", response_model=DevChangeSetResponse)
async def create_changeset(
    project_id: int,
    request: DevChangeSetCreateRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Create a changeset from current branch.
    Snapshot diffs, commit info, file list for later push.
    """
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    try:
        client = LocalGitClient(project.root_path)
        
        # Get current state
        status = client.get_status()
        diff = client.get_diff()
        log = client.get_log(max_count=100)  # Get all commits on this branch
        
        # Count new commits vs main
        # (simplified: just count all commits)
        commit_count = len(log)
        
        # Changed files
        changed_files = client.get_changed_files() + client.get_staged_files()
        
        # Create changeset record
        changeset = DevChangeSet(
            project_id=project_id,
            branch_name=request.branch_name,
            commit_count=commit_count,
            status='ready',
            title=request.title,
            description=request.description,
            diff_snapshot=diff,
            changed_files=json.dumps(list(set(changed_files)))
        )
        
        db.add(changeset)
        db.flush()
        
        # Create file records
        for filepath in set(changed_files):
            file_record = DevChangeSetFile(
                changeset_id=changeset.id,
                relative_path=filepath,
                change_type='modified',  # Simplified
                diff_content=''
            )
            db.add(file_record)
        
        db.commit()
        db.refresh(changeset)
        
        # Audit log
        from marcus_app.core.models import AuditLog
        audit = AuditLog(
            timestamp=datetime.utcnow(),
            event_type='changeset_created',
            online_mode='offline',
            query=f"Project {project_id}, Branch {request.branch_name}",
            user_action=f"Created changeset: {request.title}"
        )
        db.add(audit)
        db.commit()
        
        return changeset
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{project_id}/changesets", response_model=List[DevChangeSetResponse])
async def list_changesets(
    project_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """List all changesets for a project."""
    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    changesets = db.query(DevChangeSet).filter(
        DevChangeSet.project_id == project_id
    ).order_by(DevChangeSet.created_at.desc()).all()
    
    return changesets


@router.get("/{project_id}/changesets/{changeset_id}", response_model=DevChangeSetResponse)
async def get_changeset(
    project_id: int,
    changeset_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Get changeset details."""
    changeset = db.query(DevChangeSet).filter(
        DevChangeSet.id == changeset_id,
        DevChangeSet.project_id == project_id
    ).first()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="Changeset not found")
    
    return changeset


@router.post("/{project_id}/changesets/{changeset_id}/export")
async def export_changeset(
    project_id: int,
    changeset_id: int,
    request: DevChangeSetExportRequest,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """
    Export changeset as patch file.
    Works entirely offline.
    """
    changeset = db.query(DevChangeSet).filter(
        DevChangeSet.id == changeset_id,
        DevChangeSet.project_id == project_id
    ).first()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="Changeset not found")
    
    # Return as downloadable patch
    patch_content = changeset.diff_snapshot
    
    from fastapi.responses import FileResponse, StreamingResponse
    
    # Return as stream
    return StreamingResponse(
        iter([patch_content]),
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename=changeset-{changeset_id}.patch"}
    )


@router.delete("/{project_id}/changesets/{changeset_id}")
async def delete_changeset(
    project_id: int,
    changeset_id: int,
    db: Session = Depends(get_db),
    _: str = Depends(require_auth)
):
    """Delete (archive) a changeset."""
    changeset = db.query(DevChangeSet).filter(
        DevChangeSet.id == changeset_id,
        DevChangeSet.project_id == project_id
    ).first()
    
    if not changeset:
        raise HTTPException(status_code=404, detail="Changeset not found")
    
    changeset.status = 'archived'
    db.commit()
    
    return {"status": "archived"}
# ============================================================================
# ONLINE OPERATIONS - PUSH & PULL REQUEST (v0.42)
# ============================================================================

@router.post("/{project_id}/git/push")
async def push_branch(
    project_id: int,
    branch_name: Optional[str] = None,
    force: bool = False,
    db: Session = Depends(get_db),
    _: str = Depends(require_online_mode)
):
    """
    Push branch to remote (REQUIRES Online Mode).

    Args:
        project_id: Project ID
        branch_name: Branch to push (defaults to current branch)
        force: Force push (use with caution)

    Security:
        - Requires authentication
        - Requires Online Mode enabled
        - Logs all push operations to audit log
    """
    from marcus_app.core.models import AuditLog

    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        client = LocalGitClient(project.root_path)

        # Get current branch if not specified
        if not branch_name:
            status = client.get_status()
            branch_name = status.current_branch

        # Get remote name (default to 'origin')
        remote = 'origin'

        # Execute push
        push_args = ['git', 'push', remote, branch_name]
        if force:
            push_args.append('--force')

        import subprocess
        result = subprocess.run(
            push_args,
            cwd=project.root_path,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )

        if result.returncode != 0:
            raise GitOperationError(f"Push failed: {result.stderr}")

        # Log successful push
        audit_log = AuditLog(
            event_type='git_push',
            user_action=f"Pushed branch '{branch_name}' to {remote}",
            online_mode='online',
            metadata=json.dumps({
                'project_id': project_id,
                'branch': branch_name,
                'remote': remote,
                'force': force
            })
        )
        db.add(audit_log)
        db.commit()

        return {
            "success": True,
            "message": f"Successfully pushed '{branch_name}' to {remote}",
            "branch": branch_name,
            "remote": remote
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="Push operation timed out")
    except GitOperationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Push failed: {str(e)}")


@router.post("/{project_id}/github/create-pr")
async def create_pull_request(
    project_id: int,
    title: str,
    body: Optional[str] = None,
    base_branch: str = 'main',
    db: Session = Depends(get_db),
    _: str = Depends(require_online_mode)
):
    """
    Create GitHub Pull Request (REQUIRES Online Mode).

    Args:
        project_id: Project ID
        title: PR title (required)
        body: PR description
        base_branch: Target branch (default: 'main')

    Security:
        - Requires authentication
        - Requires Online Mode enabled
        - Uses GitHub token from TokenService (encrypted)
        - Logs all PR creation to audit log
    """
    from marcus_app.core.models import AuditLog
    from marcus_app.services.token_service import TokenService
    import subprocess
    import re

    project = ProjectService.get_project(db, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    try:
        client = LocalGitClient(project.root_path)
        status = client.get_status()
        head_branch = status.current_branch

        # Prefer gh CLI if available
        gh_available = subprocess.run(
            ['gh', '--version'],
            capture_output=True,
            timeout=5
        ).returncode == 0

        if gh_available:
            # Use gh CLI (preferred method)
            cmd = [
                'gh', 'pr', 'create',
                '--title', title,
                '--base', base_branch,
                '--head', head_branch
            ]

            if body:
                cmd.extend(['--body', body])

            result = subprocess.run(
                cmd,
                cwd=project.root_path,
                capture_output=True,
                text=True,
                timeout=60
            )

            if result.returncode != 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"PR creation failed: {result.stderr}"
                )

            # Extract PR URL from gh output
            pr_url = result.stdout.strip().split('\n')[-1]

        else:
            # Fallback to GitHub API
            # Extract owner/repo from git remote
            remote_result = subprocess.run(
                ['git', 'remote', 'get-url', 'origin'],
                cwd=project.root_path,
                capture_output=True,
                text=True
            )

            if remote_result.returncode != 0:
                raise HTTPException(status_code=400, detail="Could not determine GitHub repository")

            remote_url = remote_result.stdout.strip()

            # Parse owner/repo from URL
            # Supports: git@github.com:owner/repo.git or https://github.com/owner/repo.git
            match = re.search(r'github\.com[:/]([^/]+)/([^/.]+)', remote_url)
            if not match:
                raise HTTPException(status_code=400, detail="Not a GitHub repository")

            owner, repo = match.groups()

            # Get GitHub token
            github_username = os.getenv('GITHUB_USERNAME', 'default')
            token = TokenService.retrieve_token(github_username, db)

            if not token:
                raise HTTPException(
                    status_code=400,
                    detail="GitHub token not found. Please configure token first."
                )

            # Create PR via GitHub API
            import requests
            api_url = f"https://api.github.com/repos/{owner}/{repo}/pulls"

            headers = {
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json'
            }

            pr_data = {
                'title': title,
                'head': head_branch,
                'base': base_branch,
                'body': body or ''
            }

            response = requests.post(api_url, headers=headers, json=pr_data, timeout=30)

            if response.status_code != 201:
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"GitHub API error: {response.json().get('message', 'Unknown error')}"
                )

            pr_url = response.json()['html_url']

        # Log successful PR creation
        audit_log = AuditLog(
            event_type='github_pr_created',
            user_action=f"Created PR: {title}",
            online_mode='online',
            metadata=json.dumps({
                'project_id': project_id,
                'title': title,
                'base_branch': base_branch,
                'head_branch': head_branch,
                'pr_url': pr_url
            })
        )
        db.add(audit_log)
        db.commit()

        return {
            "success": True,
            "message": "Pull request created successfully",
            "pr_url": pr_url,
            "title": title,
            "base": base_branch,
            "head": head_branch
        }

    except subprocess.TimeoutExpired:
        raise HTTPException(status_code=504, detail="PR creation timed out")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PR creation failed: {str(e)}")
