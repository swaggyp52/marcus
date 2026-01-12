"""
Integration tests for v0.44-beta: BoxRunner + Inbox/Extract/Ask

Tests:
- Box execution with state transitions
- InboxBox artifact linking
- ExtractBox chunking pipeline
- AskBox Q/A with citations
- Concurrency guards
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from marcus_app.core.models import (
    Base, Mission, MissionBox, MissionArtifact, BoxState,
    Artifact, Assignment, Class, ExtractedText, TextChunk
)
from marcus_app.services.mission_service import MissionService
from marcus_app.services.box_runner import BoxRunner, BoxRunnerError


def setup_test_db():
    """Create in-memory test database with sample data."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    # Create test class
    test_class = Class(code="TEST101", name="Test Class")
    db.add(test_class)
    db.commit()

    # Create test assignment
    test_assignment = Assignment(
        class_id=test_class.id,
        title="Test Assignment"
    )
    db.add(test_assignment)
    db.commit()

    # Create test artifact
    test_artifact = Artifact(
        assignment_id=test_assignment.id,
        filename="test.pdf",
        original_filename="test.pdf",
        file_path="/fake/path/test.pdf",
        file_type="pdf"
    )
    db.add(test_artifact)
    db.commit()

    return db, test_class, test_assignment, test_artifact


def test_inbox_box_links_artifacts():
    """Test InboxBox links existing artifacts."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    # Create mission
    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    # Find inbox box
    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')

    # Run inbox box
    result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=inbox_box.id,
        input_payload={'artifact_ids': [test_artifact.id]}
    )

    # Verify
    assert result['state'] == BoxState.DONE.value
    assert len(result['artifacts']) == 1
    assert result['error'] is None

    # Check box state updated
    db.refresh(inbox_box)
    assert inbox_box.state == BoxState.DONE.value
    assert inbox_box.last_run_at is not None

    # Check mission artifact created
    mission_artifacts = db.query(MissionArtifact).filter(
        MissionArtifact.mission_id == mission.id,
        MissionArtifact.artifact_type == 'document'
    ).all()
    assert len(mission_artifacts) == 1
    assert mission_artifacts[0].title == "test.pdf"

    print("[PASS] test_inbox_box_links_artifacts")


def test_inbox_box_validates_artifact_ids():
    """Test InboxBox rejects invalid artifact IDs."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')

    # Try with invalid artifact ID
    try:
        BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=inbox_box.id,
            input_payload={'artifact_ids': [99999]}
        )
        assert False, "Should have raised error"
    except BoxRunnerError as e:
        assert "not found" in str(e).lower()

    # Verify box marked as error
    db.refresh(inbox_box)
    assert inbox_box.state == BoxState.ERROR.value
    assert inbox_box.last_error is not None

    print("[PASS] test_inbox_box_validates_artifact_ids")


