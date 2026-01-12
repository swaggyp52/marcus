"""
Item Classifier Service - v0.47a

Heuristic-based classification for universal items.
Routes items to appropriate context (class/project/personal) based on:
- Class code patterns (PHYS214, ECE347, etc.)
- Keywords for type detection
- File types
- Date/time parsing for events/tasks
- Project name matching

NO LLM required - fast, reliable, local classification.
"""

import re
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from sqlalchemy.orm import Session

from marcus_app.core.models import Class


# ============================================================================
# CLASS CODE DETECTION
# ============================================================================

CLASS_CODE_PATTERNS = [
    r'\b([A-Z]{2,4})\s*(\d{3,4})\b',  # PHYS214, ECE 347, CS101
    r'\b([A-Z]{2,4})[-_](\d{3,4})\b',  # PHYS-214, ECE_347
]


def extract_class_codes(text: str) -> List[str]:
    """Extract class codes from text (e.g., 'PHYS214', 'ECE347')."""
    codes = []
    for pattern in CLASS_CODE_PATTERNS:
        matches = re.findall(pattern, text.upper())
        for match in matches:
            # Combine department and number (e.g., ('PHYS', '214') -> 'PHYS214')
            code = ''.join(match).strip()
            codes.append(code)
    return list(set(codes))  # deduplicate


def match_class_code_to_db(codes: List[str], db: Session) -> Optional[int]:
    """Match extracted class codes to actual Class records."""
    if not codes:
        return None

    # Try exact match first
    for code in codes:
        cls = db.query(Class).filter(
            (Class.class_code == code) |
            (Class.class_code.ilike(f"%{code}%"))
        ).first()
        if cls:
            return cls.id

    return None


# ============================================================================
# KEYWORD DETECTION
# ============================================================================

TASK_KEYWORDS = [
    'todo', 'task', 'homework', 'assignment', 'due', 'submit',
    'complete', 'finish', 'do', 'need to', 'remember to'
]

EVENT_KEYWORDS = [
    'meeting', 'call', 'appointment', 'event', 'class', 'lecture',
    'exam', 'test', 'quiz', 'presentation', 'office hours'
]

DOCUMENT_EXTENSIONS = [
    '.pdf', '.docx', '.doc', '.txt', '.md', '.pptx', '.ppt',
    '.xlsx', '.xls', '.csv'
]


def detect_item_type(text: str, filename: Optional[str], file_type: Optional[str]) -> tuple[str, float]:
    """
    Detect item type based on content and metadata.

    Returns:
        (item_type, confidence)
    """
    text_lower = text.lower()

    # Document detection (highest priority if file present)
    if filename or file_type:
        return 'document', 0.95

    # Task detection
    task_score = sum(1 for kw in TASK_KEYWORDS if kw in text_lower)
    if task_score >= 2:
        return 'task', 0.85
    elif task_score == 1:
        return 'task', 0.60

    # Event detection
    event_score = sum(1 for kw in EVENT_KEYWORDS if kw in text_lower)
    # Check for time patterns
    has_time = bool(re.search(r'\b\d{1,2}:\d{2}\b|\b\d{1,2}\s*(am|pm)\b', text_lower))
    # Check for date patterns
    has_date = bool(re.search(r'\b(today|tomorrow|monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b', text_lower))

    if event_score >= 2 or (event_score >= 1 and (has_time or has_date)):
        return 'event', 0.85
    elif event_score == 1:
        return 'event', 0.60

    # Default to note
    return 'note', 0.70


# ============================================================================
# DATE/TIME PARSING
# ============================================================================

