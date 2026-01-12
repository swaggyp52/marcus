"""
Agent Router Service - v0.47b

Intent parsing and command routing for Central Agent Chat.
Heuristic-first approach - no LLM dependency required.

Design Rule: Marcus EXECUTES actions, not merely suggests them.
"""

import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from sqlalchemy.orm import Session

from marcus_app.core.models import Class, Mission
from marcus_app.services.item_classifier import (
    extract_class_codes,
    match_class_code_to_db,
    detect_item_type,
    parse_due_date,
    extract_tags
)


# ============================================================================
# INTENT PATTERNS
# ============================================================================

INTENT_PATTERNS = {
    # Create item intents
    'create_task': [
        r'\b(add|create|make)\s+(a\s+)?task\b',
        r'\btask:\s*',
        r'\btodo:\s*',
        r'\b(need to|have to|must|should)\s+\w+',
    ],
    'create_note': [
        r'\b(add|create|make)\s+(a\s+)?note\b',
        r'\bnote:\s*',
        r'\b(learned|studied|reviewed)\b',
        r'\bremember\s+that\b',
    ],
    'create_event': [
        r'\b(schedule|add|create)\s+(a\s+)?(meeting|event|appointment)\b',
        r'\bmeeting\s+(at|on)\b',
        r'\b(exam|test|quiz)\s+(at|on)\b',
    ],

    # Schedule/deadline intents
    'create_deadline': [
        r'\b(deadline|due date)\b',
        r'\bdue\s+(on|by|at)\b',
        r'\bsubmit\s+by\b',
    ],

    # File/organize intents
    'file_content': [
        r'\bfile\s+(this|that|it)\s+into\b',
        r'\b(attach|link|add)\s+(this|that|it)\s+to\b',
        r'\bmove\s+(this|that|it)\s+to\b',
    ],

    # Mission intents
    'create_mission': [
        r'\bcreate\s+(a\s+)?mission\b',
        r'\bnew\s+mission\b',
        r'\bstart\s+(a\s+)?mission\b',
    ],
    'run_mission_step': [
        r'\brun\s+(next\s+)?(step|box)\b',
        r'\bexecute\s+(next\s+)?step\b',
        r'\bcontinue\s+mission\b',
    ],
    'mission_status': [
        r'\bwhat\'?s?\s+blocking\b',
        r'\bmission\s+status\b',
        r'\bshow\s+missions?\b',
    ],

    # Inbox intents
    'show_inbox': [
        r'\bwhat\'?s?\s+in\s+(my\s+)?inbox\b',
        r'\bshow\s+(my\s+)?inbox\b',
        r'\binbox\s+items?\b',
    ],
    'clear_inbox': [
        r'\bclear\s+(my\s+)?inbox\b',
        r'\bprocess\s+(my\s+)?inbox\b',
    ],

    # Status intents
    'whats_next': [
        r'\bwhat\'?s?\s+next\b',
        r'\bshow\s+(me\s+)?next\s+tasks?\b',
        r'\bwhat\s+should\s+i\s+do\b',
    ],
    'whats_due': [
        r'\bwhat\'?s?\s+due\b',
        r'\bshow\s+due\s+(items?|tasks?)\b',
        r'\bdeadlines?\b',
    ],
    'show_blocked': [
        r'\bshow\s+blocked\b',
        r'\bwhat\'?s?\s+blocked\b',
    ],
}


# Confidence threshold for auto-execution
CONFIDENCE_THRESHOLD = 0.75


# ============================================================================
# INTENT DETECTION
# ============================================================================

def detect_intent(text: str) -> Tuple[Optional[str], float]:
    """
    Detect primary intent from user input.

    Returns:
        (intent_name, confidence)
    """
    text_lower = text.lower()

    best_intent = None
    best_confidence = 0.0

    for intent_name, patterns in INTENT_PATTERNS.items():
        matches = sum(1 for pattern in patterns if re.search(pattern, text_lower))

        if matches > 0:
            # Confidence based on number of matching patterns
            confidence = min(0.6 + (matches * 0.2), 1.0)

            if confidence > best_confidence:
                best_intent = intent_name
                best_confidence = confidence

    return best_intent, best_confidence


