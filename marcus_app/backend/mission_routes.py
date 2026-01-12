"""
Mission Routes - v0.44-alpha

API endpoints for mission management (read-only + template creation).
Box execution will be added in v0.44-beta.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional, List
from pydantic import BaseModel

from marcus_app.core.database import get_db
from marcus_app.services.mission_service import MissionService, MissionServiceError


router = APIRouter(prefix="/api/missions", tags=["missions"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class CreateMissionRequest(BaseModel):
    name: str
    mission_type: str
    class_id: Optional[int] = None
    assignment_id: Optional[int] = None


class CreateFromTemplateRequest(BaseModel):
    template_name: str
    mission_name: str
    class_id: Optional[int] = None
    assignment_id: Optional[int] = None


class UpdateStateRequest(BaseModel):
    state: str


# ============================================================================
# AUTH DEPENDENCY (reuse existing)
# ============================================================================

def require_auth():
    """Require authentication - stub for v0.44-alpha."""
    # TODO: Integrate with existing auth service from v0.42
    # For now, allow all requests in development
    return True


# ============================================================================
# MISSION ENDPOINTS
# ============================================================================

@router.post("/create")
async def create_mission(
    request: CreateMissionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a new mission manually.

    For most users, use /create-from-template instead.
    """
    try:
        mission = MissionService.create_mission(
            db=db,
            name=request.name,
            mission_type=request.mission_type,
            class_id=request.class_id,
            assignment_id=request.assignment_id
        )

        return {
            'id': mission.id,
            'name': mission.name,
            'mission_type': mission.mission_type,
            'state': mission.state,
            'created_at': mission.created_at.isoformat()
        }

    except MissionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")


