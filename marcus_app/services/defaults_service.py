"""
DefaultsService - Opinionated defaults for reduced friction

Philosophy:
- Tasks default to TODAY if no date specified
- Notes default to LAST ACTIVE CONTEXT
- Files default to INBOX → auto-file
- Missions default to LAST USED TEMPLATE
- Quick Add defaults to ACCEPT on ≥90% confidence

User can always override. Defaults just eliminate the friction.
"""

from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from marcus_app.models import Item, Mission, Context, User


class DefaultsService:
    """Applies opinionated defaults to reduce friction."""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    # ============================================================
    # TASK DEFAULTS
    # ============================================================
    
    def apply_task_defaults(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply defaults for task creation:
        - If no due_date: default to TODAY
        - If no context_id: default to LAST ACTIVE
        - If no priority: default to NORMAL
        """
        
        # Default to TODAY if no date specified
        if not task_data.get('due_date'):
            task_data['due_date'] = datetime.now().date()
        
        # Default to last active context
        if not task_data.get('context_id'):
            last_context = self._get_last_active_context()
            if last_context:
                task_data['context_id'] = last_context.id
        
        # Default to normal priority
        if not task_data.get('priority'):
            task_data['priority'] = 'normal'
        
        return task_data
    
    # ============================================================
    # NOTE DEFAULTS
    # ============================================================
    
    def apply_note_defaults(self, note_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply defaults for note creation:
        - If no context_id: default to LAST ACTIVE CONTEXT
        - If no timestamp: default to NOW
        """
        
        # Default to last active context
        if not note_data.get('context_id'):
            last_context = self._get_last_active_context()
            if last_context:
                note_data['context_id'] = last_context.id
        
        # Default to now
        if not note_data.get('created_at'):
            note_data['created_at'] = datetime.now()
        
        return note_data
    
    # ============================================================
    # FILE DEFAULTS
    # ============================================================
    
    def apply_file_defaults(self, file_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply defaults for file/link creation:
        - If no context_id: default to INBOX
        - Mark for auto-filing if confidence high
        """
        
        # Default to inbox
        if not file_data.get('context_id'):
            inbox_context = self._get_inbox_context()
            if inbox_context:
                file_data['context_id'] = inbox_context.id
        
        # Mark for auto-file if added via quick capture (≥90% confidence)
        if file_data.get('confidence_score', 0) >= 0.9:
            file_data['auto_file'] = True
            file_data['auto_file_suggested_context'] = self._suggest_context_for_auto_file(file_data)
        
        return file_data
    
    # ============================================================
    # MISSION DEFAULTS
    # ============================================================
    
    def apply_mission_defaults(self, mission_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply defaults for mission creation:
        - If no template: default to LAST USED TEMPLATE
        - If no duration: default to MEDIUM (2 weeks)
        """
        
        # Default to last used template
        if not mission_data.get('template_id'):
            last_template = self._get_last_used_template()
            if last_template:
                mission_data['template_id'] = last_template
        
        # Default to medium duration (2 weeks)
        if not mission_data.get('duration_days'):
            mission_data['duration_days'] = 14
        
        return mission_data
    
    # ============================================================
    # QUICK ADD DEFAULTS
    # ============================================================
    
    def should_auto_accept(self, item_data: Dict[str, Any]) -> bool:
        """
        Determine if item should auto-accept on ≥90% confidence.
        
        Rules:
        - Confidence ≥ 90%
        - Type is TASK or NOTE (not file)
        - Not a mission
        """
        
        confidence = item_data.get('confidence_score', 0)
        item_type = item_data.get('type', '').lower()
        
        return (
            confidence >= 0.9 and
            item_type in ['task', 'note'] and
            not item_data.get('is_mission', False)
        )
    
    # ============================================================
    # HELPERS
    # ============================================================
    
    def _get_last_active_context(self) -> Optional[Context]:
        """Get user's last active context."""
        from marcus_app.models import Item
        
        last_item = self.db.query(Item).filter(
            Item.user_id == self.user_id,
            Item.context_id.isnot(None)
        ).order_by(Item.updated_at.desc()).first()
        
        if last_item and last_item.context:
            return last_item.context
        
        return None
    
    def _get_inbox_context(self) -> Optional[Context]:
        """Get user's inbox context."""
        return self.db.query(Context).filter(
            Context.user_id == self.user_id,
            Context.code == 'INBOX'
        ).first()
    
    def _get_last_used_template(self) -> Optional[int]:
        """Get user's last used mission template ID."""
        last_mission = self.db.query(Mission).filter(
            Mission.user_id == self.user_id
        ).order_by(Mission.created_at.desc()).first()
        
        return last_mission.template_id if last_mission else None
    
    def _suggest_context_for_auto_file(self, file_data: Dict[str, Any]) -> Optional[int]:
        """
        Suggest best context for auto-filing based on:
        - File title/description keywords
        - Recent context activity
        - File type hints
        """
        
        # Extract keywords from title
        title = file_data.get('title', '').lower()
        keywords = title.split()
        
        # Find contexts matching keywords (very simple heuristic)
        matching_contexts = self.db.query(Context).filter(
            Context.user_id == self.user_id,
            Context.code.ilike(f'%{keywords[0]}%') if keywords else False
        ).all()
        
        if matching_contexts:
            return matching_contexts[0].id
        
        # Fall back to last active
        last = self._get_last_active_context()
        return last.id if last else None
    
    # ============================================================
    # DETERMINISTIC DEFAULTS (FOR TESTING)
    # ============================================================
    
    def get_all_defaults(self) -> Dict[str, Any]:
        """
        Return current defaults as a deterministic dict.
        Used for testing consistency.
        """
        
        last_context = self._get_last_active_context()
        inbox = self._get_inbox_context()
        last_template = self._get_last_used_template()
        
        return {
            'task': {
                'due_date': datetime.now().date().isoformat(),
                'context_id': last_context.id if last_context else None,
                'priority': 'normal'
            },
            'note': {
                'context_id': last_context.id if last_context else None,
                'created_at': datetime.now().isoformat()
            },
            'file': {
                'context_id': inbox.id if inbox else None,
                'auto_file': True
            },
            'mission': {
                'template_id': last_template,
                'duration_days': 14
            },
            'quick_add_auto_accept_threshold': 0.9
        }
