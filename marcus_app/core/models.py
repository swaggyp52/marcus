"""
Core data models for Marcus.
SQLAlchemy ORM models for all entities.
"""

from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Text, ForeignKey, Boolean, Enum, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()


class ClassStatus(str, enum.Enum):
    ACTIVE = "active"
    ARCHIVED = "archived"


class AssignmentStatus(str, enum.Enum):
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class OnlineMode(str, enum.Enum):
    OFFLINE = "offline"
    ONLINE = "online"


class Class(Base):
    __tablename__ = "classes"

    id = Column(Integer, primary_key=True)
    code = Column(String(50), nullable=False, unique=True)  # e.g., "26SPECE34701"
    name = Column(String(200), nullable=False)  # e.g., "26SP Embedded System Design 01"
    status = Column(String(20), default=ClassStatus.ACTIVE.value)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignments = relationship("Assignment", back_populates="class_obj", cascade="all, delete-orphan")


class Assignment(Base):
    __tablename__ = "assignments"

    id = Column(Integer, primary_key=True)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    title = Column(String(200), nullable=False)
    description = Column(Text)
    due_date = Column(DateTime)
    status = Column(String(20), default=AssignmentStatus.TODO.value)
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    class_obj = relationship("Class", back_populates="assignments")
    artifacts = relationship("Artifact", back_populates="assignment", cascade="all, delete-orphan")
    plans = relationship("Plan", back_populates="assignment", cascade="all, delete-orphan")


class Artifact(Base):
    __tablename__ = "artifacts"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # pdf, image, docx, txt, code, etc.
    file_size = Column(Integer)
    file_hash = Column(String(64))  # SHA-256
    created_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="artifacts")
    extracted_texts = relationship("ExtractedText", back_populates="artifact", cascade="all, delete-orphan")


class ExtractedText(Base):
    __tablename__ = "extracted_texts"

    id = Column(Integer, primary_key=True)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False)
    content = Column(Text, nullable=False)
    extraction_method = Column(String(50))  # ocr, pdf, docx, plain
    extraction_status = Column(String(20))  # success, failed, partial
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    artifact = relationship("Artifact", back_populates="extracted_texts")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    title = Column(String(200))
    steps = Column(Text)  # JSON array of step objects
    required_materials = Column(Text)  # JSON array
    output_formats = Column(Text)  # JSON array
    draft_outline = Column(Text)
    effort_estimate = Column(String(10))  # S, M, L
    risks_unknowns = Column(Text)
    assumptions = Column(Text)
    confidence = Column(String(10))  # low, medium, high
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = relationship("Assignment", back_populates="plans")
    claims = relationship("Claim", back_populates="plan", cascade="all, delete-orphan")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String(50))  # online_query, file_upload, plan_generated, etc.
    online_mode = Column(String(20))  # offline, online
    query = Column(Text)
    domains_accessed = Column(Text)  # JSON array
    results_summary = Column(Text)
    citations = Column(Text)  # JSON array of citation objects
    user_action = Column(String(100))
    extra_data = Column(Text)  # JSON for extra fields (renamed from metadata)
    created_at = Column(DateTime, default=datetime.utcnow)


class SystemConfig(Base):
    __tablename__ = "system_config"

    id = Column(Integer, primary_key=True)
    key = Column(String(100), unique=True, nullable=False)
    value = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


# ============================================================================
# V0.2: ANSWER CONTRACTS - Provenance & Trust
# ============================================================================

class Claim(Base):
    """
    Individual atomic claims within a plan or answer.
    Each claim is verifiable and traceable to source material.
    """
    __tablename__ = "claims"

    id = Column(Integer, primary_key=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)
    statement = Column(Text, nullable=False)  # The atomic claim
    confidence = Column(String(10), nullable=False)  # low, medium, high
    verification_status = Column(String(20), default="unverified")  # unverified, verified, invalid
    created_at = Column(DateTime, default=datetime.utcnow)
    verified_at = Column(DateTime)

    plan = relationship("Plan", back_populates="claims")
    supports = relationship("ClaimSupport", back_populates="claim", cascade="all, delete-orphan")
    verifications = relationship("ClaimVerification", back_populates="claim", cascade="all, delete-orphan")


