"""
ProgressiveDisclosureService - Hide complexity until it matters

Philosophy:
- Show minimal UI by default
- Reveal features only when relevant
- User never sees unused tools
- Marcus gets out of the way

Rules:
1. Ops panels appear only when a box is runnable
2. Inbox auto-collapses when empty
3. Life View appears only when graph density > threshold
4. Advanced actions hidden behind "More" affordances
5. Tabs hidden by default (keyboard + agent chat primary)
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from sqlalchemy.orm import Session
from marcus_app.models import Item, Mission, Box, Context


class ProgressiveDisclosureService:
    """Controls visibility and complexity based on context."""
    
    def __init__(self, db: Session, user_id: int):
        self.db = db
        self.user_id = user_id
    
    # ============================================================
    # OPS PANELS (Show only when relevant)
    # ============================================================
    
    def should_show_ops_panel(self, box_id: int) -> bool:
        """
        Show ops panel only when box is runnable.
        
        Runnable = has next step that's not blocked
        """
        
        box = self.db.query(Box).filter(Box.id == box_id).first()
        if not box:
            return False
        
        # Box is runnable if:
        # 1. Has status != 'blocked'
        # 2. Has unfinished steps
        # 3. Is in active mission
        
        return (
            box.status != 'blocked' and
            box.status != 'completed' and
            self._box_has_unfinished_steps(box)
        )
    
    def _box_has_unfinished_steps(self, box: Box) -> bool:
        """Check if box has unfinished work items."""
        unfinished = self.db.query(Item).filter(
            Item.box_id == box.id,
            Item.is_deleted == False,
            Item.status != 'completed'
        ).first()
        
        return unfinished is not None
    
    # ============================================================
    # INBOX AUTO-COLLAPSE (Hide when empty)
    # ============================================================
    
    def should_show_inbox(self) -> bool:
        """
        Show inbox only if it has items.
        Empty inbox collapses to just icon + count.
        """
        
        inbox_count = self.db.query(Item).filter(
            Item.user_id == self.user_id,
            Item.context_id.is_(None),  # Inbox items have no context
            Item.is_deleted == False
        ).count()
        
        return inbox_count > 0
    
    def get_inbox_visibility_state(self) -> Dict[str, Any]:
        """Get inbox visibility state."""
        count = self.db.query(Item).filter(
            Item.user_id == self.user_id,
            Item.context_id.is_(None),
            Item.is_deleted == False
        ).count()
        
        return {
            'visible': count > 0,
            'count': count,
            'display_mode': 'expanded' if count > 0 else 'icon_only'
        }
    
    # ============================================================
    # LIFE VIEW (Show only when dense)
    # ============================================================
    
    def should_show_life_view(self) -> bool:
        """
        Show Life View only when graph density > threshold.
        
        Threshold = user has multiple active contexts + missions
        """
        
        # Count active contexts with items
        active_contexts = self.db.query(Context).filter(
            Context.user_id == self.user_id,
            Context.is_active == True
        ).count()
        
        # Count active missions
        active_missions = self.db.query(Mission).filter(
            Mission.user_id == self.user_id,
            Mission.status != 'completed'
        ).count()
        
        # Show if > 3 contexts OR > 2 missions
        return active_contexts > 3 or active_missions > 2
    
    def get_life_view_visibility_state(self) -> Dict[str, Any]:
        """Get Life View visibility state."""
        active_contexts = self.db.query(Context).filter(
            Context.user_id == self.user_id,
            Context.is_active == True
        ).count()
        
        active_missions = self.db.query(Mission).filter(
            Mission.user_id == self.user_id,
            Mission.status != 'completed'
        ).count()
        
        return {
            'visible': active_contexts > 3 or active_missions > 2,
            'graph_density': {
                'contexts': active_contexts,
                'missions': active_missions
            },
            'display_mode': 'visible' if active_contexts > 3 else 'hidden'
        }
    
    # ============================================================
    # ADVANCED ACTIONS (Hide behind "More")
    # ============================================================
    
    def get_item_actions(self, item_id: int) -> Dict[str, List[str]]:
        """
        Get visible and hidden actions for item.
        
        Visible (primary):
        - Accept/Complete
        - Snooze
        - Pin
        
        Hidden (behind "More"):
        - Duplicate
        - Move to different context
        - Change priority
        - Add dependencies
        """
        
        item = self.db.query(Item).filter(Item.id == item_id).first()
        if not item:
            return {'primary': [], 'more': []}
        
        primary_actions = ['accept', 'complete', 'snooze', 'pin']
        
        more_actions = ['duplicate', 'move', 'priority']
        
        # Show "add_dependency" only if missions exist
        missions = self.db.query(Mission).filter(
            Mission.user_id == self.user_id,
            Mission.status != 'completed'
        ).count()
        
        if missions > 0:
            more_actions.append('add_dependency')
        
        return {
            'primary': primary_actions,
            'more': more_actions
        }
    
    # ============================================================
    # TAB VISIBILITY (Hidden by default)
    # ============================================================
    
    def get_tab_visibility(self) -> Dict[str, bool]:
        """
        Get which tabs should be visible.
        
        Default:
        - Agent (always)
        - Inbox (if items)
        - Missions (if active)
        
        Hidden by default (keyboard to access):
        - Life View (unless dense)
        - Audit Log (command-only)
        """
        
        inbox_visible = self.should_show_inbox()
        missions_visible = self.db.query(Mission).filter(
            Mission.user_id == self.user_id,
            Mission.status != 'completed'
        ).count() > 0
        life_view_visible = self.should_show_life_view()
        
        return {
            'agent': True,  # Always visible
            'inbox': inbox_visible,
            'missions': missions_visible,
            'life_view': life_view_visible,
            'audit_log': False,  # Command-only
            'dev_mode': False  # Dev-only
        }
    
    # ============================================================
    # MARCUS MODE STATE (Agent-first defaults)
    # ============================================================
    
    def get_marcus_mode_state(self) -> Dict[str, Any]:
        """
        Get complete Marcus Mode state:
        - What's visible
        - Focus/defaults
        - Active component
        """
        
        return {
            'primary_component': 'agent_chat',  # Always focused
            'agent_chat': {
                'focused': True,
                'visible': True,
                'what_next_visible': True
            },
            'inbox': {
                'visible': self.should_show_inbox(),
                'collapsed': not self.should_show_inbox(),
                'auto_collapse': True
            },
            'missions': {
                'visible': self._has_active_missions(),
                'collapsed': False
            },
            'tabs': self.get_tab_visibility(),
            'advanced_actions': 'hidden',  # Behind "More"
            'keyboard_nav_hint': 'visible'  # Remind about hotkeys
        }
    
    def _has_active_missions(self) -> bool:
        """Check if user has active missions."""
        return self.db.query(Mission).filter(
            Mission.user_id == self.user_id,
            Mission.status != 'completed'
        ).count() > 0
    
    # ============================================================
    # DETERMINISTIC STATE (For testing)
    # ============================================================
    
    def get_all_disclosure_rules(self) -> Dict[str, Any]:
        """
        Return all disclosure rules as deterministic dict.
        Same inputs always produce same output.
        """
        
        return {
            'ops_panels': 'show_only_when_runnable',
            'inbox': 'auto_collapse_when_empty',
            'life_view': 'show_when_density_high',
            'advanced_actions': 'hide_behind_more',
            'tabs': {
                'agent': 'always',
                'inbox': 'if_has_items',
                'missions': 'if_active',
                'life_view': 'if_dense',
                'audit': 'keyboard_only',
                'dev': 'hidden'
            },
            'marcus_mode': 'agent_first_primary',
            'keyboard_nav': 'always_available'
        }
