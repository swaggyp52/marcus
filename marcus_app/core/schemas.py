"""
Pydantic schemas for API request/response validation.
"""

from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List


class ClassCreate(BaseModel):
    code: str
    name: str


class ClassResponse(BaseModel):
    id: int
    code: str
    name: str
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class AssignmentCreate(BaseModel):
    class_id: int
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    notes: Optional[str] = None


class AssignmentUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    status: Optional[str] = None
    notes: Optional[str] = None


class AssignmentResponse(BaseModel):
    id: int
    class_id: int
    title: str
    description: Optional[str]
    due_date: Optional[datetime]
    status: str
    notes: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ArtifactResponse(BaseModel):
    id: int
    assignment_id: int
    filename: str
    original_filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ExtractedTextResponse(BaseModel):
    id: int
    artifact_id: int
    content: str
    extraction_method: Optional[str]
    extraction_status: str
    error_message: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class PlanStep(BaseModel):
    order: int
    description: str
    effort: str  # S, M, L


class PlanCreate(BaseModel):
    assignment_id: int
    use_online_mode: bool = False


class PlanResponse(BaseModel):
    id: int
    assignment_id: int
    title: Optional[str]
    steps: Optional[str]
    required_materials: Optional[str]
    output_formats: Optional[str]
    draft_outline: Optional[str]
    effort_estimate: Optional[str]
    risks_unknowns: Optional[str]
    assumptions: Optional[str]
    confidence: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class AuditLogResponse(BaseModel):
    id: int
    timestamp: datetime
    event_type: str
    online_mode: str
    query: Optional[str]
    domains_accessed: Optional[str]
    user_action: Optional[str]

    class Config:
        from_attributes = True


class OnlineModeToggle(BaseModel):
    enabled: bool


class SystemStatus(BaseModel):
    online_mode: bool
    db_path: str
    vault_path: str
    total_classes: int
    total_assignments: int
    total_artifacts: int


# ============================================================================
# V0.2: ANSWER CONTRACTS SCHEMAS
# ============================================================================

class ClaimSupportResponse(BaseModel):
    id: int
    claim_id: int
    artifact_id: int
    page_number: Optional[int]
    section_title: Optional[str]
    quote: Optional[str]
    relevance_score: Optional[int]

    class Config:
        from_attributes = True


class ClaimVerificationCreate(BaseModel):
    verification_result: str  # verified, invalid, uncertain
    verification_method: Optional[str]
    notes: Optional[str]


class ClaimVerificationResponse(BaseModel):
    id: int
    claim_id: int
    verification_result: str
    verification_method: Optional[str]
    notes: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class ClaimResponse(BaseModel):
    id: int
    plan_id: int
    statement: str
    confidence: str
    verification_status: str
    created_at: datetime
    supports: List[ClaimSupportResponse] = []
    verifications: List[ClaimVerificationResponse] = []

    class Config:
        from_attributes = True


class InboxItemResponse(BaseModel):
    id: int
    filename: str
    file_type: Optional[str]
    file_size: Optional[int]
    suggested_class_id: Optional[int]
    suggested_assignment_id: Optional[int]
    classification_confidence: Optional[str]
    classification_reasoning: Optional[str]
    status: str
    created_at: datetime

    class Config:
        from_attributes = True


class InboxClassifyAction(BaseModel):
    class_id: Optional[int]
    assignment_id: Optional[int]
    create_new_assignment: bool = False
    new_assignment_title: Optional[str] = None


class DeadlineResponse(BaseModel):
    id: int
    assignment_id: Optional[int]
    class_id: Optional[int]
    title: str
    due_date: datetime
    deadline_type: Optional[str]
    extraction_confidence: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class CalendarExportRequest(BaseModel):
    class_id: Optional[int] = None
    include_assignments: bool = True
    include_deadlines: bool = True


# ============================================================================
# V0.3: SEARCH & CHUNKING SCHEMAS
# ============================================================================

class SearchRequest(BaseModel):
    query: str
    class_id: Optional[int] = None
    assignment_id: Optional[int] = None
    limit: int = 10


class ChunkResponse(BaseModel):
    id: int
    content: str
    chunk_index: int
    artifact_id: int
    section_title: Optional[str]
    page_number: Optional[int]
    word_count: Optional[int]

    class Config:
        from_attributes = True


class SearchResultResponse(BaseModel):
    chunk_id: int
    content: str
    snippet: str
    score: float
    artifact_filename: Optional[str]
    artifact_id: int
    section_title: Optional[str]
    page_number: Optional[int]
    class_id: Optional[int]
    assignment_id: Optional[int]
    search_method: str


class ChunkContextResponse(BaseModel):
    chunk: dict
    previous_chunks: List[dict]
    next_chunks: List[dict]
    artifact: Optional[dict]
    metadata: dict


class LoginRequest(BaseModel):
    password: str


class LoginResponse(BaseModel):
    success: bool
    message: str
    session_token: Optional[str] = None


class SetupPasswordRequest(BaseModel):
    password: str
    confirm_password: str


class ChangePasswordRequest(BaseModel):
    old_password: str
    new_password: str
    confirm_new_password: str


class SessionInfoResponse(BaseModel):
    authenticated: bool
    user_id: Optional[str] = None
    idle_seconds: Optional[float] = None
    session_timeout_minutes: int


# ============================================================================
# V0.38: STUDY PACK SCHEMAS
# ============================================================================

class StudySkillResponse(BaseModel):
    id: int
    type: str
    description: str
    order: Optional[int]

    class Config:
        from_attributes = True