class ClaimSupport(Base):
    """
    Links a claim to specific source material (extracted text chunks).
    Provides exact citation with page/section references.
    """
    __tablename__ = "claim_supports"

    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False)
    extracted_text_id = Column(Integer, ForeignKey("extracted_texts.id"))

    # Citation details
    chunk_id = Column(String(100))  # For semantic search chunks (v0.3)
    page_number = Column(Integer)
    section_title = Column(String(200))
    quote = Column(Text)  # Exact supporting quote from source
    relevance_score = Column(Integer)  # 1-10 how well this supports the claim

    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("Claim", back_populates="supports")
    artifact = relationship("Artifact")
    extracted_text = relationship("ExtractedText")


class ClaimVerification(Base):
    """
    User feedback on claim accuracy.
    Feeds into system learning and confidence adjustment.
    """
    __tablename__ = "claim_verifications"

    id = Column(Integer, primary_key=True)
    claim_id = Column(Integer, ForeignKey("claims.id"), nullable=False)
    verification_result = Column(String(20), nullable=False)  # verified, invalid, uncertain
    verification_method = Column(String(100))  # manual_check, cross_reference, experiment, etc.
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    claim = relationship("Claim", back_populates="verifications")


class TextChunk(Base):
    """
    Structured chunks of extracted text for better retrieval (v0.3).
    Each chunk is a semantic unit (paragraph, section, page).
    Denormalized for fast filtering without joins.
    """
    __tablename__ = "text_chunks"

    id = Column(Integer, primary_key=True)
    extracted_text_id = Column(Integer, ForeignKey("extracted_texts.id"), nullable=False)
    chunk_index = Column(Integer, nullable=False)  # Order within document
    content = Column(Text, nullable=False)

    # Denormalized foreign keys for fast filtering
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))

    # Metadata for retrieval
    chunk_type = Column(String(50))  # paragraph, heading, page, code_block
    page_number = Column(Integer)
    section_title = Column(String(200))
    word_count = Column(Integer)
    char_start = Column(Integer)  # Start position in original text
    char_end = Column(Integer)    # End position in original text

    # For semantic search (v0.3)
    embedding_vector = Column(Text)  # JSON serialized vector
    embedding_model = Column(String(100))  # Track which model generated embedding

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    extracted_text = relationship("ExtractedText")
    artifact = relationship("Artifact")
    assignment = relationship("Assignment")
    class_obj = relationship("Class")