@router.post("/create-from-template")
async def create_from_template(
    request: CreateFromTemplateRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a mission from a pre-defined template.

    Templates:
    - exam_prep: Exam preparation workflow (InboxBox → ExtractBox → AskBox → PracticeBox → CheckerBox → CitationsBox)
    - code_review: Code review workflow (stub)
    - research: Research workflow (stub)
    """
    try:
        mission = MissionService.create_from_template(
            db=db,
            template_name=request.template_name,
            mission_name=request.mission_name,
            class_id=request.class_id,
            assignment_id=request.assignment_id
        )

        # Return mission with boxes
        return {
            'id': mission.id,
            'name': mission.name,
            'mission_type': mission.mission_type,
            'state': mission.state,
            'boxes': [
                {
                    'id': box.id,
                    'type': box.box_type,
                    'order': box.order_index,
                    'state': box.state
                }
                for box in mission.boxes
            ],
            'created_at': mission.created_at.isoformat()
        }

    except MissionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create mission: {str(e)}")


@router.get("")
async def list_missions(
    class_id: Optional[int] = None,
    mission_type: Optional[str] = None,
    state: Optional[str] = None,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    List all missions with optional filters.

    Query params:
    - class_id: Filter by class
    - mission_type: Filter by type (exam_prep, code_review, research)
    - state: Filter by state (draft, active, blocked, done)
    """
    try:
        missions = MissionService.list_missions(
            db=db,
            class_id=class_id,
            mission_type=mission_type,
            state=state
        )

        return [
            {
                'id': mission.id,
                'name': mission.name,
                'mission_type': mission.mission_type,
                'state': mission.state,
                'class_id': mission.class_id,
                'assignment_id': mission.assignment_id,
                'box_count': len(mission.boxes),
                'artifact_count': len(mission.artifacts),
                'created_at': mission.created_at.isoformat(),
                'updated_at': mission.updated_at.isoformat()
            }
            for mission in missions
        ]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list missions: {str(e)}")


@router.get("/{mission_id}")
async def get_mission_detail(
    mission_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Get full mission detail including boxes and artifacts.
    """
    try:
        detail = MissionService.get_mission_detail(db=db, mission_id=mission_id)

        if not detail:
            raise HTTPException(status_code=404, detail="Mission not found")

        mission = detail['mission']

        return {
            'mission': {
                'id': mission.id,
                'name': mission.name,
                'mission_type': mission.mission_type,
                'state': mission.state,
                'class_id': mission.class_id,
                'assignment_id': mission.assignment_id,
                'created_at': mission.created_at.isoformat(),
                'updated_at': mission.updated_at.isoformat()
            },
            'boxes': [
                {
                    'id': box.id,
                    'type': box.box_type,
                    'order': box.order_index,
                    'state': box.state,
                    'last_run_at': box.last_run_at.isoformat() if box.last_run_at else None,
                    'last_error': box.last_error
                }
                for box in detail['boxes']
            ],
            'artifacts': [
                {
                    'id': artifact.id,
                    'type': artifact.artifact_type,
                    'title': artifact.title,
                    'box_id': artifact.box_id,
                    'created_at': artifact.created_at.isoformat()
                }
                for artifact in detail['artifacts']
            ],
            'practice_sessions': [
                {
                    'id': session.id,
                    'state': session.state,
                    'item_count': len(session.items),
                    'created_at': session.created_at.isoformat()
                }
                for session in detail['practice_sessions']
            ]
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get mission: {str(e)}")


@router.patch("/{mission_id}")
async def update_mission_state(
    mission_id: int,
    request: UpdateStateRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Update mission state.

    Valid states: draft, active, blocked, done
    """
    try:
        mission = MissionService.update_mission_state(
            db=db,
            mission_id=mission_id,
            new_state=request.state
        )

        return {
            'id': mission.id,
            'state': mission.state,
            'updated_at': mission.updated_at.isoformat()
        }

    except MissionServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to update mission: {str(e)}")


@router.delete("/{mission_id}")
async def delete_mission(
    mission_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Delete mission and all associated data.
    """
    try:
        deleted = MissionService.delete_mission(db=db, mission_id=mission_id)

        if not deleted:
            raise HTTPException(status_code=404, detail="Mission not found")

        return {'success': True, 'message': 'Mission deleted'}

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete mission: {str(e)}")


# ============================================================================
# BOX ENDPOINTS (v0.44-beta)
# ============================================================================

@router.get("/{mission_id}/boxes/{box_id}")
async def get_box_detail(
    mission_id: int,
    box_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Get box detail.
    """
    from marcus_app.core.models import MissionBox

    box = db.query(MissionBox).filter(
        MissionBox.id == box_id,
        MissionBox.mission_id == mission_id
    ).first()

    if not box:
        raise HTTPException(status_code=404, detail="Box not found")

    return {
        'id': box.id,
        'mission_id': box.mission_id,
        'type': box.box_type,
        'order': box.order_index,
        'state': box.state,
        'config': box.config_json,
        'last_run_at': box.last_run_at.isoformat() if box.last_run_at else None,
        'last_error': box.last_error,
        'artifact_count': len(box.artifacts)
    }


class RunBoxRequest(BaseModel):
    input_payload: Optional[dict] = None


@router.post("/{mission_id}/boxes/{box_id}/run")
async def run_box(
    mission_id: int,
    box_id: int,
    request: RunBoxRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Execute a box.

    v0.44-beta supports: inbox, extract, ask
    v0.44-final will add: practice, checker, citations

    Input payload varies by box type:
    - inbox: {artifact_ids: [1, 2, 3]}
    - extract: {} (no input required)
    - ask: {question: str, use_search: bool}
    """
    from marcus_app.services.box_runner import BoxRunner, BoxRunnerError

    try:
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission_id,
            box_id=box_id,
            input_payload=request.input_payload
        )

        return result

    except BoxRunnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Box execution failed: {str(e)}")


# Convenience endpoints

@router.post("/{mission_id}/inbox/link")
async def link_artifacts_to_mission(
    mission_id: int,
    artifact_ids: List[int],
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Convenience endpoint: Link artifacts to mission via InboxBox.

    Finds the inbox box and runs it with artifact_ids.
    """
    from marcus_app.core.models import MissionBox
    from marcus_app.services.box_runner import BoxRunner, BoxRunnerError

    # Find inbox box
    inbox_box = db.query(MissionBox).filter(
        MissionBox.mission_id == mission_id,
        MissionBox.box_type == 'inbox'
    ).first()

    if not inbox_box:
        raise HTTPException(status_code=404, detail="InboxBox not found in mission")

    try:
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission_id,
            box_id=inbox_box.id,
            input_payload={'artifact_ids': artifact_ids}
        )

        return result

    except BoxRunnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to link artifacts: {str(e)}")


class AskQuestionRequest(BaseModel):
    question: str
    use_search: bool = True


@router.post("/{mission_id}/ask")
async def ask_question(
    mission_id: int,
    request: AskQuestionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Convenience endpoint: Ask a question in mission context.

    Finds the ask box and runs it with question.
    """
    from marcus_app.core.models import MissionBox
    from marcus_app.services.box_runner import BoxRunner, BoxRunnerError

    # Find ask box
    ask_box = db.query(MissionBox).filter(
        MissionBox.mission_id == mission_id,
        MissionBox.box_type == 'ask'
    ).first()

    if not ask_box:
        raise HTTPException(status_code=404, detail="AskBox not found in mission")

    try:
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission_id,
            box_id=ask_box.id,
            input_payload={
                'question': request.question,
                'use_search': request.use_search
            }
        )

        return result

    except BoxRunnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to answer question: {str(e)}")


# ============================================================================
# PRACTICE WORKFLOW ENDPOINTS (v0.44-final)
# ============================================================================

class CreatePracticeRequest(BaseModel):
    topic_keywords: Optional[str] = None
    question_count: int = 10


@router.post("/{mission_id}/practice/create")
async def create_practice_session(
    mission_id: int,
    request: CreatePracticeRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Create a practice session for the mission.

    Finds the practice box and runs it to generate questions.
    """
    from marcus_app.core.models import MissionBox
    from marcus_app.services.box_runner import BoxRunner, BoxRunnerError

    # Find practice box
    practice_box = db.query(MissionBox).filter(
        MissionBox.mission_id == mission_id,
        MissionBox.box_type == 'practice'
    ).first()

    if not practice_box:
        raise HTTPException(status_code=404, detail="PracticeBox not found in mission")

    try:
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission_id,
            box_id=practice_box.id,
            input_payload={
                'topic_keywords': request.topic_keywords,
                'question_count': request.question_count
            }
        )

        return result

    except BoxRunnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create practice session: {str(e)}")


class AnswerQuestionRequest(BaseModel):
    user_answer: str


@router.post("/practice/{session_id}/items/{item_id}/answer")
async def submit_answer(
    session_id: int,
    item_id: int,
    request: AnswerQuestionRequest,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Submit an answer to a practice question.

    This only stores the answer, doesn't check it yet.
    Use /check endpoint to verify the answer.
    """
    from marcus_app.core.models import PracticeItem

    practice_item = db.query(PracticeItem).filter(
        PracticeItem.id == item_id,
        PracticeItem.session_id == session_id
    ).first()

    if not practice_item:
        raise HTTPException(status_code=404, detail="Practice item not found")

    # Store answer without checking
    practice_item.user_answer = request.user_answer
    practice_item.state = 'answered'
    db.commit()

    return {
        'item_id': item_id,
        'session_id': session_id,
        'state': practice_item.state,
        'message': 'Answer submitted. Use /check to verify.'
    }


@router.post("/practice/{session_id}/items/{item_id}/check")
async def check_answer(
    session_id: int,
    item_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Check a submitted answer using CheckerBox.

    The practice item must already have a user_answer.
    """
    from marcus_app.core.models import PracticeSession, PracticeItem, MissionBox
    from marcus_app.services.box_runner import BoxRunner, BoxRunnerError

    # Verify practice item exists and has answer
    practice_item = db.query(PracticeItem).filter(
        PracticeItem.id == item_id,
        PracticeItem.session_id == session_id
    ).first()

    if not practice_item:
        raise HTTPException(status_code=404, detail="Practice item not found")

    if not practice_item.user_answer:
        raise HTTPException(status_code=400, detail="No answer submitted yet. Use /answer first.")

    # Get mission_id from session
    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    # Find checker box
    checker_box = db.query(MissionBox).filter(
        MissionBox.mission_id == session.mission_id,
        MissionBox.box_type == 'checker'
    ).first()

    if not checker_box:
        raise HTTPException(status_code=404, detail="CheckerBox not found in mission")

    try:
        result = BoxRunner.run_box(
            db=db,
            mission_id=session.mission_id,
            box_id=checker_box.id,
            input_payload={
                'session_id': session_id,
                'item_id': item_id,
                'user_answer': practice_item.user_answer
            }
        )

        return result

    except BoxRunnerError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to check answer: {str(e)}")


@router.get("/practice/{session_id}")
async def get_practice_session(
    session_id: int,
    db: Session = Depends(get_db),
    _: bool = Depends(require_auth)
):
    """
    Get practice session detail with all items.
    """
    from marcus_app.core.models import PracticeSession
    import json

    session = db.query(PracticeSession).filter(
        PracticeSession.id == session_id
    ).first()

    if not session:
        raise HTTPException(status_code=404, detail="Practice session not found")

    score = json.loads(session.score_json) if session.score_json else {}

    return {
        'session': {
            'id': session.id,
            'mission_id': session.mission_id,
            'state': session.state,
            'score': score,
            'created_at': session.created_at.isoformat()
        },
        'items': [
            {
                'id': item.id,
                'prompt_md': item.prompt_md,
                'user_answer': item.user_answer,
                'state': item.state,
                'citations_json': item.citations_json,
                'checks_json': item.checks_json,
                'answered_at': item.answered_at.isoformat() if item.answered_at else None
            }
            for item in session.items
        ]
    }