# ============================================================================
# INTENT PARSERS
# ============================================================================

def parse_create_item_intent(text: str, db: Session) -> Dict[str, Any]:
    """
    Parse intent to create an item (note/task/event).

    Returns:
        {
            'item_type': 'note|task|event',
            'title': str,
            'context_kind': str,
            'context_id': int or None,
            'due_at': datetime or None,
            'tags': list
        }
    """
    # Extract class codes
    class_codes = extract_class_codes(text)
    context_kind = 'none'
    context_id = None

    if class_codes:
        context_id = match_class_code_to_db(class_codes, db)
        if context_id:
            context_kind = 'class'

    # Detect item type
    item_type, _ = detect_item_type(text, None, None)

    # Parse due date
    due_at = parse_due_date(text)

    # Extract tags
    tags = extract_tags(text)

    # Extract title (clean up command prefixes)
    title = text
    # Remove command prefixes
    for pattern in ['add task', 'create task', 'task:', 'todo:', 'add note', 'note:', 'add event', 'schedule']:
        title = re.sub(rf'\b{pattern}\b\s*', '', title, flags=re.IGNORECASE)

    title = title.strip()

    return {
        'item_type': item_type,
        'title': title[:200],  # Limit title length
        'context_kind': context_kind,
        'context_id': context_id,
        'due_at': due_at,
        'tags': tags
    }


def parse_create_mission_intent(text: str, db: Session) -> Dict[str, Any]:
    """
    Parse intent to create a mission.

    Returns:
        {
            'name': str,
            'mission_type': str,
            'class_id': int or None
        }
    """
    # Extract class codes
    class_codes = extract_class_codes(text)
    class_id = None

    if class_codes:
        class_id = match_class_code_to_db(class_codes, db)

    # Detect mission type from keywords
    mission_type = 'custom'
    if re.search(r'\b(exam|test|quiz)\s+prep\b', text, re.IGNORECASE):
        mission_type = 'exam_prep'
    elif re.search(r'\bcode\s+review\b', text, re.IGNORECASE):
        mission_type = 'code_review'
    elif re.search(r'\bresearch\b', text, re.IGNORECASE):
        mission_type = 'research'

    # Extract name (remove command prefix)
    name = text
    for pattern in ['create mission', 'new mission', 'start mission']:
        name = re.sub(rf'\b{pattern}\b\s*', '', name, flags=re.IGNORECASE)

    # If name contains "for <class>", clean it up
    name = re.sub(r'\s+for\s+[A-Z]{2,4}\s*\d{3,4}', '', name, flags=re.IGNORECASE)

    name = name.strip() or 'New Mission'

    return {
        'name': name[:200],
        'mission_type': mission_type,
        'class_id': class_id
    }


def parse_file_content_intent(text: str) -> Dict[str, Any]:
    """
    Parse intent to file content.

    Returns:
        {
            'target_type': 'class|mission|project',
            'target_name': str
        }
    """
    # Extract target from "file into X" or "add to X"
    match = re.search(r'\b(?:into|to)\s+([^,\.]+)', text, re.IGNORECASE)

    target_name = match.group(1).strip() if match else None

    # Determine target type
    target_type = 'class'  # default
    if target_name and re.search(r'\bmission\b', target_name, re.IGNORECASE):
        target_type = 'mission'
    elif target_name and re.search(r'\bproject\b', target_name, re.IGNORECASE):
        target_type = 'project'

    return {
        'target_type': target_type,
        'target_name': target_name
    }


def parse_status_query(text: str, query_type: str, db: Session) -> Dict[str, Any]:
    """
    Parse status query intent.

    Returns:
        {
            'query_type': 'next|due|blocked|inbox',
            'filters': dict
        }
    """
    filters = {}

    # Extract class filter if present
    class_codes = extract_class_codes(text)
    if class_codes:
        class_id = match_class_code_to_db(class_codes, db)
        if class_id:
            filters['class_id'] = class_id

    # Extract time filter for "due" queries
    if query_type == 'whats_due':
        if 'today' in text.lower():
            filters['time_filter'] = 'today'
        elif 'tomorrow' in text.lower():
            filters['time_filter'] = 'tomorrow'
        elif 'this week' in text.lower() or 'week' in text.lower():
            filters['time_filter'] = 'week'
        else:
            filters['time_filter'] = 'all'

    return {
        'query_type': query_type,
        'filters': filters
    }


