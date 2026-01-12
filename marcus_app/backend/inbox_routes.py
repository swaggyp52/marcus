"""
Inbox Routes - v0.47a

API endpoints for unified inbox and item management.
Supports Quick Add, Inbox workflow, and item operations.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from marcus_app.core.database import get_db
from marcus_app.core.models import Item
from marcus_app.services.item_classifier import classify_item, should_auto_file


router = APIRouter(prefix="/api/inbox", tags=["inbox"])


# ============================================================================
# AUTH DEPENDENCY
# ============================================================================

def require_auth():
    """Require authentication - stub for development."""
    # TODO: Integrate with existing auth service
    return True


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class QuickAddRequest(BaseModel):
    text: str
    filename: Optional[str] = None
    file_type: Optional[str] = None


class ItemResponse(BaseModel):
    id: int
    item_type: str
    title: str
    content_md: Optional[str]
    status: str
    context_kind: Optional[str]
    context_id: Optional[int]
    confidence: Optional[float]
    suggested_route_json: Optional[str]
    tags: List[str]
    pinned: bool
    due_at: Optional[str]
    created_at: str
    filed_at: Optional[str]


class AcceptItemRequest(BaseModel):
    item_id: int


class ChangeRouteRequest(BaseModel):
    item_id: int
    context_kind: str  # class|project|personal|none
    context_id: Optional[int] = None


class SnoozeItemRequest(BaseModel):
    item_id: int
    snooze_until: str  # ISO datetime


class PinItemRequest(BaseModel):
    item_id: int
    pinned: bool


# ============================================================================
# QUICK ADD ENDPOINT
# ============================================================================

@router.post("/quick-add")
async def quick_add_item(
    request: QuickAddRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Quick Add: Create item from text input with auto-classification.

    If confidence >= 0.90: auto-file to suggested context
    If confidence < 0.90: send to inbox for review
    """

    # Classify the item
    classification = classify_item(
        text=request.text,
        filename=request.filename,
        file_type=request.file_type,
        db=db
    )

    # Extract title (first line or up to 200 chars)
    lines = request.text.strip().split('\n')
    title = lines[0][:200] if lines else request.text[:200]
    content_md = request.text if len(lines) > 1 else None

    # Determine status based on confidence
    auto_filed = should_auto_file(classification['confidence'])
    status = 'active' if auto_filed else 'inbox'
    filed_at = datetime.utcnow() if auto_filed else None

    # Create item
    item = Item(
        item_type=classification['item_type'],
        title=title,
        content_md=content_md,
        status=status,
        context_kind=classification['context_kind'],
        context_id=classification['context_id'],
        confidence=classification['confidence'],
        suggested_route_json=json.dumps(classification),
        tags_json=json.dumps(classification['tags']),
        due_at=classification['due_at'],
        filed_at=filed_at,
        created_at=datetime.utcnow()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    return {
        'item_id': item.id,
        'auto_filed': auto_filed,
        'status': status,
        'classification': classification,
        'message': 'Auto-filed successfully' if auto_filed else 'Sent to inbox for review'
    }


# ============================================================================
# INBOX LIST ENDPOINT
# ============================================================================

@router.get("/items")
async def list_inbox_items(
    status: str = 'inbox',
    limit: int = 100,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    List items by status.

    Query params:
    - status: inbox|active|done|archived|snoozed (default: inbox)
    - limit: max items to return (default: 100)
    """

    query = db.query(Item).filter(Item.status == status)

    # Exclude snoozed items that haven't reached snooze_until
    if status == 'inbox':
        query = query.filter(
            (Item.snooze_until.is_(None)) |
            (Item.snooze_until <= datetime.utcnow())
        )

    items = query.order_by(Item.created_at.desc()).limit(limit).all()

    return [
        ItemResponse(
            id=item.id,
            item_type=item.item_type,
            title=item.title,
            content_md=item.content_md,
            status=item.status,
            context_kind=item.context_kind,
            context_id=item.context_id,
            confidence=item.confidence,
            suggested_route_json=item.suggested_route_json,
            tags=json.loads(item.tags_json) if item.tags_json else [],
            pinned=bool(item.pinned),
            due_at=item.due_at.isoformat() if item.due_at else None,
            created_at=item.created_at.isoformat(),
            filed_at=item.filed_at.isoformat() if item.filed_at else None
        )
        for item in items
    ]


# ============================================================================
# INBOX ACTIONS
# ============================================================================

@router.post("/accept")
async def accept_item(
    request: AcceptItemRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Accept classification and file item to suggested context.
    Moves item from 'inbox' to 'active'.
    """

    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    if item.status != 'inbox':
        raise HTTPException(status_code=400, detail="Item is not in inbox")

    # Accept the suggested route
    item.status = 'active'
    item.filed_at = datetime.utcnow()

    db.commit()
    db.refresh(item)

    return {
        'item_id': item.id,
        'status': item.status,
        'message': 'Item filed successfully'
    }


@router.post("/change-route")
async def change_item_route(
    request: ChangeRouteRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Change item classification and file to different context.
    """

    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Update context
    item.context_kind = request.context_kind
    item.context_id = request.context_id
    item.status = 'active'
    item.filed_at = datetime.utcnow()
    item.confidence = 1.0  # User override = 100% confidence

    db.commit()
    db.refresh(item)

    return {
        'item_id': item.id,
        'status': item.status,
        'context_kind': item.context_kind,
        'message': 'Item rerouted successfully'
    }


@router.post("/snooze")
async def snooze_item(
    request: SnoozeItemRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Snooze item until specified time.
    Item will reappear in inbox when snooze_until is reached.
    """

    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    # Parse snooze time
    try:
        snooze_until = datetime.fromisoformat(request.snooze_until)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid datetime format")

    item.status = 'snoozed'
    item.snooze_until = snooze_until

    db.commit()
    db.refresh(item)

    return {
        'item_id': item.id,
        'status': item.status,
        'snooze_until': item.snooze_until.isoformat(),
        'message': f'Item snoozed until {snooze_until.strftime("%Y-%m-%d %H:%M")}'
    }


@router.post("/pin")
async def pin_item(
    request: PinItemRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Pin or unpin an item.
    Pinned items appear at top of inbox.
    """

    item = db.query(Item).filter(Item.id == request.item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    item.pinned = 1 if request.pinned else 0

    db.commit()
    db.refresh(item)

    return {
        'item_id': item.id,
        'pinned': bool(item.pinned),
        'message': 'Item pinned' if item.pinned else 'Item unpinned'
    }


# ============================================================================
# ITEM DETAIL
# ============================================================================

@router.get("/items/{item_id}")
async def get_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """Get full item details."""

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    return ItemResponse(
        id=item.id,
        item_type=item.item_type,
        title=item.title,
        content_md=item.content_md,
        status=item.status,
        context_kind=item.context_kind,
        context_id=item.context_id,
        confidence=item.confidence,
        suggested_route_json=item.suggested_route_json,
        tags=json.loads(item.tags_json) if item.tags_json else [],
        pinned=bool(item.pinned),
        due_at=item.due_at.isoformat() if item.due_at else None,
        created_at=item.created_at.isoformat(),
        filed_at=item.filed_at.isoformat() if item.filed_at else None
    )


@router.delete("/items/{item_id}")
async def delete_item(
    item_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """Delete an item permanently."""

    item = db.query(Item).filter(Item.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")

    db.delete(item)
    db.commit()

    return {'message': 'Item deleted successfully'}


# ============================================================================
# INBOX STATS
# ============================================================================

@router.get("/stats")
async def get_inbox_stats(
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Get inbox statistics for Home dashboard.

    Returns counts for:
    - Inbox items (needs review)
    - Due soon (next 24 hours)
    - Overdue
    """

    now = datetime.utcnow()
    tomorrow = datetime.utcnow().replace(hour=23, minute=59, second=59)

    inbox_count = db.query(Item).filter(Item.status == 'inbox').count()

    due_soon_count = db.query(Item).filter(
        Item.status == 'active',
        Item.due_at.isnot(None),
        Item.due_at <= tomorrow,
        Item.due_at >= now
    ).count()

    overdue_count = db.query(Item).filter(
        Item.status == 'active',
        Item.due_at.isnot(None),
        Item.due_at < now
    ).count()

    return {
        'inbox_count': inbox_count,
        'due_soon_count': due_soon_count,
        'overdue_count': overdue_count
    }
