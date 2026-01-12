"""
Agent Routes - v0.47b

API endpoints for Central Agent Chat.
Executes real actions against existing services.

Design Rule: Marcus EXECUTES, not suggests.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime
import json

from marcus_app.core.database import get_db
from marcus_app.core.models import Item, Mission, Class
from marcus_app.services.agent_router import AgentRouter


router = APIRouter(prefix="/api/agent", tags=["agent"])


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

class CommandRequest(BaseModel):
    text: str
    context: Optional[dict] = None  # Optional context (e.g., selected item, current view)


class ConfirmActionRequest(BaseModel):
    action_id: str
    confirmed: bool


class CommandResponse(BaseModel):
    intent: str
    confidence: float
    message: str
    action_card: Optional[dict] = None
    needs_confirmation: bool = False
    confirmation_id: Optional[str] = None


# ============================================================================
# IN-MEMORY CONFIRMATION STORE
# ============================================================================
# For simplicity, store pending confirmations in memory
# In production, use Redis or database with expiry
pending_confirmations = {}
confirmation_counter = 0


# ============================================================================
# COMMAND ENDPOINT
# ============================================================================

@router.post("/command", response_model=CommandResponse)
async def process_command(
    request: CommandRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Process user command through agent router.

    Flow:
    1. Parse intent
    2. If needs confirmation → return confirmation prompt
    3. Otherwise → execute and return result
    """
    global confirmation_counter

    router = AgentRouter(db)
    route_result = router.route_command(request.text)

    # Unknown intent or clarification needed
    if route_result['clarification_needed']:
        return CommandResponse(
            intent=route_result['intent'],
            confidence=route_result['confidence'],
            message=route_result['clarification_needed'],
            needs_confirmation=False
        )

    # Needs confirmation - store action and return prompt
    if route_result['needs_confirmation']:
        confirmation_counter += 1
        confirmation_id = f"confirm_{confirmation_counter}"

        pending_confirmations[confirmation_id] = {
            'intent': route_result['intent'],
            'action': route_result['action'],
            'timestamp': datetime.utcnow()
        }

        confirmation_msg = router.format_confirmation_message(
            route_result['intent'],
            route_result['action']
        )

        return CommandResponse(
            intent=route_result['intent'],
            confidence=route_result['confidence'],
            message=confirmation_msg,
            needs_confirmation=True,
            confirmation_id=confirmation_id
        )

    # Execute action immediately
    result = await execute_action(
        route_result['intent'],
        route_result['action'],
        db
    )

    return result


