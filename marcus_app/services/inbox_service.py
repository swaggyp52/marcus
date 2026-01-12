"""
Service for inbox management and auto-classification.
Handles drag-drop file uploads and smart suggestions.
"""

from typing import Optional, Dict, List, Tuple
from sqlalchemy.orm import Session
from pathlib import Path
import hashlib
import re
from datetime import datetime

from ..core.models import InboxItem, Class, Assignment, Artifact
from .file_service import FileService


class InboxService:
    """
    Manages the inbox: file drops, auto-classification, and organization.
    """

    def __init__(self, inbox_path: Path):
        self.inbox_path = inbox_path
        self.inbox_path.mkdir(exist_ok=True)

    def add_to_inbox(
        self,
        file_content: bytes,
        filename: str,
        db: Session
    ) -> InboxItem:
        """
        Add a file to the inbox and attempt auto-classification.
        """
        # Calculate hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Check for duplicates
        existing = db.query(InboxItem).filter(
            InboxItem.file_hash == file_hash
        ).first()

        if existing and existing.status == "pending":
            return existing

        # Save file to inbox
        safe_filename = self._safe_filename(filename)
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        stored_filename = f"{timestamp}_{safe_filename}"
        file_path = self.inbox_path / stored_filename

        with open(file_path, 'wb') as f:
            f.write(file_content)

        # Detect file type
        file_type = self._detect_file_type(filename)

        # Create inbox item
        inbox_item = InboxItem(
            filename=filename,
            file_path=str(file_path),
            file_type=file_type,
            file_size=len(file_content),
            file_hash=file_hash,
            status="pending"
        )

        # Auto-classify
        suggestion = self._auto_classify(filename, file_type, file_content, db)

        inbox_item.suggested_class_id = suggestion.get('class_id')
        inbox_item.suggested_assignment_id = suggestion.get('assignment_id')
        inbox_item.classification_confidence = suggestion.get('confidence')
        inbox_item.classification_reasoning = suggestion.get('reasoning')

        db.add(inbox_item)
        db.commit()
        db.refresh(inbox_item)

        return inbox_item

    def _auto_classify(
        self,
        filename: str,
        file_type: str,
        file_content: bytes,
        db: Session
    ) -> Dict:
        """
        Attempt to classify the file based on filename patterns and content.
        Returns suggested class_id, assignment_id, confidence, and reasoning.
        """
        # Get all classes and assignments
        classes = db.query(Class).all()
        assignments = db.query(Assignment).all()

        if not classes:
            return {
                'class_id': None,
                'assignment_id': None,
                'confidence': 'low',
                'reasoning': 'No classes exist yet. Create a class first.'
            }

        # Strategy 1: Pattern matching in filename
        filename_lower = filename.lower()

        # Try to extract class code patterns (e.g., ECE347, CYENG350, PHYS214)
        class_code_pattern = r'\b([A-Z]{2,5}\s?\d{3,4})\b'
        matches = re.findall(class_code_pattern, filename.upper())

        for match in matches:
            # Normalize (remove spaces)
            normalized_code = match.replace(' ', '')

            # Check against existing classes
            for cls in classes:
                if normalized_code in cls.code.replace(' ', '').upper():
                    # Found a class match!
                    # Now try to find assignment
                    assignment_match = self._match_assignment(
                        filename,
                        cls.id,
                        assignments
                    )

                    return {
                        'class_id': cls.id,
                        'assignment_id': assignment_match.get('assignment_id'),
                        'confidence': 'high' if assignment_match.get('assignment_id') else 'medium',
                        'reasoning': f"Detected class code '{normalized_code}' in filename. " + assignment_match.get('reasoning', '')
                    }

        # Strategy 2: Keyword matching
        # Common assignment keywords
        assignment_keywords = {
            'lab': ['lab', 'laboratory', 'experiment'],
            'homework': ['hw', 'homework', 'problem set', 'pset'],
            'exam': ['exam', 'test', 'quiz', 'midterm', 'final'],
            'project': ['project', 'proj'],
            'lecture': ['lecture', 'notes', 'slides'],
            'syllabus': ['syllabus', 'schedule']
        }

        detected_type = None
        for keyword_type, keywords in assignment_keywords.items():
            if any(kw in filename_lower for kw in keywords):
                detected_type = keyword_type
                break

        # Strategy 3: Date patterns (e.g., 2024-01-15)
        date_pattern = r'\b(20\d{2})[_-]?(\d{2})[_-]?(\d{2})\b'
        date_matches = re.findall(date_pattern, filename)

        # If we found keywords but no class, suggest most recent class
        if detected_type and not matches:
            most_recent_class = max(classes, key=lambda c: c.created_at)

            # Try to find matching assignment by type
            matching_assignments = [
                a for a in assignments
                if a.class_id == most_recent_class.id
                and detected_type in a.title.lower()
            ]

            if matching_assignments:
                assignment = matching_assignments[0]
                return {
                    'class_id': most_recent_class.id,
                    'assignment_id': assignment.id,
                    'confidence': 'medium',
                    'reasoning': f"Detected '{detected_type}' keyword. Matched to existing {detected_type} assignment in {most_recent_class.code}."
                }
            else:
                return {
                    'class_id': most_recent_class.id,
                    'assignment_id': None,
                    'confidence': 'low',
                    'reasoning': f"Detected '{detected_type}' keyword. Suggested class: {most_recent_class.code}. Consider creating a new assignment."
                }

        # Fallback: suggest most recent class
        most_recent_class = max(classes, key=lambda c: c.created_at)
        return {
            'class_id': most_recent_class.id,
            'assignment_id': None,
            'confidence': 'low',
            'reasoning': f"No strong pattern detected. Suggesting most recent class: {most_recent_class.code}."
        }

    def _match_assignment(
        self,
        filename: str,
        class_id: int,
        all_assignments: List[Assignment]
    ) -> Dict:
        """
        Try to match filename to an existing assignment within a class.
        """
        filename_lower = filename.lower()

        # Get assignments for this class
        class_assignments = [a for a in all_assignments if a.class_id == class_id]

        if not class_assignments:
            return {
                'assignment_id': None,
                'reasoning': 'No assignments exist for this class yet.'
            }

        # Try to extract assignment number (e.g., HW1, Lab2, Assignment 3)
        number_pattern = r'\b(hw|lab|assignment|project|quiz|exam)\s?(\d+)\b'
        match = re.search(number_pattern, filename_lower)

        if match:
            assignment_type = match.group(1)
            assignment_num = match.group(2)

            # Look for matching assignment
            for assignment in class_assignments:
                assignment_title_lower = assignment.title.lower()
                if assignment_type in assignment_title_lower and assignment_num in assignment_title_lower:
                    return {
                        'assignment_id': assignment.id,
                        'reasoning': f"Matched to assignment '{assignment.title}' based on type and number."
                    }

        # Fallback: most recent assignment in class
        most_recent = max(class_assignments, key=lambda a: a.created_at)
        return {
            'assignment_id': most_recent.id,
            'reasoning': f"Suggested most recent assignment: '{most_recent.title}'."
        }

    def classify_item(
        self,
        inbox_item_id: int,
        class_id: Optional[int],
        assignment_id: Optional[int],
        create_new_assignment: bool,
        new_assignment_title: Optional[str],
        db: Session
    ) -> Artifact:
        """
        User confirms/corrects classification and moves file to proper location.
        """
        inbox_item = db.query(InboxItem).filter(InboxItem.id == inbox_item_id).first()
        if not inbox_item:
            raise ValueError("Inbox item not found")

        # If creating new assignment, do it now
        if create_new_assignment and new_assignment_title and class_id:
            new_assignment = Assignment(
                class_id=class_id,
                title=new_assignment_title,
                status="todo"
            )
            db.add(new_assignment)
            db.commit()
            db.refresh(new_assignment)
            assignment_id = new_assignment.id

        if not assignment_id:
            raise ValueError("Must provide assignment_id or create new assignment")

        # Read file content
        with open(inbox_item.file_path, 'rb') as f:
            file_content = f.read()

        # Create artifact using file service
        file_service = FileService(Path("vault"))  # Will be injected properly
        artifact = file_service.save_file(
            file_content=file_content,
            original_filename=inbox_item.filename,
            assignment_id=assignment_id,
            db=db
        )

        # Update inbox item status
        inbox_item.status = "classified"
        inbox_item.classified_at = datetime.utcnow()

        db.commit()

        return artifact

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from extension."""
        ext = Path(filename).suffix.lower()

        type_map = {
            '.pdf': 'pdf',
            '.png': 'image',
            '.jpg': 'image',
            '.jpeg': 'image',
            '.gif': 'image',
            '.bmp': 'image',
            '.docx': 'docx',
            '.doc': 'doc',
            '.txt': 'text',
            '.md': 'markdown',
            '.py': 'code',
            '.java': 'code',
            '.cpp': 'code',
            '.c': 'code',
            '.js': 'code',
            '.html': 'code',
            '.css': 'code'
        }

        return type_map.get(ext, 'unknown')

    def _safe_filename(self, filename: str) -> str:
        """Create a safe filename by removing/replacing problematic characters."""
        # Remove path components
        filename = Path(filename).name

        # Replace problematic characters
        safe = re.sub(r'[^\w\s.-]', '_', filename)
        safe = re.sub(r'\s+', '_', safe)

        return safe
