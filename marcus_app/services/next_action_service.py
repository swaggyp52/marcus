"""
Next Action Service - v0.48

Deterministic ranking of actionable items.

Ranking algorithm:
1. Overdue deadlines (highest priority)
2. Due in next 48 hours
3. Pinned inbox items
4. Blocked missions with runnable boxes
5. Active tasks not started

Returns top 3 actionable items + 1 recommended action.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from marcus_app.core.models import Item, Mission, MissionBox, Inbox


class NextActionService:
    """
    Deterministic service for "What's next?" queries.
    """

    def __init__(self, db: Session):
        self.db = db
        self.now = datetime.utcnow()

    def get_next_actions(self, limit: int = 3) -> Dict:
        """
        Get top N actionable items with deterministic ranking.

        Returns:
        {
            "items": [
                {
                    "id": 123,
                    "type": "task",
                    "title": "Finish lab report",
                    "context": "PHYS214",
                    "due": "2024-01-15 17:00",
                    "priority": 95,
                    "reason": "overdue"
                },
                ...
            ],
            "recommended_action": {
                "title": "Finish lab report",
                "actions": [
                    {"label": "Open Item", "type": "navigate", "target": "/items/123"},
                    {"label": "Mark Done", "type": "command", "command": "mark done"}
                ]
            },
            "summary": "1 overdue, 2 due soon"
        }
        """

        candidates = []

        # 1. Collect overdue items (highest priority: 95-100)
        overdue = self._get_overdue_items()
        for item in overdue:
            candidates.append({
                "item": item,
                "priority": 100,
                "reason": "overdue",
                "rank_order": 1
            })

        # 2. Collect items due in next 48h (priority: 80-94)
        due_soon = self._get_due_soon_items()
        for item in due_soon:
            candidates.append({
                "item": item,
                "priority": 85,
                "reason": "due_soon",
                "rank_order": 2
            })

        # 3. Collect pinned inbox items (priority: 70-79)
        pinned = self._get_pinned_inbox_items()
        for item in pinned:
            candidates.append({
                "item": item,
                "priority": 75,
                "reason": "pinned_inbox",
                "rank_order": 3
            })

        # 4. Blocked missions with runnable boxes (priority: 60-69)
        blocked = self._get_blocked_missions()
        for mission in blocked:
            candidates.append({
                "item": mission,
                "priority": 65,
                "reason": "blocked_mission",
                "rank_order": 4
            })

        # 5. Active tasks not started (priority: 50-59)
        not_started = self._get_not_started_tasks()
        for item in not_started:
            candidates.append({
                "item": item,
                "priority": 55,
                "reason": "not_started",
                "rank_order": 5
            })

        # Sort by priority (descending) and then by rank_order
        candidates.sort(key=lambda x: (-x["priority"], x["rank_order"]))

        # Take top N items
        top_items = candidates[:limit]

        # Format results
        formatted_items = [
            self._format_item_for_response(c["item"], c["reason"])
            for c in top_items
        ]

        # Determine recommended action
        recommended_action = None
        if formatted_items:
            recommended_action = self._get_recommended_action(formatted_items[0])

        # Generate summary
        summary = self._generate_summary(top_items)

        return {
            "items": formatted_items,
            "recommended_action": recommended_action,
            "summary": summary,
            "timestamp": self.now.isoformat()
        }

    def _get_overdue_items(self) -> List[Item]:
        """Get items with past due dates."""
        try:
            return self.db.query(Item).filter(
                Item.due_at < self.now,
                Item.due_at.isnot(None),
                Item.done_at.is_(None)
            ).order_by(Item.due_at.asc()).limit(10).all()
        except Exception as e:
            print(f"Error fetching overdue items: {e}")
            return []

    def _get_due_soon_items(self) -> List[Item]:
        """Get items due in next 48 hours."""
        try:
            threshold = self.now + timedelta(hours=48)
            return self.db.query(Item).filter(
                Item.due_at >= self.now,
                Item.due_at <= threshold,
                Item.due_at.isnot(None),
                Item.done_at.is_(None)
            ).order_by(Item.due_at.asc()).limit(10).all()
        except Exception as e:
            print(f"Error fetching due-soon items: {e}")
            return []

    def _get_pinned_inbox_items(self) -> List[Item]:
        """Get pinned inbox items."""
        try:
            return self.db.query(Item).join(
                Inbox, Item.id == Inbox.item_id
            ).filter(
                Inbox.pinned == True,
                Item.done_at.is_(None)
            ).order_by(Inbox.created_at.desc()).limit(10).all()
        except Exception as e:
            print(f"Error fetching pinned inbox items: {e}")
            return []

    def _get_blocked_missions(self) -> List[Mission]:
        """Get blocked missions with runnable boxes."""
        try:
            blocked_missions = self.db.query(Mission).filter(
                Mission.state == "blocked"
            ).limit(10).all()

            result = []
            for mission in blocked_missions:
                # Check if any boxes are runnable
                runnable_boxes = self.db.query(MissionBox).filter(
                    MissionBox.mission_id == mission.id,
                    MissionBox.status != "done"
                ).limit(1).all()

                if runnable_boxes:
                    result.append(mission)

            return result
        except Exception as e:
            print(f"Error fetching blocked missions: {e}")
            return []

    def _get_not_started_tasks(self) -> List[Item]:
        """Get active tasks not started."""
        try:
            return self.db.query(Item).filter(
                Item.item_type == "task",
                Item.done_at.is_(None),
                Item.context.isnot(None)
            ).order_by(Item.created_at.desc()).limit(10).all()
        except Exception as e:
            print(f"Error fetching not-started tasks: {e}")
            return []

    def _format_item_for_response(self, item, reason: str) -> Dict:
        """Format item for API response."""
        if isinstance(item, Mission):
            return {
                "id": item.id,
                "type": "mission",
                "title": item.name,
                "context": item.mission_type,
                "due": item.deadline.isoformat() if item.deadline else None,
                "reason": reason,
                "status": item.state
            }
        else:
            # Item object
            return {
                "id": item.id,
                "type": item.item_type,
                "title": item.title,
                "context": item.context or "General",
                "due": item.due_at.isoformat() if item.due_at else None,
                "reason": reason,
                "status": "done" if item.done_at else "active"
            }

    def _get_recommended_action(self, top_item: Dict) -> Dict:
        """Get recommended next action for top item."""
        return {
            "title": top_item["title"],
            "description": f"Start with: {top_item['title']}",
            "actions": [
                {
                    "label": "Open Item",
                    "type": "navigate",
                    "target": f"/{top_item['type']}s/{top_item['id']}"
                },
                {
                    "label": "Mark Done",
                    "type": "command",
                    "command": f"mark {top_item['id']} done"
                }
            ]
        }

    def _generate_summary(self, candidates: List[Dict]) -> str:
        """Generate human-readable summary of priorities."""
        counts = {}
        for c in candidates:
            reason = c["reason"]
            counts[reason] = counts.get(reason, 0) + 1

        parts = []
        if counts.get("overdue"):
            parts.append(f"{counts['overdue']} overdue")
        if counts.get("due_soon"):
            parts.append(f"{counts['due_soon']} due soon")
        if counts.get("pinned_inbox"):
            parts.append(f"{counts['pinned_inbox']} pinned")
        if counts.get("blocked_mission"):
            parts.append(f"{counts['blocked_mission']} blocked")
        if counts.get("not_started"):
            parts.append(f"{counts['not_started']} not started")

        return ", ".join(parts) if parts else "No actionable items"