@router.post("/confirm", response_model=CommandResponse)
async def confirm_action(
    request: ConfirmActionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Confirm and execute a pending action.
    """
    if request.action_id not in pending_confirmations:
        raise HTTPException(status_code=404, detail="Confirmation not found or expired")

    pending = pending_confirmations.pop(request.action_id)

    if not request.confirmed:
        return CommandResponse(
            intent=pending['intent'],
            confidence=1.0,
            message="Action cancelled.",
            needs_confirmation=False
        )

    # Execute confirmed action
    result = await execute_action(
        pending['intent'],
        pending['action'],
        db
    )

    return result


# ============================================================================
# ACTION EXECUTORS
# ============================================================================

async def execute_action(intent: str, action: dict, db: Session) -> CommandResponse:
    """
    Execute action based on intent.
    Returns CommandResponse with result message and action card.
    """

    if intent in ('create_task', 'create_note', 'create_event'):
        return await execute_create_item(action, db)

    elif intent == 'create_mission':
        return await execute_create_mission(action, db)

    elif intent == 'show_inbox':
        return await execute_show_inbox(db)

    elif intent == 'clear_inbox':
        return await execute_clear_inbox(db)

    elif intent == 'whats_next':
        return await execute_whats_next(db)

    elif intent == 'whats_due':
        return await execute_whats_due(action, db)

    elif intent == 'show_blocked':
        return await execute_show_blocked(db)

    elif intent == 'mission_status':
        return await execute_mission_status(db)

    else:
        return CommandResponse(
            intent=intent,
            confidence=0.0,
            message=f"Intent '{intent}' recognized but not yet implemented.",
            needs_confirmation=False
        )


async def execute_create_item(action: dict, db: Session) -> CommandResponse:
    """Create an item (task/note/event)."""

    item = Item(
        item_type=action['item_type'],
        title=action['title'],
        status='active',  # Skip inbox, go straight to active
        context_kind=action['context_kind'],
        context_id=action['context_id'],
        confidence=1.0,  # User command = 100% confidence
        tags_json=json.dumps(action['tags']),
        due_at=action['due_at'],
        filed_at=datetime.utcnow(),
        created_at=datetime.utcnow()
    )

    db.add(item)
    db.commit()
    db.refresh(item)

    # Format context display
    context_display = format_context_display(action['context_kind'], action['context_id'], db)
    due_display = f" due {action['due_at'].strftime('%A, %B %d')}" if action['due_at'] else ""

    message = f"Created {action['item_type']} \"{action['title']}\" in {context_display}{due_display}."

    action_card = {
        'type': 'item_created',
        'item_id': item.id,
        'item_type': action['item_type'],
        'title': action['title'],
        'context': context_display,
        'due_at': action['due_at'].isoformat() if action['due_at'] else None,
        'actions': [
            {'label': 'View', 'type': 'navigate', 'target': f'/items/{item.id}'},
            {'label': 'Edit', 'type': 'edit', 'target': item.id},
        ]
    }

    return CommandResponse(
        intent='create_item',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_create_mission(action: dict, db: Session) -> CommandResponse:
    """Create a mission."""

    mission = Mission(
        name=action['name'],
        mission_type=action['mission_type'],
        class_id=action.get('class_id'),
        state='draft',
        created_at=datetime.utcnow()
    )

    db.add(mission)
    db.commit()
    db.refresh(mission)

    class_display = ""
    if action.get('class_id'):
        cls = db.query(Class).filter(Class.id == action['class_id']).first()
        if cls:
            class_display = f" for {cls.class_code}"

    message = f"Created mission \"{action['name']}\"{class_display}. State: draft."

    action_card = {
        'type': 'mission_created',
        'mission_id': mission.id,
        'name': action['name'],
        'mission_type': action['mission_type'],
        'state': 'draft',
        'actions': [
            {'label': 'Open Mission Control', 'type': 'navigate', 'target': '/missions'},
            {'label': 'Run First Step', 'type': 'command', 'command': 'run next step'},
        ]
    }

    return CommandResponse(
        intent='create_mission',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_show_inbox(db: Session) -> CommandResponse:
    """Show inbox items."""

    items = db.query(Item).filter(Item.status == 'inbox').order_by(Item.created_at.desc()).limit(10).all()

    if not items:
        return CommandResponse(
            intent='show_inbox',
            confidence=1.0,
            message="Inbox is empty. 📭",
            needs_confirmation=False
        )

    item_list = []
    for item in items:
        context = format_context_display(item.context_kind, item.context_id, db)
        item_list.append({
            'id': item.id,
            'title': item.title,
            'type': item.item_type,
            'context': context,
            'confidence': item.confidence
        })

    message = f"You have {len(items)} item{'s' if len(items) != 1 else ''} in your inbox."

    action_card = {
        'type': 'inbox_list',
        'count': len(items),
        'items': item_list,
        'actions': [
            {'label': 'Open Inbox', 'type': 'navigate', 'target': '/inbox'},
            {'label': 'Clear Inbox', 'type': 'command', 'command': 'clear inbox'},
        ]
    }

    return CommandResponse(
        intent='show_inbox',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_clear_inbox(db: Session) -> CommandResponse:
    """Accept all inbox items."""

    items = db.query(Item).filter(Item.status == 'inbox').all()

    if not items:
        return CommandResponse(
            intent='clear_inbox',
            confidence=1.0,
            message="Inbox is already empty.",
            needs_confirmation=False
        )

    # Accept all items (file to suggested context)
    for item in items:
        item.status = 'active'
        item.filed_at = datetime.utcnow()

    db.commit()

    message = f"Accepted and filed {len(items)} item{'s' if len(items) != 1 else ''} from inbox."

    return CommandResponse(
        intent='clear_inbox',
        confidence=1.0,
        message=message,
        needs_confirmation=False
    )


async def execute_whats_next(db: Session) -> CommandResponse:
    """Show next tasks/items."""

    # Get active items, prioritize by due date and context
    items = db.query(Item).filter(
        Item.status == 'active'
    ).order_by(
        Item.due_at.asc().nullslast(),
        Item.created_at.desc()
    ).limit(5).all()

    if not items:
        return CommandResponse(
            intent='whats_next',
            confidence=1.0,
            message="No active items. You're all caught up! 🎉",
            needs_confirmation=False
        )

    item_list = []
    for item in items:
        context = format_context_display(item.context_kind, item.context_id, db)
        due_display = item.due_at.strftime('%a, %b %d') if item.due_at else 'No deadline'

        item_list.append({
            'id': item.id,
            'title': item.title,
            'type': item.item_type,
            'context': context,
            'due': due_display
        })

    message = f"Here are your next {len(items)} items:"

    action_card = {
        'type': 'next_items',
        'items': item_list,
        'actions': [
            {'label': 'View All', 'type': 'navigate', 'target': '/items'},
        ]
    }

    return CommandResponse(
        intent='whats_next',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_whats_due(action: dict, db: Session) -> CommandResponse:
    """Show items due soon."""

    time_filter = action['filters'].get('time_filter', 'all')

    # Calculate date range
    now = datetime.utcnow()
    if time_filter == 'today':
        end_date = now.replace(hour=23, minute=59, second=59)
    elif time_filter == 'tomorrow':
        tomorrow = now + timedelta(days=1)
        end_date = tomorrow.replace(hour=23, minute=59, second=59)
    elif time_filter == 'week':
        end_date = now + timedelta(days=7)
    else:
        end_date = None

    # Query items
    query = db.query(Item).filter(
        Item.status == 'active',
        Item.due_at.isnot(None)
    )

    if end_date:
        query = query.filter(Item.due_at <= end_date)

    items = query.order_by(Item.due_at.asc()).limit(10).all()

    if not items:
        return CommandResponse(
            intent='whats_due',
            confidence=1.0,
            message=f"No items due {time_filter}.",
            needs_confirmation=False
        )

    item_list = []
    for item in items:
        context = format_context_display(item.context_kind, item.context_id, db)
        due_display = item.due_at.strftime('%A, %B %d at %I:%M %p')

        item_list.append({
            'id': item.id,
            'title': item.title,
            'type': item.item_type,
            'context': context,
            'due': due_display
        })

    message = f"Items due {time_filter}:"

    action_card = {
        'type': 'due_items',
        'filter': time_filter,
        'items': item_list
    }

    return CommandResponse(
        intent='whats_due',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_show_blocked(db: Session) -> CommandResponse:
    """Show blocked missions."""

    missions = db.query(Mission).filter(Mission.state == 'blocked').all()

    if not missions:
        return CommandResponse(
            intent='show_blocked',
            confidence=1.0,
            message="No missions are currently blocked.",
            needs_confirmation=False
        )

    mission_list = []
    for mission in missions:
        class_display = ""
        if mission.class_id:
            cls = db.query(Class).filter(Class.id == mission.class_id).first()
            if cls:
                class_display = f" ({cls.class_code})"

        mission_list.append({
            'id': mission.id,
            'name': mission.name + class_display,
            'type': mission.mission_type
        })

    message = f"{len(missions)} blocked mission{'s' if len(missions) != 1 else ''}:"

    action_card = {
        'type': 'blocked_missions',
        'missions': mission_list,
        'actions': [
            {'label': 'Open Mission Control', 'type': 'navigate', 'target': '/missions'},
        ]
    }

    return CommandResponse(
        intent='show_blocked',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


async def execute_mission_status(db: Session) -> CommandResponse:
    """Show overall mission status."""

    draft_count = db.query(Mission).filter(Mission.state == 'draft').count()
    active_count = db.query(Mission).filter(Mission.state == 'active').count()
    blocked_count = db.query(Mission).filter(Mission.state == 'blocked').count()
    done_count = db.query(Mission).filter(Mission.state == 'done').count()

    total = draft_count + active_count + blocked_count + done_count

    if total == 0:
        return CommandResponse(
            intent='mission_status',
            confidence=1.0,
            message="No missions yet. Create one with 'create mission'.",
            needs_confirmation=False
        )

    message = f"Mission Status: {active_count} active, {blocked_count} blocked, {done_count} done, {draft_count} draft."

    action_card = {
        'type': 'mission_summary',
        'stats': {
            'active': active_count,
            'blocked': blocked_count,
            'done': done_count,
            'draft': draft_count,
            'total': total
        },
        'actions': [
            {'label': 'Open Mission Control', 'type': 'navigate', 'target': '/missions'},
        ]
    }

    return CommandResponse(
        intent='mission_status',
        confidence=1.0,
        message=message,
        action_card=action_card,
        needs_confirmation=False
    )


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================

def format_context_display(context_kind: str, context_id: Optional[int], db: Session) -> str:
    """Format context for display."""
    if context_kind == 'class' and context_id:
        cls = db.query(Class).filter(Class.id == context_id).first()
        return cls.class_code if cls else f"Class #{context_id}"
    elif context_kind == 'personal':
        return "Personal"
    else:
        return "General"
