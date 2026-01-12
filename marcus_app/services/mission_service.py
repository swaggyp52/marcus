"""
MissionService - v0.44-alpha

Manages mission lifecycle: create, list, get, delete, update state.
Creates missions from templates with pre-configured boxes.
"""

import json
from typing import List, Optional, Dict
from datetime import datetime
from sqlalchemy.orm import Session

from marcus_app.core.models import (
    Mission, MissionBox, MissionArtifact, PracticeSession, PracticeItem,
    MissionState, BoxState
)


class MissionServiceError(Exception):
    """Mission operation failed."""
    pass


class MissionService:
    """
    Service for managing missions and workflow orchestration.
    v0.44-alpha: Read-only operations + template creation.
    """

    # ========================================================================
    # MISSION CRUD
    # ========================================================================

    @staticmethod
    def create_mission(
        db: Session,
        name: str,
        mission_type: str,
        class_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        metadata: Optional[Dict] = None
    ) -> Mission:
        """
        Create a new mission.

        Args:
            db: Database session
            name: Mission name
            mission_type: Type of mission (exam_prep, code_review, research)
            class_id: Optional class ID to link
            assignment_id: Optional assignment ID to link
            metadata: Optional metadata dict

        Returns:
            Created Mission object
        """
        mission = Mission(
            name=name,
            mission_type=mission_type,
            state=MissionState.DRAFT.value,
            class_id=class_id,
            assignment_id=assignment_id,
            metadata_json=json.dumps(metadata) if metadata else None
        )

        db.add(mission)
        db.commit()
        db.refresh(mission)

        return mission

    @staticmethod
    def list_missions(
        db: Session,
        class_id: Optional[int] = None,
        mission_type: Optional[str] = None,
        state: Optional[str] = None
    ) -> List[Mission]:
        """
        List missions with optional filters.

        Args:
            db: Database session
            class_id: Filter by class ID
            mission_type: Filter by mission type
            state: Filter by mission state

        Returns:
            List of Mission objects
        """
        query = db.query(Mission)

        if class_id:
            query = query.filter(Mission.class_id == class_id)
        if mission_type:
            query = query.filter(Mission.mission_type == mission_type)
        if state:
            query = query.filter(Mission.state == state)

        return query.order_by(Mission.created_at.desc()).all()

    @staticmethod
    def get_mission(db: Session, mission_id: int) -> Optional[Mission]:
        """
        Get mission by ID.

        Args:
            db: Database session
            mission_id: Mission ID

        Returns:
            Mission object or None
        """
        return db.query(Mission).filter(Mission.id == mission_id).first()

    @staticmethod
    def get_mission_detail(db: Session, mission_id: int) -> Optional[Dict]:
        """
        Get mission with full detail including boxes and artifacts.

        Args:
            db: Database session
            mission_id: Mission ID

        Returns:
            Dict with mission, boxes, artifacts, practice_sessions
        """
        mission = MissionService.get_mission(db, mission_id)
        if not mission:
            return None

        return {
            'mission': mission,
            'boxes': mission.boxes,
            'artifacts': mission.artifacts,
            'practice_sessions': mission.practice_sessions
        }

    @staticmethod
    def update_mission_state(
        db: Session,
        mission_id: int,
        new_state: str
    ) -> Mission:
        """
        Update mission state.

        Args:
            db: Database session
            mission_id: Mission ID
            new_state: New state value

        Returns:
            Updated Mission object

        Raises:
            MissionServiceError: If mission not found or invalid state
        """
        mission = MissionService.get_mission(db, mission_id)
        if not mission:
            raise MissionServiceError(f"Mission {mission_id} not found")

        # Validate state
        valid_states = [s.value for s in MissionState]
        if new_state not in valid_states:
            raise MissionServiceError(f"Invalid state: {new_state}. Must be one of {valid_states}")

        mission.state = new_state
        db.commit()
        db.refresh(mission)

        return mission

    @staticmethod
    def delete_mission(db: Session, mission_id: int) -> bool:
        """
        Delete mission and all associated boxes/artifacts.

        Args:
            db: Database session
            mission_id: Mission ID

        Returns:
            True if deleted, False if not found
        """
        mission = MissionService.get_mission(db, mission_id)
        if not mission:
            return False

        db.delete(mission)
        db.commit()
        return True

    # ========================================================================
    # TEMPLATE CREATION
    # ========================================================================

    @staticmethod
    def create_from_template(
        db: Session,
        template_name: str,
        mission_name: str,
        class_id: Optional[int] = None,
        assignment_id: Optional[int] = None
    ) -> Mission:
        """
        Create mission from a pre-defined template.

        Args:
            db: Database session
            template_name: Template identifier (exam_prep, code_review, research)
            mission_name: Name for the created mission
            class_id: Optional class ID
            assignment_id: Optional assignment ID

        Returns:
            Created Mission with boxes

        Raises:
            MissionServiceError: If template not found
        """
        template_func = {
            'exam_prep': MissionService._create_exam_prep_template,
            'code_review': MissionService._create_code_review_template,
            'research': MissionService._create_research_template
        }.get(template_name)

        if not template_func:
            raise MissionServiceError(f"Unknown template: {template_name}")

        return template_func(db, mission_name, class_id, assignment_id)

    @staticmethod
    def _create_exam_prep_template(
        db: Session,
        name: str,
        class_id: Optional[int],
        assignment_id: Optional[int]
    ) -> Mission:
        """
        Create Exam Prep Mission template.

        Boxes (in order):
        1. InboxBox - ingest materials
        2. ExtractBox - chunk and index
        3. AskBox - scoped Q&A
        4. PracticeBox - generate practice questions
        5. CheckerBox - verify answers
        6. CitationsBox - show sources
        """
        mission = MissionService.create_mission(
            db=db,
            name=name,
            mission_type='exam_prep',
            class_id=class_id,
            assignment_id=assignment_id,
            metadata={'template_version': '1.0'}
        )

        # Create boxes in execution order
        boxes_config = [
            {'type': 'inbox', 'order': 0, 'config': {'max_artifacts': 20}},
            {'type': 'extract', 'order': 1, 'config': {'chunk_strategy': 'semantic'}},
            {'type': 'ask', 'order': 2, 'config': {'enable_search': True}},
            {'type': 'practice', 'order': 3, 'config': {'question_count': 10}},
            {'type': 'checker', 'order': 4, 'config': {'auto_verify': False}},
            {'type': 'citations', 'order': 5, 'config': {'show_confidence': True}}
        ]

        for box_config in boxes_config:
            box = MissionBox(
                mission_id=mission.id,
                box_type=box_config['type'],
                order_index=box_config['order'],
                state=BoxState.IDLE.value,
                config_json=json.dumps(box_config['config'])
            )
            db.add(box)

        db.commit()
        db.refresh(mission)

        return mission

    @staticmethod
    def _create_code_review_template(
        db: Session,
        name: str,
        class_id: Optional[int],
        assignment_id: Optional[int]
    ) -> Mission:
        """
        Create Code Review Mission template (stub for v0.44-beta+).
        """
        mission = MissionService.create_mission(
            db=db,
            name=name,
            mission_type='code_review',
            class_id=class_id,
            assignment_id=assignment_id,
            metadata={'template_version': '1.0', 'status': 'stub'}
        )
        return mission

    @staticmethod
    def _create_research_template(
        db: Session,
        name: str,
        class_id: Optional[int],
        assignment_id: Optional[int]
    ) -> Mission:
        """
        Create Research Mission template (stub for v0.44-beta+).
        """
        mission = MissionService.create_mission(
            db=db,
            name=name,
            mission_type='research',
            class_id=class_id,
            assignment_id=assignment_id,
            metadata={'template_version': '1.0', 'status': 'stub'}
        )
        return mission