class InboxItem(Base):
    """
    Temporary holding area for uploaded files before classification.
    Auto-classifier suggests class/assignment, user confirms or corrects.
    """
    __tablename__ = "inbox_items"

    id = Column(Integer, primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size = Column(Integer)
    file_hash = Column(String(64))

    # Auto-classification suggestions
    suggested_class_id = Column(Integer, ForeignKey("classes.id"))
    suggested_assignment_id = Column(Integer, ForeignKey("assignments.id"))
    classification_confidence = Column(String(10))  # low, medium, high
    classification_reasoning = Column(Text)  # Why this suggestion

    # Status
    status = Column(String(20), default="pending")  # pending, classified, archived

    created_at = Column(DateTime, default=datetime.utcnow)
    classified_at = Column(DateTime)

    suggested_class = relationship("Class", foreign_keys=[suggested_class_id])
    suggested_assignment = relationship("Assignment", foreign_keys=[suggested_assignment_id])


class Deadline(Base):
    """
    Extracted deadlines from syllabi and assignment descriptions.
    Feeds calendar view and .ics export.
    """
    __tablename__ = "deadlines"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"))
    class_id = Column(Integer, ForeignKey("classes.id"))

    title = Column(String(200), nullable=False)
    due_date = Column(DateTime, nullable=False)
    deadline_type = Column(String(50))  # assignment, exam, project, reading

    # Extraction provenance
    source_artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    extraction_confidence = Column(String(10))  # low, medium, high
    extracted_text = Column(Text)  # Original text that mentioned this deadline

    # Reminders
    reminder_sent = Column(Boolean, default=False)

    created_at = Column(DateTime, default=datetime.utcnow)

    assignment = relationship("Assignment", foreign_keys=[assignment_id])
    class_obj = relationship("Class", foreign_keys=[class_id])
    source_artifact = relationship("Artifact", foreign_keys=[source_artifact_id])

# ============================================================================
# V0.38: STUDY PACKS - Blueprint-driven tutoring
# ============================================================================

class StudyPack(Base):
    """
    Study pack generated from an assessment (exam, quiz, homework, review sheet).
    Contains topics, skills, lessons, and study checklist.
    """
    __tablename__ = "study_packs"

    id = Column(Integer, primary_key=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id"), nullable=False)
    class_id = Column(Integer, ForeignKey("classes.id"), nullable=False)
    artifact_id = Column(Integer, ForeignKey("artifacts.id"), nullable=False)

    # Study pack metadata
    title = Column(String(255), nullable=False)  # Derived from artifact
    description = Column(Text)  # Auto-generated summary
    
    # Status
    status = Column(String(20), default="draft")  # draft, published, archived
    quality_score = Column(Integer)  # 1-10 confidence in blueprint quality
    
    # Blueprint data (JSON structures)
    topics_json = Column(Text)  # JSON array of topic objects
    skills_json = Column(Text)  # JSON array of skill objects
    lessons_json = Column(Text)  # JSON array of lesson objects
    checklist_json = Column(Text)  # JSON array of checklist items
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    assignment = relationship("Assignment", foreign_keys=[assignment_id])
    class_obj = relationship("Class", foreign_keys=[class_id])
    artifact = relationship("Artifact", foreign_keys=[artifact_id])
    topics = relationship("StudyTopic", back_populates="study_pack", cascade="all, delete-orphan")


class StudyTopic(Base):
    """
    Individual topic within a study pack.
    Links to skills and lessons.
    """
    __tablename__ = "study_topics"

    id = Column(Integer, primary_key=True)
    study_pack_id = Column(Integer, ForeignKey("study_packs.id"), nullable=False)

    # Topic definition
    title = Column(String(255), nullable=False)
    order = Column(Integer)  # Display order within pack
    description = Column(Text)  # What it is (one sentence)

    # Metadata
    is_grounded = Column(Boolean, default=True)  # All citations are traceable
    confidence = Column(String(20))  # low, medium, high
    weighting = Column(String(20))  # low, medium, high - importance in assessment

    created_at = Column(DateTime, default=datetime.utcnow)

    study_pack = relationship("StudyPack", back_populates="topics")
    skills = relationship("StudySkill", back_populates="topic", cascade="all, delete-orphan")
    lessons = relationship("StudyLesson", back_populates="topic", cascade="all, delete-orphan")
    citations = relationship("StudyCitation", back_populates="topic", cascade="all, delete-orphan")


class StudySkill(Base):
    """
    Skills required to master a topic.
    Types: Derive (apply), Conceptual (understand), Memorize (recall).
    """
    __tablename__ = "study_skills"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("study_topics.id"), nullable=False)

    # Skill definition
    type = Column(String(50), nullable=False)  # derive, conceptual, memorize
    description = Column(String(255), nullable=False)
    order = Column(Integer)

    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("StudyTopic", back_populates="skills")


class StudyLesson(Base):
    """
    Lesson content for a topic.
    Contains subpoints, common mistakes, and citations.
    """
    __tablename__ = "study_lessons"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("study_topics.id"), nullable=False)

    # Lesson content
    what_it_is = Column(Text, nullable=False)  # One sentence definition
    key_subpoints = Column(Text)  # JSON array of bullet points
    common_mistakes = Column(Text)  # JSON array of mistake descriptions

    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("StudyTopic", back_populates="lessons")


class StudyCitation(Base):
    """
    Citation linking a study topic to specific chunks in the assessment.
    Provides traceability and grounding.
    """
    __tablename__ = "study_citations"

    id = Column(Integer, primary_key=True)
    topic_id = Column(Integer, ForeignKey("study_topics.id"), nullable=False)
    chunk_id = Column(Integer, ForeignKey("text_chunks.id"))

    # Citation metadata
    artifact_id = Column(Integer, ForeignKey("artifacts.id"))
    page_number = Column(Integer)
    section_title = Column(String(200))
    quote = Column(Text)  # Exact text from source
    
    # Relevance
    relevance_score = Column(Integer)  # 1-10 how well this grounds the topic
    is_ungrounded = Column(Boolean, default=False)  # True if no citation found

    created_at = Column(DateTime, default=datetime.utcnow)

    topic = relationship("StudyTopic", back_populates="citations")
    chunk = relationship("TextChunk", foreign_keys=[chunk_id])
    artifact = relationship("Artifact", foreign_keys=[artifact_id])