class StudyLessonResponse(BaseModel):
    id: int
    what_it_is: str
    key_subpoints: Optional[List[str]]
    common_mistakes: Optional[List[str]]

    class Config:
        from_attributes = True


class StudyCitationResponse(BaseModel):
    id: int
    chunk_id: Optional[int]
    artifact_id: Optional[int]
    page_number: Optional[int]
    section_title: Optional[str]
    quote: Optional[str]
    relevance_score: Optional[int]
    is_ungrounded: bool

    class Config:
        from_attributes = True


class StudyTopicResponse(BaseModel):
    id: int
    title: str
    order: Optional[int]
    description: Optional[str]
    is_grounded: bool
    confidence: Optional[str]
    weighting: Optional[str]
    skills: List[StudySkillResponse]
    lessons: List[StudyLessonResponse]
    citations: List[StudyCitationResponse]

    class Config:
        from_attributes = True


class StudyChecklistItemResponse(BaseModel):
    id: int
    order: int
    step_description: str
    effort_estimate: Optional[str]
    self_check_prompt: Optional[str]

    class Config:
        from_attributes = True


class StudyPackResponse(BaseModel):
    id: int
    assignment_id: int
    class_id: int
    artifact_id: int
    title: str
    description: Optional[str]
    status: str
    quality_score: Optional[int]
    topics: List[StudyTopicResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StudyPackCreateRequest(BaseModel):
    assignment_id: int
    class_id: int
    artifact_id: int


# ============================================================================
# V0.39: PROJECTS - Schema Definitions
# ============================================================================


class ProjectFileResponse(BaseModel):
    """File metadata within a project."""
    id: int
    project_id: int
    relative_path: str
    file_type: Optional[str]
    file_size: Optional[int]
    created_at: datetime
    modified_at: datetime

    class Config:
        from_attributes = True


class ProjectNoteResponse(BaseModel):
    """Note within a project."""
    id: int
    project_id: int
    title: Optional[str]
    content: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectResponse(BaseModel):
    """Full project with all relationships."""
    id: int
    name: str
    description: Optional[str]
    project_type: str
    root_path: str
    status: str
    created_at: datetime
    updated_at: datetime
    files: List[ProjectFileResponse] = []
    notes: List[ProjectNoteResponse] = []

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    """Request to create a new project."""
    name: str
    description: Optional[str] = None
    project_type: str = 'web'


class ProjectUpdateRequest(BaseModel):
    """Request to update project metadata."""
    description: Optional[str] = None
    status: Optional[str] = None


class ProjectFileCreateRequest(BaseModel):
    """Request to create or update a project file."""
    relative_path: str
    content: str


class ProjectNoteCreateRequest(BaseModel):
    """Request to create a project note."""
    title: str
    content: str


class ProjectNoteUpdateRequest(BaseModel):
    """Request to update a project note."""
    title: Optional[str] = None
    content: Optional[str] = None


# ============================================================================
# V0.40: DEV MODE - SCHEMAS
# ============================================================================

class DevChangeSetFileResponse(BaseModel):
    """File within a changeset."""
    id: int
    relative_path: str
    change_type: Optional[str]
    diff_content: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class DevChangeSetResponse(BaseModel):
    """Complete changeset with files."""
    id: int
    project_id: int
    branch_name: str
    commit_count: int
    status: str
    title: Optional[str]
    description: Optional[str]
    diff_snapshot: Optional[str]
    changed_files: Optional[str]  # JSON
    pushed_at: Optional[datetime]
    pushed_commit_hash: Optional[str]
    pr_url: Optional[str]
    files: List[DevChangeSetFileResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DevChangeSetCreateRequest(BaseModel):
    """Request to create a changeset."""
    branch_name: str
    title: str
    description: Optional[str] = None


class DevChangeSetExportRequest(BaseModel):
    """Request to export changeset."""
    format: str = "patch"  # patch, diff, zip


class GitStatusResponse(BaseModel):
    """Git status of a project."""
    is_repo: bool
    current_branch: Optional[str]
    changed_files: List[str]
    staged_files: List[str]
    untracked_files: List[str]
    is_dirty: bool


class GitDiffResponse(BaseModel):
    """Git diff output."""
    summary: str  # --stat output
    diff: str  # Full unified diff


class GitBranchCreateRequest(BaseModel):
    """Request to create a branch."""
    branch_name: str
    from_branch: Optional[str] = None


class GitCommitRequest(BaseModel):
    """Request to commit changes."""
    message: str
    author_name: Optional[str] = None
    author_email: Optional[str] = None


class GitStageRequest(BaseModel):
    """Request to stage files."""
    files: List[str]


class GitPushRequest(BaseModel):
    """Request to push branch."""
    branch_name: str
    force: bool = False


class GitHubPRCreateRequest(BaseModel):
    """Request to create GitHub PR."""
    title: str
    body: Optional[str] = None
    target_branch: Optional[str] = None
    base_branch: str = "main"


class LifeGraphNodeResponse(BaseModel):
    """Node in knowledge graph."""
    id: int
    node_type: str
    entity_id: Optional[int]
    label: str
    description: str
    x: int
    y: int
    z: int


class LifeGraphEdgeResponse(BaseModel):
    """Edge in knowledge graph."""
    id: int
    source_node_id: int
    target_node_id: int
    edge_type: str


class LifeGraphResponse(BaseModel):
    """Complete knowledge graph."""
    nodes: List[LifeGraphNodeResponse]
    edges: List[LifeGraphEdgeResponse]
    node_count: int
    edge_count: int
    generated_at: datetime
