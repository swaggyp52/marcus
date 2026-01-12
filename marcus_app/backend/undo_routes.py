"""
Undo Routes - v0.48

API endpoints for undo functionality.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional

from marcus_app.core.database import get_db
from marcus_app.services.undo_service import UndoService


router = APIRouter(prefix="/api/undo", tags=["undo"])


# ============================================================================
# MODELS
# ============================================================================

class UndoResponse(BaseModel):
    success: bool
    message: str
    action_type: Optional[str] = None
    undone_id: Optional[int] = None


class UndoStatusResponse(BaseModel):
    undo_available: bool
    seconds_remaining: int
    last_action: Optional[str] = None
    action_type: Optional[str] = None


# ============================================================================
# ENDPOINTS
# ============================================================================

@router.post("/last", response_model=UndoResponse)
async def undo_last_action(db: Session = Depends(get_db)):
    """
    Undo the last action (if within 10-second window).

    Example response (success):
    {
        "success": true,
        "message": "Undid: Created task: Homework",
        "action_type": "create_item",
        "undone_id": 42
    }

    Example response (failure):
    {
        "success": false,
        "message": "No actions to undo"
    }
    """
    service = UndoService(db)
    result = service.undo_last_action()

    return UndoResponse(
        success=result["success"],
        message=result["message"],
        action_type=result.get("action_type"),
        undone_id=result.get("undone_id")
    )


@router.get("/status", response_model=UndoStatusResponse)
async def get_undo_status(db: Session = Depends(get_db)):
    """
    Get current undo status for UI display.

    Example response:
    {
        "undo_available": true,
        "seconds_remaining": 7,
        "last_action": "Created task: Homework",
        "action_type": "create_item"
    }
    """
    service = UndoService(db)
    status = service.get_status()

    return UndoStatusResponse(
        undo_available=status["undo_available"],
        seconds_remaining=status["seconds_remaining"],
        last_action=status["last_action"],
        action_type=status["action_type"]
    )