class StudyChecklistItem(Base):
    """
    Individual step in the study checklist.
    Ordered, with effort estimates and self-check prompts.
    """
    __tablename__ = "study_checklist_items"

    id = Column(Integer, primary_key=True)
    study_pack_id = Column(Integer, ForeignKey("study_packs.id"), nullable=False)

    # Step definition
    order = Column(Integer, nullable=False)
    step_description = Column(Text, nullable=False)
    effort_estimate = Column(String(10))  # S, M, L
    self_check_prompt = Column(Text)  # Question for student to verify learning

    created_at = Column(DateTime, default=datetime.utcnow)

    study_pack = relationship("StudyPack", foreign_keys=[study_pack_id])


# ============================================================================
# V0.39: PROJECTS - Local Development Workspace
# ============================================================================

class ProjectType(str, enum.Enum):
    WEB = 'web'
    SOFTWARE = 'software'
    DOCS = 'docs'


class Project(Base):
    '''
    A development project stored locally in encrypted vault.
    Can be a website, application, or documentation.
    '''
    __tablename__ = 'projects'

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False, unique=True)  # e.g., 'RedByte'
    description = Column(Text)
    project_type = Column(String(50), default=ProjectType.WEB.value)  # web, software, docs
    root_path = Column(String(500), nullable=False)  # M:\Marcus\projects\RedByte\
    
    # Status and metadata
    status = Column(String(20), default='active')  # active, archived
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    files = relationship('ProjectFile', back_populates='project', cascade='all, delete-orphan')
    notes = relationship('ProjectNote', back_populates='project', cascade='all, delete-orphan')
    changesets = relationship('DevChangeSet', back_populates='project', cascade='all, delete-orphan')


class ProjectFile(Base):
    '''
    A file within a project.
    Tracked for metadata; content stored on disk.
    '''
    __tablename__ = 'project_files'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # Path relative to project root (e.g., 'index.html', 'css/style.css')
    relative_path = Column(String(500), nullable=False)
    
    # File metadata
    file_type = Column(String(50))  # html, css, js, json, md, text, etc.
    file_size = Column(Integer)  # bytes
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    modified_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship('Project', back_populates='files')


class ProjectNote(Base):
    '''
    Markdown notes for a project.
    Used for architecture, TODOs, design decisions.
    '''
    __tablename__ = 'project_notes'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # Content
    title = Column(String(255))
    content = Column(Text)  # Markdown
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship('Project', back_populates='notes')


# ============================================================================
# V0.40: DEVELOPMENT MODE MODELS
# ============================================================================

class DevChangeSet(Base):
    """
    Offline changeset for Git workflow.
    Represents a bundle of commits ready to push as PR.
    """
    __tablename__ = 'dev_changesets'

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey('projects.id'), nullable=False)
    
    # Git metadata
    branch_name = Column(String(255), nullable=False)
    commit_count = Column(Integer, default=0)
    
    # Status: draft, ready, pushed, pr_created, archived
    status = Column(String(50), default='draft')
    
    # PR preparation
    title = Column(String(500))
    description = Column(Text)  # PR description / commit message
    
    # Snapshot of changes
    diff_snapshot = Column(Text)  # Full unified diff
    changed_files = Column(Text)  # JSON list of files changed
    
    # Audit trail for online push
    pushed_at = Column(DateTime, nullable=True)
    pushed_commit_hash = Column(String(50))  # SHA-1 after push
    pr_url = Column(String(500))  # GitHub PR URL after creation
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    project = relationship('Project', back_populates='changesets')
    files = relationship('DevChangeSetFile', back_populates='changeset', cascade='all, delete-orphan')