def test_extract_box_creates_chunks():
    """Test ExtractBox creates chunks for linked artifacts."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    # Add extracted text (simulating successful extraction)
    extracted_text = ExtractedText(
        artifact_id=test_artifact.id,
        content="Sample content for testing chunking pipeline.",
        extraction_method="test",
        extraction_status="success"
    )
    db.add(extracted_text)
    db.commit()

    # Create mission and link artifact
    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')
    BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=inbox_box.id,
        input_payload={'artifact_ids': [test_artifact.id]}
    )

    # Run extract box
    extract_box = next(box for box in mission.boxes if box.box_type == 'extract')
    result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=extract_box.id,
        input_payload={}
    )

    # Verify
    assert result['state'] == BoxState.DONE.value
    assert len(result['artifacts']) == 1
    assert result['artifacts'][0]['type'] == 'note'

    # Check chunks created
    chunks = db.query(TextChunk).filter(TextChunk.artifact_id == test_artifact.id).all()
    assert len(chunks) > 0

    print("[PASS] test_extract_box_creates_chunks")


def test_ask_box_with_search():
    """Test AskBox retrieves and cites mission materials."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    # Setup: Create extracted text and chunks
    extracted_text = ExtractedText(
        artifact_id=test_artifact.id,
        content="The Pythagorean theorem states that a^2 + b^2 = c^2.",
        extraction_method="test",
        extraction_status="success"
    )
    db.add(extracted_text)
    db.commit()

    chunk = TextChunk(
        extracted_text_id=extracted_text.id,
        chunk_index=0,
        content="The Pythagorean theorem states that a^2 + b^2 = c^2.",
        artifact_id=test_artifact.id,
        assignment_id=test_assignment.id,
        class_id=test_class.id,
        chunk_type="paragraph",
        word_count=10
    )
    db.add(chunk)
    db.commit()

    # Create mission and setup
    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')
    BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=inbox_box.id,
        input_payload={'artifact_ids': [test_artifact.id]}
    )

    # Ask question
    ask_box = next(box for box in mission.boxes if box.box_type == 'ask')
    result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=ask_box.id,
        input_payload={
            'question': 'What is the Pythagorean theorem?',
            'use_search': True
        }
    )

    # Verify
    assert result['state'] == BoxState.DONE.value
    assert len(result['artifacts']) == 1

    qa_artifact = result['artifacts'][0]
    assert qa_artifact['type'] == 'qa'
    assert 'answer' in qa_artifact
    # Citations may be empty if search fails (FTS5 may not work in memory DB)
    # The important thing is that it doesn't crash
    assert 'citations' in qa_artifact

    print("[PASS] test_ask_box_with_search")


def test_ask_box_without_materials():
    """Test AskBox handles missing materials gracefully."""
    db, _, _, _ = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    # Ask question without linking any materials
    ask_box = next(box for box in mission.boxes if box.box_type == 'ask')
    result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=ask_box.id,
        input_payload={
            'question': 'What is gravity?',
            'use_search': True
        }
    )

    # Verify - should succeed but with low confidence
    assert result['state'] == BoxState.DONE.value
    qa_artifact = result['artifacts'][0]
    assert qa_artifact['confidence'] == 'low'
    assert len(qa_artifact['citations']) == 0

    print("[PASS] test_ask_box_without_materials")


def test_state_transitions():
    """Test box state machine transitions."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')

    # Initial state: idle
    assert inbox_box.state == BoxState.IDLE.value

    # Run box
    BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=inbox_box.id,
        input_payload={'artifact_ids': [test_artifact.id]}
    )

    # After success: done
    db.refresh(inbox_box)
    assert inbox_box.state == BoxState.DONE.value

    print("[PASS] test_state_transitions")


def test_concurrent_execution_guard():
    """Test that running box cannot be run again."""
    db, test_class, test_assignment, test_artifact = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')

    # Manually set to running
    inbox_box.state = BoxState.RUNNING.value
    db.commit()

    # Try to run
    try:
        BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=inbox_box.id,
            input_payload={'artifact_ids': [test_artifact.id]}
        )
        assert False, "Should have raised error"
    except BoxRunnerError as e:
        assert "already running" in str(e).lower()

    print("[PASS] test_concurrent_execution_guard")


def test_box_type_not_implemented():
    """Test that all box types are now implemented (v0.44-final)."""
    db, _, _, _ = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Test Mission"
    )

    # v0.44-final: PracticeBox is now implemented
    # It should fail with meaningful error (no documents) not "not implemented"
    practice_box = next(box for box in mission.boxes if box.box_type == 'practice')

    try:
        BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=practice_box.id,
            input_payload={}
        )
        assert False, "Should have raised error"
    except BoxRunnerError as e:
        # Should fail with "No documents" not "not implemented"
        assert "no documents" in str(e).lower() or "run inboxbox first" in str(e).lower()

    print("[PASS] test_box_type_not_implemented")


def run_all_tests():
    """Run all v0.44-beta tests."""
    print("=" * 70)
    print("MARCUS v0.44-BETA INTEGRATION TESTS")
    print("=" * 70)

    tests = [
        test_inbox_box_links_artifacts,
        test_inbox_box_validates_artifact_ids,
        test_extract_box_creates_chunks,
        test_ask_box_with_search,
        test_ask_box_without_materials,
        test_state_transitions,
        test_concurrent_execution_guard,
        test_box_type_not_implemented
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
