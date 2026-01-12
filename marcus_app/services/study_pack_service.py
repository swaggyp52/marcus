"""
Study Pack Blueprint Generation Service (v0.38).

Transforms assessment artifacts into structured study blueprints with:
- Topics and skills extraction
- Lesson generation with citations
- Study checklist creation
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
import json
import re
from ..core.models import (
    StudyPack, StudyTopic, StudySkill, StudyLesson, 
    StudyCitation, StudyChecklistItem, Artifact, TextChunk,
    Assignment, Class
)


class BlueprintGenerator:
    """
    Generates study pack blueprints from assessment documents.
    """

    def __init__(self):
        self.max_citations_per_topic = 3

    def generate_blueprint(
        self,
        artifact_id: int,
        assignment_id: int,
        class_id: int,
        db: Session
    ) -> StudyPack:
        """
        Generate a complete study pack blueprint from an assessment artifact.

        Args:
            artifact_id: ID of assessment artifact (exam, quiz, homework)
            assignment_id: Associated assignment ID
            class_id: Associated class ID
            db: Database session

        Returns:
            StudyPack object with complete blueprint
        """
        # Load artifact and related data
        artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
        if not artifact:
            raise ValueError(f"Artifact {artifact_id} not found")

        assignment = db.query(Assignment).filter(Assignment.id == assignment_id).first()
        class_obj = db.query(Class).filter(Class.id == class_id).first()

        # Extract assessment content
        content = self._extract_artifact_content(artifact, db)

        # Parse topics from assessment structure
        topics_data = self._extract_topics(content, artifact_id, db)

        # Create study pack
        study_pack = StudyPack(
            assignment_id=assignment_id,
            class_id=class_id,
            artifact_id=artifact_id,
            title=self._generate_title(artifact, assignment),
            description=self._generate_description(topics_data),
            status="draft",
            quality_score=self._calculate_quality_score(topics_data)
        )
        db.add(study_pack)
        db.flush()  # Get the ID without committing

        # Create topics with skills and lessons
        for topic_data in topics_data:
            topic = self._create_topic(topic_data, study_pack, artifact_id, db)
            study_pack.topics.append(topic)

        # Create study checklist
        checklist_items = self._generate_checklist(topics_data, study_pack, db)

        db.add(study_pack)
        db.commit()

        return study_pack

    def _extract_artifact_content(self, artifact: Artifact, db: Session) -> str:
        """Extract full text content from artifact."""
        from ..services.extraction_service import ExtractionService
        extraction_service = ExtractionService()
        
        chunks = db.query(TextChunk).filter(
            TextChunk.artifact_id == artifact.id
        ).order_by(TextChunk.chunk_index).all()

        return "\n\n".join([chunk.content for chunk in chunks])

    def _extract_topics(
        self,
        content: str,
        artifact_id: int,
        db: Session
    ) -> List[Dict[str, Any]]:
        """
        Extract topics from assessment content.

        Uses multiple strategies:
        1. Header-based: Problems, Sections, Questions
        2. Keyword-based: Common exam keywords
        3. Semantic: Group related chunks
        """
        topics = []

        # Strategy 1: Problem/Question extraction
        problem_pattern = r"(?:Problem|Question|Exercise)\s+(\d+)[:\.]?\s*([^\n]+)"
        for match in re.finditer(problem_pattern, content, re.IGNORECASE):
            number, title = match.groups()
            topics.append({
                "title": f"Problem {number}: {title}",
                "order": len(topics),
                "description": self._extract_context(content, match.start(), 200),
                "type": "problem",
                "keywords": [title.lower()],
                "full_text": self._extract_section_text(content, match.start())
            })

        # Strategy 2: Section-based extraction
        section_pattern = r"^#+\s+([^\n]+)"
        for match in re.finditer(section_pattern, content, re.MULTILINE):
            title = match.group(1)
            if title not in [t["title"] for t in topics]:
                topics.append({
                    "title": title,
                    "order": len(topics),
                    "description": title,
                    "type": "section",
                    "keywords": self._extract_keywords(title),
                    "full_text": self._extract_section_text(content, match.start())
                })

        # If no topics found, create generic one
        if not topics:
            topics.append({
                "title": "Assessment Review",
                "order": 0,
                "description": "Complete assessment review",
                "type": "generic",
                "keywords": self._extract_keywords(content[:200]),
                "full_text": content
            })

        return topics

    def _create_topic(
        self,
        topic_data: Dict[str, Any],
        study_pack: StudyPack,
        artifact_id: int,
        db: Session
    ) -> StudyTopic:
        """Create a StudyTopic with skills, lessons, and citations."""
        topic = StudyTopic(
            study_pack_id=study_pack.id,
            title=topic_data["title"],
            order=topic_data["order"],
            description=topic_data.get("description", ""),
            is_grounded=True,
            confidence="medium",
            weighting="medium"
        )

        # Create skills (auto-generate based on topic)
        skills = self._generate_skills(topic_data["title"], topic_data["full_text"])
        for skill_data in skills:
            skill = StudySkill(
                topic_id=topic.id,
                type=skill_data["type"],
                description=skill_data["description"],
                order=skills.index(skill_data)
            )
            topic.skills.append(skill)

        # Create lesson
        lesson = self._generate_lesson(topic_data, db)
        topic.lessons.append(lesson)

        # Find and create citations
        citations = self._find_citations(
            topic_data,
            artifact_id,
            db
        )
        topic.citations.extend(citations)

        # Update grounded status
        topic.is_grounded = len([c for c in citations if not c.is_ungrounded]) > 0

        return topic

    def _generate_skills(self, title: str, content: str) -> List[Dict[str, str]]:
        """Generate skill types for a topic."""
        skills = []

        # Derive skill (if topic has computational aspects)
        if any(word in content.lower() for word in ["solve", "calculate", "design", "implement"]):
            skills.append({
                "type": "derive",
                "description": f"Solve problems related to {title}"
            })

        # Conceptual skill (always present)
        skills.append({
            "type": "conceptual",
            "description": f"Understand the key concepts of {title}"
        })

        # Memorize skill (if topic has definitions/terminology)
        if any(word in content.lower() for word in ["define", "term", "definition", "is"]):
            skills.append({
                "type": "memorize",
                "description": f"Recall key terms and definitions for {title}"
            })

        return skills

    def _generate_lesson(
        self,
        topic_data: Dict[str, Any],
        db: Session
    ) -> StudyLesson:
        """Generate lesson content for a topic."""
        content = topic_data["full_text"]

        # Extract key subpoints
        subpoints = self._extract_subpoints(content)

        # Extract common mistakes (if mentions "don't", "avoid", "common error")
        mistakes = self._extract_mistakes(content)

        lesson = StudyLesson(
            what_it_is=topic_data["description"][:255],
            key_subpoints=json.dumps(subpoints) if subpoints else None,
            common_mistakes=json.dumps(mistakes) if mistakes else None
        )

        return lesson

    def _find_citations(
        self,
        topic_data: Dict[str, Any],
        artifact_id: int,
        db: Session
    ) -> List[StudyCitation]:
        """Find and create citations for a topic."""
        citations = []

        # Search for chunks related to topic keywords
        keywords = topic_data.get("keywords", [])
        for keyword in keywords[:3]:  # Limit searches
            # Get chunks from this artifact that match the topic
            chunks = db.query(TextChunk).filter(
                TextChunk.artifact_id == artifact_id
            ).all()
            
            # Simple relevance matching
            matching_chunks = []
            keyword_lower = keyword.lower()
            for chunk in chunks:
                if keyword_lower in chunk.content.lower():
                    matching_chunks.append(chunk)
            
            for chunk in matching_chunks[:self.max_citations_per_topic - len(citations)]:
                citation = StudyCitation(
                    chunk_id=chunk.id,
                    artifact_id=artifact_id,
                    page_number=chunk.page_number,
                    section_title=chunk.section_title,
                    quote=chunk.content[:500],  # First 500 chars
                    relevance_score=8,  # Matched in content
                    is_ungrounded=False
                )
                citations.append(citation)
            
            # If we've found enough, stop searching
            if len(citations) >= self.max_citations_per_topic:
                break

        # If no citations found, mark as ungrounded
        if not citations:
            citation = StudyCitation(
                artifact_id=artifact_id,
                is_ungrounded=True,
                relevance_score=0
            )
            citations.append(citation)

        return citations

    def _generate_checklist(
        self,
        topics_data: List[Dict],
        study_pack: StudyPack,
        db: Session
    ) -> List[StudyChecklistItem]:
        """Generate study checklist from topics."""
        items = []

        for topic_data in topics_data:
            step = StudyChecklistItem(
                study_pack_id=study_pack.id,
                order=len(items),
                step_description=f"Master {topic_data['title']}",
                effort_estimate=self._estimate_effort(topic_data),
                self_check_prompt=f"Can you explain {topic_data['title']} to someone else?"
            )
            items.append(step)
            db.add(step)

        return items

    # Helper methods

    def _extract_context(self, text: str, position: int, length: int) -> str:
        """Extract context around a position."""
        start = max(0, position - 50)
        end = min(len(text), position + length)
        return text[start:end].strip()

    def _extract_section_text(self, content: str, start_pos: int, max_length: int = 500) -> str:
        """Extract text of a section."""
        # Find next header or end of content
        next_header = content.find("\n#", start_pos + 1)
        if next_header == -1:
            section = content[start_pos:start_pos + max_length]
        else:
            section = content[start_pos:next_header]
        return section[:max_length]

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract key terms from text."""
        # Simple keyword extraction - capitalized words and terms in quotes
        keywords = []
        
        # Quoted phrases
        quoted = re.findall(r'"([^"]+)"', text)
        keywords.extend(quoted[:3])

        # Capitalized terms (likely important)
        capitalized = re.findall(r'\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\b', text)
        keywords.extend(capitalized[:3])

        # Terms after "is", "means", "refers to"
        defined = re.findall(r'(?:is|means|refers to|defined as)\s+([^.]+)', text, re.IGNORECASE)
        keywords.extend(defined[:2])

        return list(set(keywords))[:5]  # Return unique, limited list

    def _extract_subpoints(self, text: str) -> List[str]:
        """Extract bullet points or subpoints from text."""
        points = []

        # Bullet points
        bullets = re.findall(r'^\s*[-*•]\s+([^\n]+)', text, re.MULTILINE)
        points.extend(bullets[:5])

        # Numbered points
        numbered = re.findall(r'^\s*\d+[\.\)]\s+([^\n]+)', text, re.MULTILINE)
        points.extend(numbered[:5])

        return points[:5]

    def _extract_mistakes(self, text: str) -> List[str]:
        """Extract common mistakes from text."""
        mistakes = []

        # Look for common patterns
        patterns = [
            r'(?:common|frequent)\s+(?:mistake|error|misconception)[s]?[:\s]+([^\n.]+)',
            r'do(?:n\'t|not)\s+([^\n.]+)',
            r'avoid\s+([^\n.]+)',
        ]

        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            mistakes.extend(matches[:2])

        return mistakes[:3]

    def _estimate_effort(self, topic_data: Dict[str, Any]) -> str:
        """Estimate effort required for a topic."""
        content = topic_data.get("full_text", "")
        word_count = len(content.split())

        if word_count < 200:
            return "S"
        elif word_count < 500:
            return "M"
        else:
            return "L"

    def _generate_title(self, artifact: Artifact, assignment: Optional[Assignment]) -> str:
        """Generate blueprint title."""
        if assignment:
            return f"Study Pack: {assignment.title}"
        return f"Study Pack: {artifact.original_filename}"

    def _generate_description(self, topics_data: List[Dict]) -> str:
        """Generate blueprint description."""
        if not topics_data:
            return "Study pack blueprint"
        return f"Comprehensive study guide for {len(topics_data)} topics"

    def _calculate_quality_score(self, topics_data: List[Dict]) -> int:
        """Calculate quality confidence score (1-10)."""
        # Start at 5 (medium)
        score = 5

        # More topics = higher confidence
        score = min(10, 5 + len(topics_data))

        return score