class DevChangeSetFile(Base):
    """
    Individual file change in a changeset.
    Tracks which files were added/modified/deleted.
    """
    __tablename__ = 'dev_changeset_files'

    id = Column(Integer, primary_key=True)
    changeset_id = Column(Integer, ForeignKey('dev_changesets.id'), nullable=False)
    
    # File info
    relative_path = Column(String(500), nullable=False)
    
    # Change type: added, modified, deleted, renamed
    change_type = Column(String(50))
    
    # Diff content
    diff_content = Column(Text)  # Full diff for this file
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)

    changeset = relationship('DevChangeSet', back_populates='files')


class GitHubToken(Base):
    """
    Encrypted GitHub API tokens for PR creation.
    Stored encrypted inside VeraCrypt volume.
    NEVER expose plaintext in API responses.
    """
    __tablename__ = 'github_tokens'

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    
    # ENCRYPTED - never plaintext
    encrypted_token = Column(Text, nullable=False)
    
    # Token metadata
    expires_at = Column(DateTime, nullable=True)
    scope = Column(String(500))  # GitHub token scope: repo, gist, etc
    
    # Audit
    created_at = Column(DateTime, default=datetime.utcnow)
    last_used_at = Column(DateTime, nullable=True)


class LifeGraphNode(Base):
    """
    Node in the knowledge graph (3D/2D visualization).
    Represents a class, project, study pack, or artifact.
    Feature-flagged (disabled by default).
    """
    __tablename__ = 'life_graph_nodes'

    id = Column(Integer, primary_key=True)
    
    # Node type: class, project, study_pack, artifact, assignment, etc
    node_type = Column(String(50), nullable=False)
    entity_id = Column(Integer)  # ID in corresponding table
    
    # Display
    label = Column(String(255))
    description = Column(Text)
    
    # Position (for 2D/3D visualization)
    x = Column(Integer, default=0)
    y = Column(Integer, default=0)
    z = Column(Integer, default=0)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class LifeGraphEdge(Base):
    """
    Edge in the knowledge graph.
    Represents relationships between nodes.
    Feature-flagged (disabled by default).
    """
    __tablename__ = 'life_graph_edges'

    id = Column(Integer, primary_key=True)
    
    # Nodes
    source_node_id = Column(Integer, ForeignKey('life_graph_nodes.id'), nullable=False)
    target_node_id = Column(Integer, ForeignKey('life_graph_nodes.id'), nullable=False)
    
    # Edge type: contains, references, requires, related_to
    edge_type = Column(String(50))

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)


# ============================================================================
# V0.44-ALPHA: MISSIONS + BOXES WORKFLOW ENGINE
# ============================================================================

class MissionState(str, enum.Enum):
    DRAFT = "draft"
    ACTIVE = "active"
    BLOCKED = "blocked"
    DONE = "done"


class BoxState(str, enum.Enum):
    IDLE = "idle"
    READY = "ready"
    RUNNING = "running"
    BLOCKED = "blocked"
    DONE = "done"
    ERROR = "error"


class Mission(Base):
    """
    Mission: A workflow graph of boxes operating on artifacts.
    Example: Exam Prep Mission, Code Review Mission, Research Mission.
    """
    __tablename__ = "missions"

    id = Column(Integer, primary_key=True)
    name = Column(String(255), nullable=False)
    mission_type = Column(String(50), nullable=False)  # exam_prep, code_review, research
    state = Column(String(20), default=MissionState.DRAFT.value)

    # Optional links to existing entities
    class_id = Column(Integer, ForeignKey("classes.id"))
    assignment_id = Column(Integer, ForeignKey("assignments.id"))

    # Metadata (JSON)
    metadata_json = Column(Text)  # Mission-specific config

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    class_obj = relationship("Class", foreign_keys=[class_id])
    assignment = relationship("Assignment", foreign_keys=[assignment_id])
    boxes = relationship("MissionBox", back_populates="mission", cascade="all, delete-orphan")
    artifacts = relationship("MissionArtifact", back_populates="mission", cascade="all, delete-orphan")
    practice_sessions = relationship("PracticeSession", back_populates="mission", cascade="all, delete-orphan")


