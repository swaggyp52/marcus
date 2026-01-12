"""
Undo Service - v0.48

Lightweight undo system for recent actions.

Features:
- 10-second undo window
- Persisted in database (undo_events table)
- Supports: create item, file item, delete item, snooze, pin, mission creation
- Does NOT support: online ops (push/PR)
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import Optional, Dict
from enum import Enum
import json

from marcus_app.core.database import engine
from sqlalchemy import Column, Integer, String, JSON, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

# Undo event types
class UndoAction(str, Enum):
    CREATE_ITEM = "create_item"
    FILE_ITEM = "file_item"
    DELETE_ITEM = "delete_item"
    SNOOZE_ITEM = "snooze_item"
    PIN_ITEM = "pin_item"
    CREATE_MISSION = "create_mission"


class UndoService:
    """
    Manage undo events for user actions.
    """

    UNDO_WINDOW_SECONDS = 10  # 10-second undo window

    def __init__(self, db: Session):
        self.db = db
        self.now = datetime.utcnow()

    def record_action(
        self,
        action_type: UndoAction,
        payload: Dict,
        description: str = "",
    ) -> str:
        """
        Record an action for undo.

        Args:
            action_type: Type of action (from UndoAction enum)
            payload: Data needed to undo (must be JSON-serializable)
            description: Human-readable description

        Returns:
            undo_event_id (string)
        """
        try:
            # Create undo event
            expires_at = self.now + timedelta(seconds=self.UNDO_WINDOW_SECONDS)

            from marcus_app.core.models import UndoEvent

            event = UndoEvent(
                action_type=action_type.value,
                payload=payload,
                description=description,
                created_at=self.now,
                expires_at=expires_at,
                is_consumed=False
            )

            self.db.add(event)
            self.db.commit()

            return str(event.id)
        except Exception as e:
            print(f"Error recording undo action: {e}")
            self.db.rollback()
            return None

    def get_last_action(self) -> Optional[Dict]:
        """
        Get the most recent non-expired, non-consumed undo event.

        Returns:
        {
            "id": 123,
            "action_type": "create_item",
            "payload": {...},
            "description": "Created task: Homework",
            "created_at": "2024-01-13T10:30:00",
            "expires_at": "2024-01-13T10:30:10",
            "can_undo": True/False  # False if expired
        }
        """
        try:
            from marcus_app.core.models import UndoEvent

            event = self.db.query(UndoEvent).filter(
                UndoEvent.is_consumed == False,
                UndoEvent.expires_at > self.now
            ).order_by(UndoEvent.created_at.desc()).first()

            if not event:
                return None

            return {
                "id": event.id,
                "action_type": event.action_type,
                "payload": event.payload,
                "description": event.description,
                "created_at": event.created_at.isoformat(),
                "expires_at": event.expires_at.isoformat(),
                "can_undo": event.expires_at > self.now,
                "seconds_remaining": int((event.expires_at - self.now).total_seconds())
            }
        except Exception as e:
            print(f"Error getting last undo action: {e}")
            return None

    def undo_last_action(self) -> Dict:
        """
        Undo the most recent action.

        Flow:
        1. Get last non-expired action
        2. Check if still within undo window
        3. Execute undo logic based on action_type
        4. Mark event as consumed
        5. Return result

        Returns:
        {
            "success": True/False,
            "message": "Undid: Created task: Homework",
            "action_type": "create_item",
            "undone_id": 123
        }
        """
        try:
            from marcus_app.core.models import UndoEvent, Item, Mission

            event = self.get_last_action()
            if not event:
                return {
                    "success": False,
                    "message": "No actions to undo"
                }

            if not event["can_undo"]:
                return {
                    "success": False,
                    "message": f"Undo window expired ({event['seconds_remaining']}s ago)"
                }

            action_type = event["action_type"]
            payload = event["payload"]
            result = None

            # Execute undo based on action type
            if action_type == UndoAction.CREATE_ITEM.value:
                # Delete the created item (soft delete)
                item_id = payload.get("item_id")
                item = self.db.query(Item).filter(Item.id == item_id).first()
                if item:
                    item.is_deleted = True
                    item.deleted_at = self.now
                    self.db.commit()
                    result = {
                        "success": True,
                        "message": f"Undid: Created {payload.get('item_type')}: {payload.get('title')}",
                        "action_type": action_type,
                        "undone_id": item_id
                    }

            elif action_type == UndoAction.DELETE_ITEM.value:
                # Restore deleted item
                item_id = payload.get("item_id")
                item = self.db.query(Item).filter(Item.id == item_id).first()
                if item:
                    item.is_deleted = False
                    item.deleted_at = None
                    self.db.commit()
                    result = {
                        "success": True,
                        "message": f"Restored: {payload.get('title')}",
                        "action_type": action_type,
                        "undone_id": item_id
                    }

            elif action_type == UndoAction.SNOOZE_ITEM.value:
                # Restore original due date
                item_id = payload.get("item_id")
                original_due = payload.get("original_due_at")
                item = self.db.query(Item).filter(Item.id == item_id).first()
                if item and original_due:
                    from dateutil.parser import parse
                    item.due_at = parse(original_due)
                    self.db.commit()
                    result = {
                        "success": True,
                        "message": f"Undid snooze: {payload.get('title')}",
                        "action_type": action_type,
                        "undone_id": item_id
                    }

            elif action_type == UndoAction.PIN_ITEM.value:
                # Unpin the item (via Inbox)
                item_id = payload.get("item_id")
                from marcus_app.core.models import Inbox
                inbox = self.db.query(Inbox).filter(Inbox.item_id == item_id).first()
                if inbox:
                    inbox.pinned = not inbox.pinned
                    self.db.commit()
                    result = {
                        "success": True,
                        "message": f"Undid pin: {payload.get('title')}",
                        "action_type": action_type,
                        "undone_id": item_id
                    }

            elif action_type == UndoAction.CREATE_MISSION.value:
                # Delete the created mission
                mission_id = payload.get("mission_id")
                mission = self.db.query(Mission).filter(Mission.id == mission_id).first()
                if mission:
                    mission.is_deleted = True
                    mission.deleted_at = self.now
                    self.db.commit()
                    result = {
                        "success": True,
                        "message": f"Undid: Created mission: {payload.get('name')}",
                        "action_type": action_type,
                        "undone_id": mission_id
                    }

            if result:
                # Mark event as consumed
                from marcus_app.core.models import UndoEvent
                undo_event = self.db.query(UndoEvent).filter(
                    UndoEvent.id == event["id"]
                ).first()
                if undo_event:
                    undo_event.is_consumed = True
                    self.db.commit()

                return result

            return {
                "success": False,
                "message": f"Unknown undo action: {action_type}"
            }

        except Exception as e:
            print(f"Error undoing action: {e}")
            self.db.rollback()
            return {
                "success": False,
                "message": f"Undo failed: {str(e)}"
            }

    def get_status(self) -> Dict:
        """
        Get undo status for UI display.

        Returns:
        {
            "undo_available": True/False,
            "seconds_remaining": 10,
            "last_action": "Created task: Homework",
            "action_type": "create_item"
        }
        """
        event = self.get_last_action()
        if not event:
            return {
                "undo_available": False,
                "seconds_remaining": 0,
                "last_action": None,
                "action_type": None
            }

        return {
            "undo_available": event["can_undo"],
            "seconds_remaining": event["seconds_remaining"],
            "last_action": event["description"],
            "action_type": event["action_type"]
        }

    def cleanup_expired_events(self) -> int:
        """
        Delete expired undo events (cron job).

        Returns: Number of events deleted
        """
        try:
            from marcus_app.core.models import UndoEvent

            expired = self.db.query(UndoEvent).filter(
                UndoEvent.expires_at < self.now
            ).delete()

            self.db.commit()
            return expired
        except Exception as e:
            print(f"Error cleaning up undo events: {e}")
            self.db.rollback()
            return 0