# ============================================================================
# MAIN ROUTER
# ============================================================================

class AgentRouter:
    """
    Central router for agent commands.
    Parses intent, executes actions, returns structured responses.
    """

    def __init__(self, db: Session):
        self.db = db

    def route_command(self, text: str) -> Dict[str, Any]:
        """
        Route user command to appropriate handler.

        Returns:
            {
                'intent': str,
                'confidence': float,
                'action': dict or None,  # Parsed action parameters
                'needs_confirmation': bool,
                'clarification_needed': str or None
            }
        """
        # Detect intent
        intent, confidence = detect_intent(text)

        if not intent:
            return {
                'intent': 'unknown',
                'confidence': 0.0,
                'action': None,
                'needs_confirmation': False,
                'clarification_needed': "I don't understand that command. Try 'add task', 'show inbox', 'what's next', etc."
            }

        # Low confidence - ask for clarification
        if confidence < CONFIDENCE_THRESHOLD:
            return {
                'intent': intent,
                'confidence': confidence,
                'action': None,
                'needs_confirmation': False,
                'clarification_needed': f"Did you mean to {intent.replace('_', ' ')}? Please be more specific."
            }

        # Parse action based on intent
        action = self._parse_action(intent, text)

        # Determine if confirmation needed (for destructive/high-impact actions)
        needs_confirmation = self._needs_confirmation(intent, action)

        return {
            'intent': intent,
            'confidence': confidence,
            'action': action,
            'needs_confirmation': needs_confirmation,
            'clarification_needed': None
        }

    def _parse_action(self, intent: str, text: str) -> Optional[Dict[str, Any]]:
        """Parse action parameters based on intent."""

        if intent in ('create_task', 'create_note', 'create_event'):
            return parse_create_item_intent(text, self.db)

        elif intent == 'create_mission':
            return parse_create_mission_intent(text, self.db)

        elif intent == 'file_content':
            return parse_file_content_intent(text)

        elif intent in ('whats_next', 'whats_due', 'show_blocked'):
            return parse_status_query(text, intent, self.db)

        elif intent in ('show_inbox', 'clear_inbox', 'run_mission_step', 'mission_status'):
            # These intents don't need extra parsing
            return {}

        return None

    def _needs_confirmation(self, intent: str, action: Optional[Dict]) -> bool:
        """Determine if action requires explicit confirmation."""

        # Destructive actions always need confirmation
        if intent in ('clear_inbox', 'file_content'):
            return True

        # Mission creation needs confirmation
        if intent == 'create_mission':
            return True

        # Low-confidence items need confirmation
        if action and action.get('context_kind') == 'none':
            return True

        return False

    def format_confirmation_message(self, intent: str, action: Dict[str, Any]) -> str:
        """Format confirmation message for user."""

        if intent in ('create_task', 'create_note', 'create_event'):
            context = self._format_context(action.get('context_kind'), action.get('context_id'))
            due = f" due {action['due_at'].strftime('%A, %B %d')}" if action.get('due_at') else ""

            return (
                f"I'm about to create a {action['item_type']} titled \"{action['title']}\" "
                f"in {context}{due}. Confirm?"
            )

        elif intent == 'create_mission':
            context = f" for class #{action['class_id']}" if action.get('class_id') else ""
            return (
                f"I'm about to create a {action['mission_type']} mission "
                f"named \"{action['name']}\"{context}. Confirm?"
            )

        elif intent == 'clear_inbox':
            return "I'm about to accept all inbox items with their suggested routes. Confirm?"

        elif intent == 'file_content':
            return (
                f"I'm about to file the selected content into {action['target_name']}. Confirm?"
            )

        return "Confirm this action?"

    def _format_context(self, context_kind: str, context_id: Optional[int]) -> str:
        """Format context for display."""
        if context_kind == 'class' and context_id:
            cls = self.db.query(Class).filter(Class.id == context_id).first()
            return f"class {cls.class_code}" if cls else f"class #{context_id}"
        elif context_kind == 'personal':
            return "Personal"
        else:
            return "General"
