"""
SystemResponse - Consistent system voice across Marcus

Philosophy:
- Short. Declarative. Action-oriented.
- Non-assistant tone (no "I've gone ahead...")
- Consistent formatting for all system output
- Machine-parseable (structured responses)

Examples:
❌ "I've gone ahead and created a new task for you..."
✅ "Task created: PHYS214 Lab Report
   Due: Fri 11:59 PM"

❌ "Would you like me to file this item?"
✅ "Ready to file. Press F or continue."
"""

from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum
from datetime import datetime


class ActionType(Enum):
    """All possible action outcomes."""
    CREATE = "created"
    UPDATE = "updated"
    DELETE = "deleted"
    FILE = "filed"
    ACCEPT = "accepted"
    COMPLETE = "completed"
    SNOOZE = "snoozed"
    PIN = "pinned"
    UNPIN = "unpinned"
    UNDO = "undone"
    ERROR = "error"
    INFO = "info"
    CONFIRM = "confirm"


@dataclass
class SystemResponse:
    """Structured system response."""
    
    action: ActionType
    primary: str  # Main message (short)
    details: Optional[Dict[str, Any]] = None  # Structured details
    secondary: Optional[str] = None  # Additional info
    cta: Optional[str] = None  # Call to action
    
    def to_short_text(self) -> str:
        """Short format for toasts/quick feedback."""
        if self.action == ActionType.UNDO:
            return f"↩️ Undone: {self.primary}"
        elif self.action == ActionType.ERROR:
            return f"❌ {self.primary}"
        elif self.action == ActionType.CONFIRM:
            return f"❓ {self.primary}"
        else:
            return f"{self._icon()} {self.primary}"
    
    def to_full_text(self) -> str:
        """Full format for chat/detailed feedback."""
        lines = [f"{self._icon_full()} {self.primary}"]
        
        if self.details:
            for key, value in self.details.items():
                # Format key nicely
                display_key = key.replace('_', ' ').title()
                lines.append(f"  {display_key}: {value}")
        
        if self.secondary:
            lines.append(f"\n{self.secondary}")
        
        if self.cta:
            lines.append(f"\n→ {self.cta}")
        
        return "\n".join(lines)
    
    def to_structured(self) -> Dict[str, Any]:
        """Machine-parseable format."""
        return {
            'action': self.action.value,
            'primary': self.primary,
            'details': self.details or {},
            'secondary': self.secondary,
            'cta': self.cta
        }
    
    def _icon(self) -> str:
        """Minimal icon."""
        icons = {
            ActionType.CREATE: "✚",
            ActionType.UPDATE: "↻",
            ActionType.DELETE: "✕",
            ActionType.FILE: "📁",
            ActionType.ACCEPT: "✓",
            ActionType.COMPLETE: "✔",
            ActionType.SNOOZE: "⏰",
            ActionType.PIN: "📌",
            ActionType.UNPIN: "○",
            ActionType.UNDO: "↩️",
            ActionType.ERROR: "❌",
            ActionType.INFO: "ℹ",
            ActionType.CONFIRM: "❓"
        }
        return icons.get(self.action, "•")
    
    def _icon_full(self) -> str:
        """Full icon with emoji."""
        icons = {
            ActionType.CREATE: "✨ Created",
            ActionType.UPDATE: "↻ Updated",
            ActionType.DELETE: "🗑 Deleted",
            ActionType.FILE: "📁 Filed",
            ActionType.ACCEPT: "✓ Accepted",
            ActionType.COMPLETE: "✔ Completed",
            ActionType.SNOOZE: "⏰ Snoozed",
            ActionType.PIN: "📌 Pinned",
            ActionType.UNPIN: "○ Unpinned",
            ActionType.UNDO: "↩️ Undone",
            ActionType.ERROR: "❌ Error",
            ActionType.INFO: "ℹ Info",
            ActionType.CONFIRM: "❓ Confirm"
        }
        return icons.get(self.action, "•")


# ============================================================
# PRESET RESPONSES (Deterministic Voice)
# ============================================================

