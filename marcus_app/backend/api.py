"""
FastAPI backend for Marcus.
Main API routes and application setup.
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form, Cookie, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, RedirectResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import json

from ..core.database import get_db, init_db, ACTIVE_MOUNT
from ..core.models import (
    Class, Assignment, Artifact, ExtractedText, Plan, AuditLog, SystemConfig,
    Claim, ClaimVerification, InboxItem, Deadline, TextChunk, StudyPack
)
from ..core.schemas import (
    ClassCreate, ClassResponse,
    AssignmentCreate, AssignmentUpdate, AssignmentResponse,
    ArtifactResponse, ExtractedTextResponse,
    PlanCreate, PlanResponse,
    AuditLogResponse, OnlineModeToggle, SystemStatus,
    ClaimResponse, ClaimVerificationCreate, ClaimVerificationResponse,
    InboxItemResponse, InboxClassifyAction,
    DeadlineResponse, CalendarExportRequest,
    SearchRequest, SearchResultResponse, ChunkResponse, ChunkContextResponse,
    LoginRequest, LoginResponse, SetupPasswordRequest, ChangePasswordRequest, SessionInfoResponse,
    StudyPackResponse, StudyPackCreateRequest
)
from ..services.file_service import FileService
from ..services.extraction_service import ExtractionService
from ..services.plan_service import PlanService
from ..services.export_service import ExportService
from ..services.claim_service import ClaimService
from ..services.inbox_service import InboxService
from ..services.deadline_service import DeadlineService
from ..services.chunking_service import ChunkingService
from ..services.search_service import SearchService
from ..services.auth_service import AuthService
from ..services.token_service import TokenService

# Load environment configuration
from dotenv import load_dotenv
import os
load_dotenv(Path(__file__).parent.parent.parent / "marcus.env")

# Paths - ALWAYS use ACTIVE_MOUNT (M:\Marcus or dev storage/packaging_temp)
# Don't rely on env vars since they're hardcoded to M:\
BASE_PATH = Path(__file__).parent.parent.parent
VAULT_PATH = ACTIVE_MOUNT / "vault"
PROJECTS_PATH = BASE_PATH / "projects"
EXPORTS_PATH = BASE_PATH / "exports"
INBOX_PATH = BASE_PATH / "inbox"
FRONTEND_PATH = BASE_PATH / "marcus_app" / "frontend"

# Ensure directories exist
VAULT_PATH.mkdir(exist_ok=True, parents=True)
PROJECTS_PATH.mkdir(exist_ok=True, parents=True)
EXPORTS_PATH.mkdir(exist_ok=True, parents=True)
INBOX_PATH.mkdir(exist_ok=True, parents=True)

# Initialize services
file_service = FileService(VAULT_PATH)
extraction_service = ExtractionService()
export_service = ExportService(EXPORTS_PATH)
claim_service = ClaimService()
inbox_service = InboxService(INBOX_PATH)
deadline_service = DeadlineService()
chunking_service = ChunkingService()
search_service = SearchService()
auth_service = AuthService()

# Create FastAPI app
app = FastAPI(title="Marcus API", version="0.36.0")


# ============================================================================
# AUTHENTICATION DEPENDENCY
# ============================================================================

def get_current_session(session_token: Optional[str] = Cookie(None, alias="marcus_session")) -> str:
    """
    Dependency to require authentication.
    Raises 401 if not authenticated.
    """
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(
            status_code=401,
            detail="Not authenticated. Please log in."
        )
    return session_token


# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()
    print("=" * 70)
    print("Marcus v0.36 - Auth Wall Enabled")
    print("=" * 70)
    print(f"Vault: {VAULT_PATH}")
    print(f"Projects: {PROJECTS_PATH}")
    print(f"Exports: {EXPORTS_PATH}")
    print("")
    print("Security features:")
    print("  - Encrypted storage (VeraCrypt)")
    print("  - Password authentication (Argon2id)")
    print("  - Auto-lock on idle (15 minutes)")
    print("  - Session-based access control")
    print("=" * 70)


# ============================================================================
# HEALTH CHECK ENDPOINT (Public - no auth required)
# ============================================================================

@app.get("/health")
async def health_check():
    """
    Health check endpoint for monitoring and launcher verification.
    Returns immediately without requiring authentication or database.
    Used by desktop launcher to verify backend is running.
    """
    return {
        "status": "ok",
        "version": app.version,
        "service": app.title
    }


# ============================================================================
# AUTHENTICATION ENDPOINTS (Public)
# ============================================================================

@app.get("/api/auth/status", response_model=SessionInfoResponse)
def get_auth_status(
    session_token: Optional[str] = Cookie(None, alias="marcus_session"),
    db: Session = Depends(get_db)
):
    """Check authentication status (public endpoint)."""
    if session_token and auth_service.validate_session(session_token):
        session_info = auth_service.get_session_info(session_token)
        return SessionInfoResponse(
            authenticated=True,
            user_id=session_info["user_id"],
            idle_seconds=session_info["idle_seconds"],
            session_timeout_minutes=15
        )

    # Check if password is set up
    has_password = auth_service.has_password_set(db)

    return SessionInfoResponse(
        authenticated=False,
        user_id=None,
        idle_seconds=None,
        session_timeout_minutes=15
    )


@app.post("/api/auth/setup", response_model=LoginResponse)
def setup_password(
    request: SetupPasswordRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """First-time password setup (only works if no password set)."""
    if auth_service.has_password_set(db):
        raise HTTPException(status_code=400, detail="Password already set up")

    if request.password != request.confirm_password:
        raise HTTPException(status_code=400, detail="Passwords do not match")

    try:
        auth_service.setup_password(request.password, db)

        # Auto-login after setup
        token = auth_service.create_session()
        response.set_cookie(
            key="marcus_session",
            value=token,
            httponly=True,
            samesite="strict",
            secure=False  # Set to True in production with HTTPS
        )

        return LoginResponse(
            success=True,
            message="Password set up successfully",
            session_token=token
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/api/auth/login", response_model=LoginResponse)
def login(
    request: LoginRequest,
    response: Response,
    db: Session = Depends(get_db)
):
    """Login with password."""
    if not auth_service.has_password_set(db):
        raise HTTPException(status_code=400, detail="Password not set up. Use /api/auth/setup first.")

    if not auth_service.verify_password(request.password, db):
        raise HTTPException(status_code=401, detail="Incorrect password")

    # v0.42: Derive encryption key from password for token storage
    try:
        TokenService.set_encryption_key(request.password, db)
    except Exception as e:
        print(f"Warning: Failed to initialize token encryption: {e}")

    # Create session
    token = auth_service.create_session()
    response.set_cookie(
        key="marcus_session",
        value=token,
        httponly=True,
        samesite="strict",
        secure=False  # Set to True in production with HTTPS
    )

    return LoginResponse(
        success=True,
        message="Login successful",
        session_token=token
    )


@app.post("/api/auth/logout")
def logout(
    response: Response,
    session_token: str = Depends(get_current_session)
):
    """Logout and invalidate session."""
    auth_service.invalidate_session(session_token)
    TokenService.clear_encryption_key()  # v0.42: Clear encryption key on logout
    response.delete_cookie(key="marcus_session")
    return {"success": True, "message": "Logged out successfully"}


@app.post("/api/auth/lock")
def lock_session(
    response: Response,
    session_token: str = Depends(get_current_session)
):
    """Lock session (same as logout but semantically different)."""
    auth_service.invalidate_session(session_token)
    TokenService.clear_encryption_key()  # v0.42: Clear encryption key on lock
    response.delete_cookie(key="marcus_session")
    return {"success": True, "message": "Session locked"}


@app.post("/api/auth/change-password")
def change_password(
    request: ChangePasswordRequest,
    session_token: str = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Change password (requires current password)."""
    if request.new_password != request.confirm_new_password:
        raise HTTPException(status_code=400, detail="New passwords do not match")

    try:
        success = auth_service.change_password(
            request.old_password,
            request.new_password,
            db
        )
        if not success:
            raise HTTPException(status_code=401, detail="Incorrect old password")

        return {"success": True, "message": "Password changed successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ============================================================================
# SYSTEM ENDPOINTS
# ============================================================================

@app.get("/api/status", response_model=SystemStatus, dependencies=[Depends(get_current_session)])
def get_status(db: Session = Depends(get_db)):
    """Get system status and statistics."""
    online_mode_config = db.query(SystemConfig).filter(
        SystemConfig.key == "online_mode"
    ).first()

    online_mode = False
    if online_mode_config and online_mode_config.value == "true":
        online_mode = True

    total_classes = db.query(Class).count()
    total_assignments = db.query(Assignment).count()
    total_artifacts = db.query(Artifact).count()

    return SystemStatus(
        online_mode=online_mode,
        db_path=str(BASE_PATH / "storage" / "marcus.db"),
        vault_path=str(VAULT_PATH),
        total_classes=total_classes,
        total_assignments=total_assignments,
        total_artifacts=total_artifacts
    )


@app.post("/api/online-mode")
def toggle_online_mode(toggle: OnlineModeToggle, db: Session = Depends(get_db)):
    """Toggle online mode on/off."""
    config = db.query(SystemConfig).filter(
        SystemConfig.key == "online_mode"
    ).first()

    if not config:
        config = SystemConfig(key="online_mode", value="false")
        db.add(config)

    config.value = "true" if toggle.enabled else "false"

    # Log the toggle
    audit_log = AuditLog(
        event_type="online_mode_toggled",
        online_mode="online" if toggle.enabled else "offline",
        user_action=f"Online mode {'enabled' if toggle.enabled else 'disabled'}",
        extra_data=json.dumps({"enabled": toggle.enabled})
    )
    db.add(audit_log)

    db.commit()

    return {"online_mode": toggle.enabled, "message": f"Online mode {'enabled' if toggle.enabled else 'disabled'}"}


# ============================================================================
# CLASS ENDPOINTS
# ============================================================================

@app.get("/api/classes", response_model=List[ClassResponse])
def list_classes(db: Session = Depends(get_db)):
    """List all classes."""
    classes = db.query(Class).order_by(Class.created_at.desc()).all()
    return classes


@app.post("/api/classes", response_model=ClassResponse)
def create_class(class_data: ClassCreate, db: Session = Depends(get_db)):
    """Create a new class."""
    # Check if code already exists
    existing = db.query(Class).filter(Class.code == class_data.code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Class code already exists")

    new_class = Class(code=class_data.code, name=class_data.name)
    db.add(new_class)
    db.commit()
    db.refresh(new_class)

    # Create project directory
    class_dir = PROJECTS_PATH / class_data.code
    class_dir.mkdir(exist_ok=True)

    return new_class


@app.get("/api/classes/{class_id}", response_model=ClassResponse)
def get_class(class_id: int, db: Session = Depends(get_db)):
    """Get a specific class."""
    cls = db.query(Class).filter(Class.id == class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")
    return cls


# ============================================================================
# ASSIGNMENT ENDPOINTS
# ============================================================================

@app.get("/api/assignments", response_model=List[AssignmentResponse])
def list_assignments(class_id: Optional[int] = None, db: Session = Depends(get_db)):
    """List all assignments, optionally filtered by class."""
    query = db.query(Assignment)
    if class_id:
        query = query.filter(Assignment.class_id == class_id)
    assignments = query.order_by(Assignment.due_date.asc()).all()
    return assignments


@app.post("/api/assignments", response_model=AssignmentResponse)
def create_assignment(assignment_data: AssignmentCreate, db: Session = Depends(get_db)):
    """Create a new assignment."""
    # Verify class exists
    cls = db.query(Class).filter(Class.id == assignment_data.class_id).first()
    if not cls:
        raise HTTPException(status_code=404, detail="Class not found")

    new_assignment = Assignment(**assignment_data.dict())
    db.add(new_assignment)
    db.commit()
    db.refresh(new_assignment)

    return new_assignment


@app.get("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
def get_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Get a specific assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    return assignment


@app.patch("/api/assignments/{assignment_id}", response_model=AssignmentResponse)
def update_assignment(
    assignment_id: int,
    update_data: AssignmentUpdate,
    db: Session = Depends(get_db)
):
    """Update an assignment."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    update_dict = update_data.dict(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(assignment, key, value)

    db.commit()
    db.refresh(assignment)
    return assignment


# ============================================================================
# ARTIFACT ENDPOINTS
# ============================================================================

@app.get("/api/assignments/{assignment_id}/artifacts", response_model=List[ArtifactResponse])
def list_artifacts(assignment_id: int, db: Session = Depends(get_db)):
    """List all artifacts for an assignment."""
    artifacts = db.query(Artifact).filter(
        Artifact.assignment_id == assignment_id
    ).order_by(Artifact.created_at.desc()).all()
    return artifacts


@app.post("/api/assignments/{assignment_id}/artifacts", response_model=ArtifactResponse)
async def upload_artifact(
    assignment_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """Upload a file artifact to an assignment."""
    # Verify assignment exists
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Read file content
    file_content = await file.read()

    # Save file
    artifact = file_service.save_file(
        file_content=file_content,
        original_filename=file.filename,
        assignment_id=assignment_id,
        db=db
    )

    # Log the upload
    audit_log = AuditLog(
        event_type="file_uploaded",
        online_mode="offline",
        user_action=f"Uploaded file: {file.filename}",
        extra_data=json.dumps({
            "artifact_id": artifact.id,
            "file_size": artifact.file_size,
            "file_type": artifact.file_type
        })
    )
    db.add(audit_log)
    db.commit()

    return artifact


# ============================================================================
# EXTRACTION ENDPOINTS
# ============================================================================

@app.post("/api/artifacts/{artifact_id}/extract", response_model=ExtractedTextResponse)
def extract_text(artifact_id: int, db: Session = Depends(get_db)):
    """Extract text from an artifact."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Check if already extracted
    existing = db.query(ExtractedText).filter(
        ExtractedText.artifact_id == artifact_id
    ).first()

    if existing:
        return existing

    # Perform extraction
    extracted = extraction_service.extract_from_artifact(artifact, db)

    # Log the extraction
    audit_log = AuditLog(
        event_type="text_extracted",
        online_mode="offline",
        user_action=f"Extracted text from: {artifact.original_filename}",
        extra_data=json.dumps({
            "artifact_id": artifact_id,
            "extraction_method": extracted.extraction_method,
            "extraction_status": extracted.extraction_status
        })
    )
    db.add(audit_log)
    db.commit()

    return extracted


@app.get("/api/artifacts/{artifact_id}/extracted", response_model=List[ExtractedTextResponse])
def get_extracted_text(artifact_id: int, db: Session = Depends(get_db)):
    """Get extracted text for an artifact."""
    extracted_texts = db.query(ExtractedText).filter(
        ExtractedText.artifact_id == artifact_id
    ).all()
    return extracted_texts


# ============================================================================
# PLAN ENDPOINTS
# ============================================================================

@app.post("/api/plans", response_model=PlanResponse)
def generate_plan(plan_data: PlanCreate, db: Session = Depends(get_db)):
    """Generate a plan for an assignment."""
    assignment = db.query(Assignment).filter(
        Assignment.id == plan_data.assignment_id
    ).first()

    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Check online mode
    if plan_data.use_online_mode:
        online_config = db.query(SystemConfig).filter(
            SystemConfig.key == "online_mode"
        ).first()

        if not online_config or online_config.value != "true":
            raise HTTPException(
                status_code=403,
                detail="Online mode is disabled. Enable it first to use online features."
            )

    # Generate plan
    plan_service = PlanService(online_mode=plan_data.use_online_mode)
    plan = plan_service.generate_plan(assignment, db)

    return plan


@app.get("/api/assignments/{assignment_id}/plans", response_model=List[PlanResponse])
def list_plans(assignment_id: int, db: Session = Depends(get_db)):
    """List all plans for an assignment."""
    plans = db.query(Plan).filter(
        Plan.assignment_id == assignment_id
    ).order_by(Plan.created_at.desc()).all()
    return plans


# ============================================================================
# AUDIT LOG ENDPOINTS
# ============================================================================

@app.get("/api/audit-logs", response_model=List[AuditLogResponse])
def list_audit_logs(limit: int = 50, db: Session = Depends(get_db)):
    """List recent audit logs."""
    logs = db.query(AuditLog).order_by(
        AuditLog.timestamp.desc()
    ).limit(limit).all()
    return logs


# ============================================================================
# EXPORT ENDPOINTS
# ============================================================================

@app.post("/api/assignments/{assignment_id}/export")
def export_assignment(assignment_id: int, db: Session = Depends(get_db)):
    """Export assignment bundle as ZIP."""
    assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")

    # Generate export
    zip_path = export_service.export_assignment_bundle(assignment, db)

    # Log the export
    audit_log = AuditLog(
        event_type="assignment_exported",
        online_mode="offline",
        user_action=f"Exported assignment: {assignment.title}",
        extra_data=json.dumps({
            "assignment_id": assignment_id,
            "export_path": str(zip_path)
        })
    )
    db.add(audit_log)
    db.commit()

    return FileResponse(
        path=zip_path,
        filename=zip_path.name,
        media_type="application/zip"
    )


# ============================================================================
# V0.2: ANSWER CONTRACTS ENDPOINTS
# ============================================================================

@app.get("/api/plans/{plan_id}/claims", response_model=List[ClaimResponse])
def get_plan_claims(plan_id: int, db: Session = Depends(get_db)):
    """Get all claims for a plan with supporting evidence."""
    claims = db.query(Claim).filter(Claim.plan_id == plan_id).all()
    return claims


@app.post("/api/claims/{claim_id}/verify", response_model=ClaimVerificationResponse)
def verify_claim(
    claim_id: int,
    verification: ClaimVerificationCreate,
    db: Session = Depends(get_db)
):
    """User verifies or invalidates a claim."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    result = claim_service.verify_claim(
        claim_id=claim_id,
        verification_result=verification.verification_result,
        verification_method=verification.verification_method,
        notes=verification.notes,
        db=db
    )

    # Log verification
    audit_log = AuditLog(
        event_type="claim_verified",
        online_mode="offline",
        user_action=f"Verified claim: {verification.verification_result}",
        extra_data=json.dumps({
            "claim_id": claim_id,
            "result": verification.verification_result
        })
    )
    db.add(audit_log)
    db.commit()

    return result


@app.get("/api/claims/{claim_id}/verification-suggestions")
def get_verification_suggestions(claim_id: int, db: Session = Depends(get_db)):
    """Get suggestions for how to verify a claim."""
    claim = db.query(Claim).filter(Claim.id == claim_id).first()
    if not claim:
        raise HTTPException(status_code=404, detail="Claim not found")

    suggestions = claim_service.get_verification_suggestions(claim)
    return {"claim_id": claim_id, "suggestions": suggestions}


# ============================================================================
# V0.2: INBOX & AUTO-CLASSIFICATION ENDPOINTS
# ============================================================================

@app.get("/api/inbox", response_model=List[InboxItemResponse])
def list_inbox_items(status: Optional[str] = None, db: Session = Depends(get_db)):
    """List inbox items, optionally filtered by status."""
    query = db.query(InboxItem)
    if status:
        query = query.filter(InboxItem.status == status)
    items = query.order_by(InboxItem.created_at.desc()).all()
    return items


@app.post("/api/inbox/upload", response_model=InboxItemResponse)
async def upload_to_inbox(file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Drop a file into the inbox.
    Auto-classifier will suggest class/assignment.
    """
    file_content = await file.read()

    inbox_item = inbox_service.add_to_inbox(
        file_content=file_content,
        filename=file.filename,
        db=db
    )

    # Log the upload
    audit_log = AuditLog(
        event_type="inbox_upload",
        online_mode="offline",
        user_action=f"Uploaded to inbox: {file.filename}",
        extra_data=json.dumps({
            "inbox_item_id": inbox_item.id,
            "suggested_class_id": inbox_item.suggested_class_id,
            "confidence": inbox_item.classification_confidence
        })
    )
    db.add(audit_log)
    db.commit()

    return inbox_item


@app.post("/api/inbox/{inbox_item_id}/classify", response_model=ArtifactResponse)
def classify_inbox_item(
    inbox_item_id: int,
    action: InboxClassifyAction,
    db: Session = Depends(get_db)
):
    """
    User confirms or corrects classification.
    Moves file from inbox to proper assignment.
    """
    inbox_item = db.query(InboxItem).filter(InboxItem.id == inbox_item_id).first()
    if not inbox_item:
        raise HTTPException(status_code=404, detail="Inbox item not found")

    # Update file service vault path
    inbox_service_instance = InboxService(INBOX_PATH)
    artifact = inbox_service_instance.classify_item(
        inbox_item_id=inbox_item_id,
        class_id=action.class_id,
        assignment_id=action.assignment_id,
        create_new_assignment=action.create_new_assignment,
        new_assignment_title=action.new_assignment_title,
        db=db
    )

    # Log classification
    audit_log = AuditLog(
        event_type="inbox_classified",
        online_mode="offline",
        user_action=f"Classified inbox item to assignment {action.assignment_id}",
        extra_data=json.dumps({
            "inbox_item_id": inbox_item_id,
            "artifact_id": artifact.id
        })
    )
    db.add(audit_log)
    db.commit()

    return artifact


# ============================================================================
# V0.2: DEADLINE & CALENDAR ENDPOINTS
# ============================================================================

@app.post("/api/artifacts/{artifact_id}/extract-deadlines", response_model=List[DeadlineResponse])
def extract_deadlines(artifact_id: int, db: Session = Depends(get_db)):
    """Extract deadlines from a syllabus or assignment document."""
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    deadlines = deadline_service.extract_deadlines_from_artifact(artifact, db)

    # Log extraction
    audit_log = AuditLog(
        event_type="deadlines_extracted",
        online_mode="offline",
        user_action=f"Extracted deadlines from: {artifact.original_filename}",
        extra_data=json.dumps({
            "artifact_id": artifact_id,
            "deadline_count": len(deadlines)
        })
    )
    db.add(audit_log)
    db.commit()

    return deadlines


@app.get("/api/deadlines", response_model=List[DeadlineResponse])
def list_deadlines(
    class_id: Optional[int] = None,
    upcoming_only: bool = False,
    db: Session = Depends(get_db)
):
    """List deadlines, optionally filtered by class or upcoming dates."""
    from datetime import datetime

    query = db.query(Deadline)

    if class_id:
        query = query.filter(Deadline.class_id == class_id)

    if upcoming_only:
        query = query.filter(Deadline.due_date >= datetime.utcnow())

    deadlines = query.order_by(Deadline.due_date.asc()).all()
    return deadlines


@app.post("/api/calendar/export")
def export_calendar(
    request: CalendarExportRequest,
    db: Session = Depends(get_db)
):
    """Export deadlines and assignments to .ics calendar file."""
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    filename = f"marcus_calendar_{timestamp}.ics"
    output_path = EXPORTS_PATH / filename

    ics_path = deadline_service.export_to_ics(
        class_id=request.class_id,
        include_assignments=request.include_assignments,
        include_deadlines=request.include_deadlines,
        output_path=output_path,
        db=db
    )

    # Log export
    audit_log = AuditLog(
        event_type="calendar_exported",
        online_mode="offline",
        user_action="Exported calendar to .ics",
        extra_data=json.dumps({
            "class_id": request.class_id,
            "filename": filename
        })
    )
    db.add(audit_log)
    db.commit()

    return FileResponse(
        path=ics_path,
        filename=filename,
        media_type="text/calendar"
    )


# ============================================================================
# V0.3: SEARCH & CHUNKING ENDPOINTS
# ============================================================================

@app.post("/api/search", response_model=List[SearchResultResponse])
def search_chunks(request: SearchRequest, db: Session = Depends(get_db)):
    """
    Search through text chunks with hybrid ranking.
    Falls back to FTS5 if embeddings unavailable.
    """
    results = search_service.search(
        query=request.query,
        class_id=request.class_id,
        assignment_id=request.assignment_id,
        limit=request.limit,
        db=db
    )

    # Log search
    audit_log = AuditLog(
        event_type="search_executed",
        online_mode="offline",
        query=request.query,
        user_action=f"Searched: {request.query}",
        extra_data=json.dumps({
            "class_id": request.class_id,
            "assignment_id": request.assignment_id,
            "result_count": len(results),
            "search_method": results[0]['search_method'] if results else 'none'
        })
    )
    db.add(audit_log)
    db.commit()

    return results


@app.get("/api/chunks/{chunk_id}", response_model=ChunkContextResponse)
def get_chunk_context(chunk_id: int, context_chunks: int = 1, db: Session = Depends(get_db)):
    """
    Get a chunk with surrounding context.
    Used when user clicks a search result.
    """
    context = search_service.get_chunk_with_context(
        chunk_id=chunk_id,
        context_chunks=context_chunks,
        db=db
    )

    if not context:
        raise HTTPException(status_code=404, detail="Chunk not found")

    return context


@app.post("/api/artifacts/{artifact_id}/chunk")
def chunk_artifact(artifact_id: int, db: Session = Depends(get_db)):
    """
    Chunk an artifact's extracted text.
    Usually called automatically after extraction.
    """
    artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")

    # Get extracted text
    extracted_texts = db.query(ExtractedText).filter(
        ExtractedText.artifact_id == artifact_id
    ).all()

    if not extracted_texts:
        raise HTTPException(status_code=400, detail="No extracted text found for this artifact")

    # Chunk each extracted text
    total_chunks = 0
    for extracted_text in extracted_texts:
        chunks = chunking_service.chunk_extracted_text(extracted_text, db)
        total_chunks += len(chunks)

    # Log chunking
    audit_log = AuditLog(
        event_type="artifact_chunked",
        online_mode="offline",
        user_action=f"Chunked artifact: {artifact.original_filename}",
        extra_data=json.dumps({
            "artifact_id": artifact_id,
            "chunk_count": total_chunks
        })
    )
    db.add(audit_log)
    db.commit()

    return {
        "artifact_id": artifact_id,
        "extracted_text_count": len(extracted_texts),
        "chunk_count": total_chunks
    }


@app.post("/api/chunks/batch-process")
def batch_chunk_all(force_rechunk: bool = False, db: Session = Depends(get_db)):
    """
    Process all extracted texts that don't have chunks yet.
    Useful for migrations and bulk operations.
    """
    chunked_count = chunking_service.chunk_all_extracted_texts(db, force_rechunk)

    audit_log = AuditLog(
        event_type="batch_chunking",
        online_mode="offline",
        user_action=f"Batch chunked {chunked_count} extracted texts",
        extra_data=json.dumps({
            "force_rechunk": force_rechunk,
            "chunked_count": chunked_count
        })
    )
    db.add(audit_log)
    db.commit()

    return {
        "chunked_count": chunked_count,
        "message": "Batch chunking complete"
    }


# ============================================================================
# V0.38: STUDY PACK ENDPOINTS
# ============================================================================

@app.post("/api/study-packs", response_model=StudyPackResponse)
def create_study_pack(
    request: StudyPackCreateRequest,
    session_token: str = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """
    Generate a study pack blueprint from an assessment artifact.
    
    Creates:
    - Topics with skills and lessons
    - Citations to grounding material
    - Study checklist
    """
    from ..services.study_pack_service import BlueprintGenerator
    
    # Verify artifact exists and belongs to correct assignment
    artifact = db.query(Artifact).filter(
        Artifact.id == request.artifact_id,
        Artifact.assignment_id == request.assignment_id
    ).first()
    
    if not artifact:
        raise HTTPException(status_code=404, detail="Artifact not found")
    
    # Verify assignment is in correct class
    assignment = db.query(Assignment).filter(
        Assignment.id == request.assignment_id,
        Assignment.class_id == request.class_id
    ).first()
    
    if not assignment:
        raise HTTPException(status_code=404, detail="Assignment not found")
    
    # Check if chunks exist (chunking must be done first)
    chunk_count = db.query(TextChunk).filter(
        TextChunk.artifact_id == request.artifact_id
    ).count()
    
    if chunk_count == 0:
        raise HTTPException(
            status_code=400,
            detail="Artifact must be chunked before generating study pack. Run /api/chunks/{artifact_id} first."
        )
    
    try:
        # Generate blueprint
        generator = BlueprintGenerator()
        study_pack = generator.generate_blueprint(
            artifact_id=request.artifact_id,
            assignment_id=request.assignment_id,
            class_id=request.class_id,
            db=db
        )
        
        # Log creation
        audit_log = AuditLog(
            event_type="study_pack_created",
            online_mode="offline",
            user_action=f"Created study pack for {artifact.original_filename}",
            extra_data=json.dumps({
                "study_pack_id": study_pack.id,
                "artifact_id": request.artifact_id,
                "topic_count": len(study_pack.topics)
            })
        )
        db.add(audit_log)
        db.commit()
        
        return study_pack
    
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to generate study pack: {str(e)}")


@app.get("/api/study-packs/{study_pack_id}", response_model=StudyPackResponse)
def get_study_pack(
    study_pack_id: int,
    session_token: str = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Retrieve a study pack by ID."""
    study_pack = db.query(StudyPack).filter(StudyPack.id == study_pack_id).first()
    
    if not study_pack:
        raise HTTPException(status_code=404, detail="Study pack not found")
    
    return study_pack


@app.get("/api/assignments/{assignment_id}/study-packs")
def list_study_packs_for_assignment(
    assignment_id: int,
    session_token: str = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """List all study packs for an assignment."""
    packs = db.query(StudyPack).filter(
        StudyPack.assignment_id == assignment_id
    ).all()
    
    return [StudyPackResponse.model_validate(pack) for pack in packs]


@app.put("/api/study-packs/{study_pack_id}")
def update_study_pack_status(
    study_pack_id: int,
    status: str,
    session_token: str = Depends(get_current_session),
    db: Session = Depends(get_db)
):
    """Update study pack status (draft, published, archived)."""
    study_pack = db.query(StudyPack).filter(StudyPack.id == study_pack_id).first()
    
    if not study_pack:
        raise HTTPException(status_code=404, detail="Study pack not found")
    
    if status not in ["draft", "published", "archived"]:
        raise HTTPException(status_code=400, detail="Invalid status")
    
    study_pack.status = status
    db.commit()
    
    return study_pack


# ============================================================================
# V0.51: CHAT ENDPOINTS (MVP HEURISTIC AGENT)
# ============================================================================

class ChatMessage(BaseModel):
    message: str
    attachmentId: Optional[str] = None

class ChatResponse(BaseModel):
    reply: str
    actions: List[dict] = []
    created: List[dict] = []

class UploadResponse(BaseModel):
    artifactId: str
    metadata: dict

@app.post("/api/chat/upload", response_model=UploadResponse)
async def upload_file_for_chat(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload a file for chat context.
    Returns artifact ID and metadata for use in chat messages.
    """
    try:
        file_content = await file.read()
        
        # Create artifact in database
        artifact = Artifact(
            original_filename=file.filename,
            file_type=file.content_type or "application/octet-stream",
            file_size=len(file_content),
            extraction_status="pending"
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)
        
        # Save file to vault
        vault_file = VAULT_PATH / f"artifact_{artifact.id}_{file.filename}"
        vault_file.write_bytes(file_content)
        
        # Try to extract text if it's a PDF or text file
        extracted_text = None
        if file.filename.lower().endswith('.pdf'):
            try:
                from ..services.extraction_service import ExtractionService
                extraction_svc = ExtractionService(VAULT_PATH)
                text_content = extraction_svc.extract_text_from_pdf(vault_file)
                extracted_text = ExtractedText(
                    artifact_id=artifact.id,
                    extracted_text=text_content,
                    extraction_method="pdfplumber",
                    extraction_status="success"
                )
                db.add(extracted_text)
            except Exception as e:
                print(f"PDF extraction error: {e}")
                extracted_text = ExtractedText(
                    artifact_id=artifact.id,
                    extracted_text=file.filename,
                    extraction_method="none",
                    extraction_status="failed"
                )
                db.add(extracted_text)
        elif file.filename.lower().endswith(('.txt', '.md')):
            try:
                text_content = file_content.decode('utf-8', errors='ignore')
                extracted_text = ExtractedText(
                    artifact_id=artifact.id,
                    extracted_text=text_content,
                    extraction_method="text",
                    extraction_status="success"
                )
                db.add(extracted_text)
            except Exception as e:
                print(f"Text extraction error: {e}")
        
        db.commit()
        
        # Log upload
        audit_log = AuditLog(
            event_type="chat_file_uploaded",
            online_mode="offline",
            user_action=f"Uploaded file via chat: {file.filename}",
            extra_data=json.dumps({
                "artifact_id": artifact.id,
                "file_size": artifact.file_size,
                "file_type": artifact.file_type
            })
        )
        db.add(audit_log)
        db.commit()
        
        return UploadResponse(
            artifactId=str(artifact.id),
            metadata={
                "filename": file.filename,
                "size": len(file_content),
                "type": file.content_type,
                "extractedText": extracted_text.extracted_text if extracted_text else None
            }
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"File upload failed: {str(e)}")

@app.post("/api/chat", response_model=ChatResponse)
def chat_endpoint(
    request: ChatMessage,
    db: Session = Depends(get_db)
):
    """
    MVP heuristic chat agent.
    Parses user message and returns actions to take.
    No LLM required - keyword-based matching for MVP.
    """
    msg = request.message.strip().lower()
    attachment_id = request.attachmentId
    reply = ""
    actions = []
    created = []
    
    # Parse message for commands
    if any(word in msg for word in ["create class", "add class", "new class"]):
        # Extract class name (heuristic: text after "class")
        parts = request.message.split("class", 1)
        if len(parts) > 1:
            class_name = parts[1].strip().strip("\"'")
            if class_name and len(class_name) > 1:
                # Create the class
                code = class_name.upper().replace(" ", "_")[:10]
                new_class = Class(code=code, name=class_name)
                db.add(new_class)
                db.commit()
                db.refresh(new_class)
                
                # Create project directory
                class_dir = PROJECTS_PATH / code
                class_dir.mkdir(exist_ok=True)
                
                created.append({
                    "type": "class",
                    "id": new_class.id,
                    "name": new_class.name,
                    "code": new_class.code
                })
                reply = f"✓ Created class **{new_class.name}** ({new_class.code}). Ready for assignments and materials."
                actions.append({
                    "type": "open_class",
                    "label": f"Open {new_class.code}",
                    "class_id": new_class.id
                })
    
    elif any(word in msg for word in ["add task", "create task", "new task", "add assignment"]):
        # Extract task title
        parts = request.message.split(":", 1)
        task_title = parts[-1].strip() if len(parts) > 1 else "Untitled Task"
        
        # Get first class or create dummy
        cls = db.query(Class).first()
        if not cls:
            cls = Class(code="DEFAULT", name="Default Class")
            db.add(cls)
            db.commit()
        
        # Create assignment
        from datetime import datetime, timedelta
        new_task = Assignment(
            class_id=cls.id,
            title=task_title,
            due_date=datetime.utcnow() + timedelta(days=7),
            status="created"
        )
        db.add(new_task)
        db.commit()
        db.refresh(new_task)
        
        created.append({
            "type": "task",
            "id": new_task.id,
            "title": new_task.title,
            "due_date": new_task.due_date.isoformat()
        })
        reply = f"✓ Created task **{new_task.title}** due in 7 days."
        actions.append({
            "type": "open_item",
            "label": "View Task",
            "item_id": new_task.id
        })
    
    elif any(word in msg for word in ["set this up", "process", "import"]) and attachment_id:
        # Try to extract classes/deadlines from uploaded file
        try:
            artifact = db.query(Artifact).filter(Artifact.id == int(attachment_id)).first()
            if artifact:
                # Look for extracted text
                extracted = db.query(ExtractedText).filter(
                    ExtractedText.artifact_id == artifact.id
                ).first()
                
                if extracted and extracted.extracted_text:
                    text = extracted.extracted_text.lower()
                    
                    # Simple heuristics: look for class patterns
                    class_name = None
                    if "course" in text:
                        class_name = "Course from " + artifact.original_filename.split('.')[0]
                    elif "syllabus" in text:
                        class_name = "Syllabus - " + artifact.original_filename.split('.')[0]
                    else:
                        class_name = artifact.original_filename.split('.')[0]
                    
                    # Create class
                    code = class_name.upper().replace(" ", "_")[:10]
                    new_class = Class(code=code, name=class_name)
                    db.add(new_class)
                    db.commit()
                    db.refresh(new_class)
                    
                    # Create project directory
                    class_dir = PROJECTS_PATH / code
                    class_dir.mkdir(exist_ok=True)
                    
                    created.append({
                        "type": "class",
                        "id": new_class.id,
                        "name": new_class.name,
                        "code": new_class.code
                    })
                    
                    reply = f"✓ Imported **{new_class.name}** from {artifact.original_filename}. Added to classes."
                    actions.append({
                        "type": "open_class",
                        "label": f"View {new_class.code}",
                        "class_id": new_class.id
                    })
                else:
                    reply = "Could not extract text from file. Try uploading a PDF or text file."
        except Exception as e:
            reply = f"Error processing file: {str(e)}"
    
    elif any(word in msg for word in ["what's next", "what is next", "upcoming", "show me"]):
        # Show upcoming deadlines and tasks
        from datetime import datetime, timedelta
        upcoming = db.query(Assignment).filter(
            Assignment.due_date <= datetime.utcnow() + timedelta(days=30),
            Assignment.due_date >= datetime.utcnow()
        ).order_by(Assignment.due_date.asc()).limit(5).all()
        
        if upcoming:
            reply = "📋 **Next up:**\n"
            for task in upcoming:
                days_left = (task.due_date - datetime.utcnow()).days
                reply += f"- **{task.title}** ({days_left} days)\n"
            
            for task in upcoming:
                actions.append({
                    "type": "open_item",
                    "label": f"{task.title}",
                    "item_id": task.id
                })
        else:
            reply = "✓ No upcoming tasks in the next 30 days. You're all caught up!"
    
    elif any(word in msg for word in ["show inbox", "inbox", "pending"]):
        # List inbox items
        inbox_items = db.query(InboxItem).filter(
            InboxItem.status == "pending"
        ).order_by(InboxItem.created_at.desc()).limit(5).all()
        
        if inbox_items:
            reply = f"📥 **Inbox ({len(inbox_items)})**\n"
            for item in inbox_items:
                reply += f"- {item.filename}\n"
            
            actions.append({
                "type": "view_inbox",
                "label": f"View Inbox ({len(inbox_items)})"
            })
        else:
            reply = "✓ Inbox is empty!"
    
    elif any(word in msg for word in ["help", "?"]):
        reply = """**Chat Commands:**
- "create class NAME" - Create a new class
- "add task TITLE" - Add a task/assignment
- "set this up" (with file) - Import from syllabus
- "what's next" - Show upcoming deadlines
- "show inbox" - View pending files
- Or just ask anything! Chat is learning."""
    
    else:
        # Fallback response
        reply = f"I received: **{request.message}**\n\nI'm learning! Try: create class, add task, upload a file and say 'set this up', or type 'help'."
        
        # Show quick stats
        cls_count = db.query(Class).count()
        task_count = db.query(Assignment).count()
        inbox_count = db.query(InboxItem).filter(InboxItem.status == "pending").count()
        
        if cls_count > 0 or task_count > 0:
            reply += f"\n\nQuick stats: **{cls_count}** classes, **{task_count}** tasks, **{inbox_count}** inbox items."
    
    # Log chat
    audit_log = AuditLog(
        event_type="chat_message",
        online_mode="offline",
        user_action=request.message,
        extra_data=json.dumps({
            "attachment_id": attachment_id,
            "action_count": len(actions),
            "created_count": len(created)
        })
    )
    db.add(audit_log)
    db.commit()
    
    return ChatResponse(
        reply=reply,
        actions=actions,
        created=created
    )


# ============================================================================
# SERVE FRONTEND
# ============================================================================

# Login page (public)
@app.get("/login")
async def serve_login():
    login_path = FRONTEND_PATH / "login.html"
    if login_path.exists():
        return FileResponse(login_path)
    return {"error": "Login page not found"}


# Root - redirect based on auth status
@app.get("/")
async def serve_frontend(
    request: Request,
    session_token: Optional[str] = Cookie(None, alias="marcus_session")
):
    # Check if authenticated
    if not session_token or not auth_service.validate_session(session_token):
        return RedirectResponse(url="/login")

    # Serve main app
    index_path = FRONTEND_PATH / "index.html"
    if index_path.exists():
        return FileResponse(index_path)
    return {"message": "Marcus API is running. Frontend not found."}


# Protected static files - require auth for all UI pages
class AuthStaticFiles(StaticFiles):
    async def __call__(self, scope, receive, send):
        request = Request(scope, receive=receive)

        # Allow login page
        if request.url.path.endswith("login.html"):
            return await super().__call__(scope, receive, send)

        # Check auth for all other pages
        session_token = request.cookies.get("marcus_session")
        if not session_token or not auth_service.validate_session(session_token):
            # Redirect to login
            response = RedirectResponse(url="/login")
            await response(scope, receive, send)
            return

        return await super().__call__(scope, receive, send)


# Mount static files with auth check
if FRONTEND_PATH.exists():
    app.mount("/static", AuthStaticFiles(directory=str(FRONTEND_PATH)), name="static")


# ============================================================================
# V0.39: PROJECT MANAGEMENT
# ============================================================================

# Include projects router
from .projects_routes import router as projects_router
app.include_router(projects_router)


# ============================================================================
# V0.40: DEVELOPMENT MODE
# ============================================================================

# Include dev mode routes (offline Git operations, changesets)
from .dev_mode_routes import router as dev_mode_router
app.include_router(dev_mode_router)

# Include online mode routes (push, PR creation - gated behind Online Mode)
from .online_routes import router as online_router
app.include_router(online_router)

# Include life-graph routes (knowledge graph visualization - feature-flagged)
from .life_graph_routes import router as life_graph_router
app.include_router(life_graph_router)

# ============================================================================
# V0.43: PR AUTOPILOT
# ============================================================================

# Include PR autopilot routes (offline PR text suggestion from staged diffs)
from .pr_autopilot_routes import router as pr_autopilot_router
app.include_router(pr_autopilot_router)

# ============================================================================
# V0.44-ALPHA: MISSIONS + BOXES WORKFLOW ENGINE
# ============================================================================

# Include mission routes (workflow orchestration system)
from .mission_routes import router as mission_router
app.include_router(mission_router)

# ============================================================================
# V0.46: MISSION OPERATIONS PANELS
# ============================================================================

# Include artifact routes (artifact listing + note creation for operation panels)
from .artifact_routes import router as artifact_router
app.include_router(artifact_router)

# ============================================================================
# V0.47a: UNIVERSAL INBOX + QUICK ADD
# ============================================================================

# Include inbox routes (unified capture/routing system)
from .inbox_routes import router as inbox_router
app.include_router(inbox_router)

# ============================================================================
# V0.47b: CENTRAL AGENT CHAT
# ============================================================================

# Include agent routes (command-driven conversational layer)
from .agent_routes import router as agent_router
app.include_router(agent_router)


# Project preview endpoint (at root, not under /api/)
@app.get("/preview/{project_name}/{file_path:path}")
async def preview_project_file(
    project_name: str,
    file_path: str,
    db: Session = Depends(get_db),
    session_token: Optional[str] = Cookie(None, alias="marcus_session")
):
    """Preview a file from a project (for web projects)."""
    if not session_token or not auth_service.validate_session(session_token):
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    from ..services.project_service import ProjectService
    
    project = ProjectService.get_project_by_name(db, project_name)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    project_root = Path(project.root_path)
    file_path = file_path.strip()
    if ".." in file_path or file_path.startswith("/"):
        raise HTTPException(status_code=403, detail="Invalid path")
    
    full_path = project_root / file_path
    
    try:
        full_path.resolve().relative_to(project_root.resolve())
    except ValueError:
        raise HTTPException(status_code=403, detail="Path outside project")
    
    if not full_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    
    def get_media_type(ext: str) -> str:
        types = {
            ".html": "text/html", ".htm": "text/html", ".css": "text/css",
            ".js": "application/javascript", ".json": "application/json",
            ".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".gif": "image/gif", ".svg": "image/svg+xml", ".ico": "image/x-icon"
        }
        return types.get(ext.lower(), "application/octet-stream")
    
    return FileResponse(full_path, media_type=get_media_type(full_path.suffix))