def parse_due_date(text: str) -> Optional[datetime]:
    """
    Extract due date/time from text.

    Supports:
    - "tomorrow", "today"
    - "Monday", "Tuesday", etc.
    - "at 3pm", "at 15:30"
    - "Jan 15", "January 15"
    """
    text_lower = text.lower()
    now = datetime.now()

    # Relative dates
    if 'tomorrow' in text_lower:
        base_date = now + timedelta(days=1)
    elif 'today' in text_lower:
        base_date = now
    else:
        # Day of week
        days_of_week = {
            'monday': 0, 'mon': 0,
            'tuesday': 1, 'tue': 1, 'tues': 1,
            'wednesday': 2, 'wed': 2,
            'thursday': 3, 'thu': 3, 'thur': 3, 'thurs': 3,
            'friday': 4, 'fri': 4,
            'saturday': 5, 'sat': 5,
            'sunday': 6, 'sun': 6
        }

        base_date = None
        for day_name, day_num in days_of_week.items():
            if day_name in text_lower:
                days_ahead = day_num - now.weekday()
                if days_ahead <= 0:  # Target day already passed this week
                    days_ahead += 7
                base_date = now + timedelta(days=days_ahead)
                break

        if not base_date:
            return None

    # Extract time if present
    time_match = re.search(r'(\d{1,2}):(\d{2})\s*(am|pm)?', text_lower)
    if time_match:
        hour = int(time_match.group(1))
        minute = int(time_match.group(2))
        period = time_match.group(3)

        if period == 'pm' and hour < 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        return base_date.replace(hour=hour, minute=minute, second=0, microsecond=0)

    # Check for simple hour format (e.g., "3pm", "5am")
    simple_time_match = re.search(r'(\d{1,2})\s*(am|pm)', text_lower)
    if simple_time_match:
        hour = int(simple_time_match.group(1))
        period = simple_time_match.group(2)

        if period == 'pm' and hour < 12:
            hour += 12
        elif period == 'am' and hour == 12:
            hour = 0

        return base_date.replace(hour=hour, minute=0, second=0, microsecond=0)

    # Default to end of day if no time specified
    return base_date.replace(hour=23, minute=59, second=59, microsecond=0)


# ============================================================================
# TAG EXTRACTION
# ============================================================================

def extract_tags(text: str) -> List[str]:
    """Extract hashtags from text."""
    return re.findall(r'#(\w+)', text)


# ============================================================================
# MAIN CLASSIFIER
# ============================================================================

def classify_item(
    text: str,
    filename: Optional[str] = None,
    file_type: Optional[str] = None,
    db: Optional[Session] = None
) -> Dict[str, Any]:
    """
    Classify an item based on content and metadata.

    Args:
        text: Item content (title + body)
        filename: Optional filename if document
        file_type: Optional file type/extension
        db: Optional database session for class lookup

    Returns:
        {
            'item_type': 'note|task|document|event',
            'context_kind': 'class|project|personal|none',
            'context_id': int or None,
            'confidence': 0.0-1.0,
            'reasoning': 'why this classification',
            'tags': ['tag1', 'tag2'],
            'due_at': datetime or None
        }
    """

    # Extract class codes
    class_codes = extract_class_codes(text)
    context_kind = 'none'
    context_id = None
    context_confidence = 0.0

    if class_codes and db:
        context_id = match_class_code_to_db(class_codes, db)
        if context_id:
            context_kind = 'class'
            context_confidence = 0.95

    # Detect item type
    item_type, type_confidence = detect_item_type(text, filename, file_type)

    # Parse due date
    due_at = None
    if item_type in ('task', 'event'):
        due_at = parse_due_date(text)

    # Extract tags
    tags = extract_tags(text)

    # Calculate overall confidence
    # Weight: context (40%), type (60%)
    if context_kind != 'none':
        overall_confidence = (context_confidence * 0.4) + (type_confidence * 0.6)
    else:
        overall_confidence = type_confidence * 0.7  # Penalize lack of context

    # Build reasoning
    reasoning_parts = []
    if class_codes:
        reasoning_parts.append(f"Found class code(s): {', '.join(class_codes)}")
    reasoning_parts.append(f"Detected as {item_type} (confidence: {type_confidence:.2f})")
    if due_at:
        reasoning_parts.append(f"Parsed due date: {due_at.strftime('%Y-%m-%d %H:%M')}")
    if tags:
        reasoning_parts.append(f"Extracted tags: {', '.join(tags)}")

    return {
        'item_type': item_type,
        'context_kind': context_kind,
        'context_id': context_id,
        'confidence': round(overall_confidence, 2),
        'reasoning': '; '.join(reasoning_parts),
        'tags': tags,
        'due_at': due_at
    }


# ============================================================================
# CONFIDENCE THRESHOLD
# ============================================================================

AUTO_FILE_THRESHOLD = 0.90  # Auto-file if confidence >= 0.90


def should_auto_file(confidence: float) -> bool:
    """Determine if item should be auto-filed or sent to inbox for review."""
    return confidence >= AUTO_FILE_THRESHOLD