class SystemResponses:
    """Factory for consistent system responses."""
    
    @staticmethod
    def task_created(title: str, due_date: Optional[str] = None) -> SystemResponse:
        """✓ Task created with optional due date."""
        details = {'title': title}
        if due_date:
            details['due'] = due_date
        
        return SystemResponse(
            action=ActionType.CREATE,
            primary=f"Task: {title}",
            details=details
        )
    
    @staticmethod
    def note_created(title: str, context: Optional[str] = None) -> SystemResponse:
        """✓ Note created in context."""
        details = {'title': title}
        if context:
            details['in'] = context
        
        return SystemResponse(
            action=ActionType.CREATE,
            primary=f"Note: {title}",
            details=details
        )
    
    @staticmethod
    def item_filed(title: str, context: str) -> SystemResponse:
        """✓ Item filed to context."""
        return SystemResponse(
            action=ActionType.FILE,
            primary=f"Filed: {title}",
            details={'to': context}
        )
    
    @staticmethod
    def item_accepted(title: str, context: str) -> SystemResponse:
        """✓ Item accepted to context."""
        return SystemResponse(
            action=ActionType.ACCEPT,
            primary=f"Accepted: {title}",
            details={'to': context}
        )
    
    @staticmethod
    def item_snoozed(title: str, duration: str) -> SystemResponse:
        """✓ Item snoozed for duration."""
        return SystemResponse(
            action=ActionType.SNOOZE,
            primary=f"Snoozed: {title}",
            details={'for': duration}
        )
    
    @staticmethod
    def item_deleted(title: str) -> SystemResponse:
        """✓ Item deleted (with undo available)."""
        return SystemResponse(
            action=ActionType.DELETE,
            primary=f"Deleted: {title}",
            secondary="Undo available for 10 seconds"
        )
    
    @staticmethod
    def bulk_action(count: int, action: str, target: Optional[str] = None) -> SystemResponse:
        """✓ Bulk action completed."""
        action_past = f"{action}ed" if not action.endswith('ed') else action
        primary = f"{action_past.title()}: {count} item{'s' if count != 1 else ''}"
        
        details = {'count': count}
        if target:
            details['to'] = target
        
        return SystemResponse(
            action=ActionType.UPDATE,
            primary=primary,
            details=details
        )
    
    @staticmethod
    def action_undone(action: str, title: str) -> SystemResponse:
        """↩️ Action undone."""
        return SystemResponse(
            action=ActionType.UNDO,
            primary=f"Undone: {title}",
            details={'action': action}
        )
    
    @staticmethod
    def error(message: str, hint: Optional[str] = None) -> SystemResponse:
        """❌ Error occurred."""
        return SystemResponse(
            action=ActionType.ERROR,
            primary=message,
            secondary=hint
        )
    
    @staticmethod
    def confirm(question: str, hint: Optional[str] = None) -> SystemResponse:
        """❓ Confirmation needed."""
        return SystemResponse(
            action=ActionType.CONFIRM,
            primary=question,
            secondary=hint,
            cta="Y/N"
        )
    
    @staticmethod
    def info(title: str, details: Optional[Dict[str, Any]] = None) -> SystemResponse:
        """ℹ Informational message."""
        return SystemResponse(
            action=ActionType.INFO,
            primary=title,
            details=details
        )


# ============================================================
# RESPONSE FORMATTER (Apply to all agent outputs)
# ============================================================

def format_agent_response(
    action_type: ActionType,
    primary: str,
    details: Optional[Dict[str, Any]] = None,
    secondary: Optional[str] = None,
    cta: Optional[str] = None,
    format_type: str = "short"
) -> str:
    """
    Format all agent responses consistently.
    
    Args:
        action_type: Type of action
        primary: Main message
        details: Optional details dict
        secondary: Optional secondary message
        cta: Optional call to action
        format_type: 'short' or 'full'
    
    Returns:
        Formatted response string
    """
    
    response = SystemResponse(
        action=action_type,
        primary=primary,
        details=details,
        secondary=secondary,
        cta=cta
    )
    
    if format_type == "full":
        return response.to_full_text()
    else:
        return response.to_short_text()


# ============================================================
# DETERMINISTIC LANGUAGE TEST (No randomness)
# ============================================================

def get_all_response_templates() -> Dict[str, str]:
    """
    Return all response templates for testing consistency.
    Same inputs always produce same output.
    """
    
    return {
        'task_created': SystemResponses.task_created("Lab Report", "Fri 5 PM").to_short_text(),
        'note_created': SystemResponses.note_created("Meeting notes", "PHYS214").to_short_text(),
        'item_filed': SystemResponses.item_filed("Task", "PHYS214").to_short_text(),
        'item_accepted': SystemResponses.item_accepted("Task", "PHYS214").to_short_text(),
        'item_snoozed': SystemResponses.item_snoozed("Task", "60 min").to_short_text(),
        'item_deleted': SystemResponses.item_deleted("Task").to_short_text(),
        'bulk_action': SystemResponses.bulk_action(5, "accept", "PHYS214").to_short_text(),
        'action_undone': SystemResponses.action_undone("delete", "Task").to_short_text(),
        'error': SystemResponses.error("Network error", "Check connection").to_short_text(),
        'confirm': SystemResponses.confirm("Delete 5 items?", "Cannot undo after 10s").to_short_text(),
    }
