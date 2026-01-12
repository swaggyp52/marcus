"""
Suggestion Endpoints - v0.48

Provides autocomplete suggestions for:
- Class codes
- Project names
- Mission names
- Common commands
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from marcus_app.core.database import get_db
from marcus_app.core.models import Class, Project, Mission

router = APIRouter(prefix="/api/suggest", tags=["suggestions"])


# ============================================================================
# CLASS SUGGESTIONS
# ============================================================================

@router.get("/classes")
async def suggest_classes(
    q: str = Query("", min_length=1),
    db: Session = Depends(get_db),
    limit: int = 5
) -> List[str]:
    """
    Suggest class codes matching query.
    
    Example: GET /api/suggest/classes?q=PHYS
    Returns: ["PHYS214", "PHYS280", ...]
    """
    if not q or len(q) < 1:
        return []

    try:
        query_lower = q.lower()
        classes = db.query(Class).filter(
            Class.code.ilike(f"%{query_lower}%")
        ).limit(limit).all()
        
        # Return formatted suggestions: "CODE - Name"
        return [f"{c.code} - {c.name}" for c in classes]
    except Exception as e:
        print(f"Class suggestion error: {e}")
        return []


# ============================================================================
# PROJECT SUGGESTIONS
# ============================================================================

@router.get("/projects")
async def suggest_projects(
    q: str = Query("", min_length=1),
    db: Session = Depends(get_db),
    limit: int = 5
) -> List[str]:
    """
    Suggest project names matching query.
    
    Example: GET /api/suggest/projects?q=mark
    Returns: ["Marketing campaign", "Marking system", ...]
    """
    if not q or len(q) < 1:
        return []

    try:
        query_lower = q.lower()
        projects = db.query(Project).filter(
            Project.name.ilike(f"%{query_lower}%")
        ).limit(limit).all()
        
        return [p.name for p in projects]
    except Exception as e:
        print(f"Project suggestion error: {e}")
        return []


# ============================================================================
# MISSION SUGGESTIONS
# ============================================================================

@router.get("/missions")
async def suggest_missions(
    q: str = Query("", min_length=1),
    db: Session = Depends(get_db),
    limit: int = 5
) -> List[str]:
    """
    Suggest mission names matching query.
    
    Example: GET /api/suggest/missions?q=exam
    Returns: ["Exam prep for PHYS", "Exam review MATH", ...]
    """
    if not q or len(q) < 1:
        return []

    try:
        query_lower = q.lower()
        missions = db.query(Mission).filter(
            Mission.name.ilike(f"%{query_lower}%")
        ).limit(limit).all()
        
        return [m.name for m in missions]
    except Exception as e:
        print(f"Mission suggestion error: {e}")
        return []


# ============================================================================
# COMMAND SUGGESTIONS
# ============================================================================

COMMON_COMMANDS = [
    "add task",
    "add note",
    "add mission",
    "schedule meeting",
    "what's next?",
    "show inbox",
    "show missions",
    "what's due today?",
    "what's overdue?",
    "mark done",
    "clear inbox",
    "mission status",
    "create project",
    "show blocked",
    "help"
]


@router.get("/commands")
async def suggest_commands(
    q: str = Query("", min_length=1),
    limit: int = 8
) -> List[str]:
    """
    Suggest common commands matching query.
    
    Example: GET /api/suggest/commands?q=what
    Returns: ["what's next?", "what's due today?", "what's overdue?"]
    """
    if not q or len(q) < 1:
        return COMMON_COMMANDS[:limit]

    query_lower = q.lower()
    suggestions = [
        cmd for cmd in COMMON_COMMANDS
        if query_lower in cmd.lower()
    ]
    
    return suggestions[:limit]
