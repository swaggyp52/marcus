"""
Service for extracting deadlines from syllabi and assignments.
Includes .ics calendar export functionality.
"""

from typing import List, Optional
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re
from pathlib import Path

from ..core.models import Deadline, Artifact, ExtractedText, Assignment, Class


class DeadlineService:
    """
    Handles deadline extraction from documents and calendar export.
    """

    def extract_deadlines_from_artifact(
        self,
        artifact: Artifact,
        db: Session
    ) -> List[Deadline]:
        """
        Extract deadlines from an artifact (typically syllabus or assignment description).
        """
        # Get extracted text
        extracted_texts = db.query(ExtractedText).filter(
            ExtractedText.artifact_id == artifact.id
        ).all()

        if not extracted_texts:
            return []

        all_deadlines = []

        for extracted in extracted_texts:
            deadlines = self._parse_deadlines_from_text(
                extracted.content,
                artifact,
                db
            )
            all_deadlines.extend(deadlines)

        # Save to database
        for deadline_data in all_deadlines:
            deadline = Deadline(**deadline_data)
            db.add(deadline)

        db.commit()

        return [db.query(Deadline).filter(
            Deadline.source_artifact_id == artifact.id
        ).all()]

    def _parse_deadlines_from_text(
        self,
        text: str,
        artifact: Artifact,
        db: Session
    ) -> List[dict]:
        """
        Parse deadline mentions from text.
        Looks for common date patterns and deadline keywords.
        """
        deadlines = []

        # Common deadline patterns
        # Pattern 1: "Due: January 15, 2024" or "Due Date: 1/15/2024"
        # Pattern 2: "Assignment 1 - Due 2024-01-15"
        # Pattern 3: "Exam on March 10"

        # Date patterns
        date_patterns = [
            # Month Day, Year
            r'(?P<month>January|February|March|April|May|June|July|August|September|October|November|December)\s+(?P<day>\d{1,2})(?:st|nd|rd|th)?,?\s+(?P<year>\d{4})',
            # MM/DD/YYYY or M/D/YYYY
            r'(?P<month>\d{1,2})/(?P<day>\d{1,2})/(?P<year>\d{4})',
            # YYYY-MM-DD
            r'(?P<year>\d{4})-(?P<month>\d{1,2})-(?P<day>\d{1,2})',
        ]

        # Deadline keywords
        deadline_keywords = [
            r'due\s+(?:date)?:?\s*',
            r'deadline:?\s*',
            r'submit(?:ted)?\s+by:?\s*',
            r'on\s+',
        ]

        # Assignment type keywords
        type_keywords = {
            'assignment': r'\b(?:assignment|hw|homework|problem\s+set|pset)\s*\d*\b',
            'exam': r'\b(?:exam|test|quiz|midterm|final)\s*\d*\b',
            'project': r'\b(?:project|proj)\s*\d*\b',
            'reading': r'\b(?:reading|chapter)\s*\d*\b',
        }

        lines = text.split('\n')

        for i, line in enumerate(lines):
            line_lower = line.lower()

            # Check if line contains deadline keywords
            has_deadline_keyword = any(
                re.search(kw, line_lower) for kw in deadline_keywords
            )

            if not has_deadline_keyword:
                # Also check for direct date mentions near assignment keywords
                has_assignment_keyword = any(
                    re.search(pattern, line_lower)
                    for pattern in type_keywords.values()
                )
                if not has_assignment_keyword:
                    continue

            # Try to extract date
            parsed_date = None
            date_text = None

            for pattern in date_patterns:
                match = re.search(pattern, line, re.IGNORECASE)
                if match:
                    try:
                        date_text = match.group(0)
                        parsed_date = self._parse_date_match(match)
                        break
                    except ValueError:
                        continue

            if not parsed_date:
                continue

            # Determine deadline type
            deadline_type = 'assignment'
            for type_name, pattern in type_keywords.items():
                if re.search(pattern, line_lower):
                    deadline_type = type_name
                    break

            # Extract title (try to get context before/after date)
            title = self._extract_deadline_title(line, date_text)

            # Determine confidence
            confidence = 'high' if has_deadline_keyword else 'medium'

            # Get class and assignment context
            assignment = db.query(Assignment).filter(
                Assignment.id == artifact.assignment_id
            ).first()

            class_id = assignment.class_id if assignment else None
            assignment_id = assignment.id if assignment else None

            deadlines.append({
                'title': title,
                'due_date': parsed_date,
                'deadline_type': deadline_type,
                'class_id': class_id,
                'assignment_id': assignment_id,
                'source_artifact_id': artifact.id,
                'extraction_confidence': confidence,
                'extracted_text': line.strip()
            })

        return deadlines

    def _parse_date_match(self, match: re.Match) -> datetime:
        """Convert regex match to datetime object."""
        groups = match.groupdict()

        month = groups.get('month')
        day = int(groups.get('day'))
        year = int(groups.get('year'))

        # Convert month name to number
        if month and not month.isdigit():
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4,
                'may': 5, 'june': 6, 'july': 7, 'august': 8,
                'september': 9, 'october': 10, 'november': 11, 'december': 12
            }
            month = month_map.get(month.lower(), 1)
        else:
            month = int(month)

        return datetime(year, month, day)

    def _extract_deadline_title(self, line: str, date_text: str) -> str:
        """
        Extract a meaningful title from the deadline line.
        Remove the date portion and clean up.
        """
        # Remove date text
        title = line.replace(date_text, '').strip()

        # Remove common deadline keywords
        title = re.sub(r'\b(due|deadline|submit(?:ted)?\s+by|on)\s*:?\s*', '', title, flags=re.IGNORECASE)

        # Clean up extra whitespace
        title = re.sub(r'\s+', ' ', title).strip()

        # Limit length
        if len(title) > 100:
            title = title[:100] + '...'

        # Fallback if empty
        if not title:
            title = "Deadline"

        return title

    def export_to_ics(
        self,
        class_id: Optional[int],
        include_assignments: bool,
        include_deadlines: bool,
        output_path: Path,
        db: Session
    ) -> Path:
        """
        Export deadlines and assignments to .ics calendar file.
        """
        events = []

        # Collect assignments
        if include_assignments:
            query = db.query(Assignment)
            if class_id:
                query = query.filter(Assignment.class_id == class_id)

            assignments = query.filter(Assignment.due_date.isnot(None)).all()

            for assignment in assignments:
                class_obj = db.query(Class).filter(Class.id == assignment.class_id).first()
                events.append({
                    'summary': f"{class_obj.code}: {assignment.title}",
                    'dtstart': assignment.due_date,
                    'dtend': assignment.due_date + timedelta(hours=1),
                    'description': assignment.description or '',
                    'categories': ['Assignment']
                })

        # Collect extracted deadlines
        if include_deadlines:
            query = db.query(Deadline)
            if class_id:
                query = query.filter(Deadline.class_id == class_id)

            deadlines = query.all()

            for deadline in deadlines:
                class_obj = None
                if deadline.class_id:
                    class_obj = db.query(Class).filter(Class.id == deadline.class_id).first()

                summary = deadline.title
                if class_obj:
                    summary = f"{class_obj.code}: {summary}"

                events.append({
                    'summary': summary,
                    'dtstart': deadline.due_date,
                    'dtend': deadline.due_date + timedelta(hours=1),
                    'description': deadline.extracted_text or '',
                    'categories': [deadline.deadline_type.capitalize()]
                })

        # Generate .ics file
        ics_content = self._generate_ics_content(events)

        # Write to file
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(ics_content)

        return output_path

    def _generate_ics_content(self, events: List[dict]) -> str:
        """
        Generate RFC 5545 compliant .ics file content.
        """
        lines = [
            'BEGIN:VCALENDAR',
            'VERSION:2.0',
            'PRODID:-//Marcus Academic OS//EN',
            'CALSCALE:GREGORIAN',
            'METHOD:PUBLISH',
            'X-WR-CALNAME:Marcus - Academic Calendar',
            'X-WR-TIMEZONE:UTC',
        ]

        for event in events:
            uid = f"{hash(event['summary'] + str(event['dtstart']))}@marcus"
            dtstamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            dtstart = event['dtstart'].strftime('%Y%m%d')
            dtend = event['dtend'].strftime('%Y%m%d')

            lines.extend([
                'BEGIN:VEVENT',
                f'UID:{uid}',
                f'DTSTAMP:{dtstamp}',
                f'DTSTART;VALUE=DATE:{dtstart}',
                f'DTEND;VALUE=DATE:{dtend}',
                f'SUMMARY:{self._escape_ics_text(event["summary"])}',
                f'DESCRIPTION:{self._escape_ics_text(event.get("description", ""))}',
                f'CATEGORIES:{",".join(event.get("categories", []))}',
                'STATUS:CONFIRMED',
                'TRANSP:OPAQUE',
                'END:VEVENT',
            ])

        lines.extend([
            'END:VCALENDAR'
        ])

        return '\n'.join(lines)

    def _escape_ics_text(self, text: str) -> str:
        """Escape special characters for .ics format."""
        if not text:
            return ''

        # Replace newlines with literal \n
        text = text.replace('\n', '\\n')

        # Escape commas and semicolons
        text = text.replace(',', '\\,')
        text = text.replace(';', '\\;')

        return text