class MissionBox(Base):
    """
    Box: A workflow node that performs one operation.
    Types: inbox, extract, ask, practice, checker, citations
    """
    __tablename__ = "mission_boxes"

    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    box_type = Column(String(50), nullable=False)  # inbox, extract, ask, practice, checker, citations
    order_index = Column(Integer, nullable=False)  # Execution order
    state = Column(String(20), default=BoxState.IDLE.value)

    # Configuration (JSON)
    config_json = Column(Text)  # Box-specific settings

    # Execution tracking
    last_run_at = Column(DateTime)
    last_error = Column(Text)

    # Canvas positioning (for v0.45, unused in v0.44-alpha)
    position_json = Column(Text)  # {x, y} coordinates

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    mission = relationship("Mission", back_populates="boxes")
    artifacts = relationship("MissionArtifact", back_populates="box", cascade="all, delete-orphan")


class MissionArtifact(Base):
    """
    Artifact produced by a box or ingested into a mission.
    Types: document, qa, practice_session, verification, citation, note
    """
    __tablename__ = "mission_artifacts"

    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)
    box_id = Column(Integer, ForeignKey("mission_boxes.id"))  # Null if ingested from outside
    artifact_type = Column(String(50), nullable=False)  # document, qa, practice_session, verification, citation, note

    title = Column(String(255), nullable=False)
    content_json = Column(Text)  # Artifact data (JSON or markdown)
    source_refs_json = Column(Text)  # Citations/chunk IDs/artifact IDs

    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    mission = relationship("Mission", back_populates="artifacts")
    box = relationship("MissionBox", back_populates="artifacts")


class PracticeSession(Base):
    """
    Practice session created by PracticeBox.
    Contains questions and tracks user progress.
    """
    __tablename__ = "practice_sessions"

    id = Column(Integer, primary_key=True)
    mission_id = Column(Integer, ForeignKey("missions.id"), nullable=False)

    state = Column(String(20), default="active")  # active, completed
    score_json = Column(Text)  # {attempted: N, correct: N, incorrect: N}
    notes = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    mission = relationship("Mission", back_populates="practice_sessions")
    items = relationship("PracticeItem", back_populates="session", cascade="all, delete-orphan")


class PracticeItem(Base):
    """
    Individual practice question within a session.
    CheckerBox updates state and adds verification claims.
    """
    __tablename__ = "practice_items"

    id = Column(Integer, primary_key=True)
    session_id = Column(Integer, ForeignKey("practice_sessions.id"), nullable=False)

    prompt_md = Column(Text, nullable=False)  # Question text (markdown)
    expected_answer = Column(Text)  # Expected answer (if available)
    user_answer = Column(Text)  # User's submitted answer

    state = Column(String(20), default="unanswered")  # unanswered, correct, incorrect
    checks_json = Column(Text)  # Unit checks, reasoning checks
    citations_json = Column(Text)  # Citations for this question

    created_at = Column(DateTime, default=datetime.utcnow)
    answered_at = Column(DateTime)

    # Relationships
    session = relationship("PracticeSession", back_populates="items")


class Item(Base):
    """
    Universal item for capture/routing workflow (v0.47a).
    Replaces fragmented capture points with unified inbox.
    """
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)

    # Core fields
    item_type = Column(String(50), nullable=False)  # note|task|document|event|artifact_ref|mission_ref
    title = Column(String(500), nullable=False)
    content_md = Column(Text)
    content_json = Column(Text)  # flexible storage for metadata

    # Routing/classification
    status = Column(String(20), default="inbox")  # inbox|active|done|archived|snoozed
    context_kind = Column(String(20))  # class|project|personal|none
    context_id = Column(Integer)  # class_id or project_id if applicable
    confidence = Column(Float)  # 0.0-1.0 classification confidence
    suggested_route_json = Column(Text)  # what auto-classifier suggested

    # Organization
    tags_json = Column(Text)  # JSON array of tags
    links_json = Column(Text)  # references to artifact_ids, mission_ids, etc.
    pinned = Column(Integer, default=0)

    # Scheduling (for tasks/events)
    due_at = Column(DateTime)
    completed_at = Column(DateTime)
    snooze_until = Column(DateTime)

    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    filed_at = Column(DateTime)  # when moved from inbox to context