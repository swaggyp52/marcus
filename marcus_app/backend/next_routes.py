"""
Next Action Routes - v0.48

Endpoint for "What's next?" deterministic ranking.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from pydantic import BaseModel

from marcus_app.core.database import get_db
from marcus_app.services.next_action_service import NextActionService


router = APIRouter(prefix="/api/next", tags=["next"])


# ============================================================================
# MODELS
# ============================================================================

class ActionButton(BaseModel):
    label: str
    type: str  # "navigate" or "command"
    target: Optional[str] = None
    command: Optional[str] = None


class RecommendedAction(BaseModel):
    title: str
    description: str
    actions: List[ActionButton]


class ActionItem(BaseModel):
    id: int
    type: str
    title: str
    context: str
    due: Optional[str] = None
    reason: str
    status: str


class NextResponse(BaseModel):
    items: List[ActionItem]
    recommended_action: Optional[RecommendedAction]
    summary: str
    timestamp: str


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.get("/", response_model=NextResponse)
async def get_next_actions(
    db: Session = Depends(get_db),
    limit: int = 3
):
    """
    Get next actionable items using deterministic ranking.

    Returns top N items based on:
    1. Overdue deadlines
    2. Due in next 48h
    3. Pinned inbox items
    4. Blocked missions
    5. Active tasks not started

    Query Parameters:
    - limit: Number of items to return (default: 3)

    Response:
    {
        "items": [
            {
                "id": 123,
                "type": "task",
                "title": "Finish lab report",
                "context": "PHYS214",
                "due": "2024-01-15T17:00:00",
                "reason": "overdue",
                "status": "active"
            },
            ...
        ],
        "recommended_action": {
            "title": "Finish lab report",
            "description": "Start with: Finish lab report",
            "actions": [
                {"label": "Open Item", "type": "navigate", "target": "/tasks/123"},
                {"label": "Mark Done", "type": "command", "command": "mark 123 done"}
            ]
        },
        "summary": "1 overdue, 2 due soon",
        "timestamp": "2024-01-13T10:30:00.000000"
    }
    """
    service = NextActionService(db)
    result = service.get_next_actions(limit=limit)

    return NextResponse(
        items=[ActionItem(**item) for item in result["items"]],
        recommended_action=RecommendedAction(**result["recommended_action"]) if result.get("recommended_action") else None,
        summary=result["summary"],
        timestamp=result["timestamp"]
    )
