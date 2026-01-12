"""
Integration tests for v0.44-alpha: Missions + Boxes

Tests:
- Mission CRUD operations
- Template creation (exam_prep)
- Box creation via templates
- Database integrity
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from marcus_app.core.models import Base, Mission, MissionBox, MissionState, BoxState
from marcus_app.services.mission_service import MissionService, MissionServiceError


def setup_test_db():
    """Create in-memory test database."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


def test_create_mission():
    """Test basic mission creation."""
    db = setup_test_db()

    mission = MissionService.create_mission(
        db=db,
        name="Test Mission",
        mission_type="exam_prep",
        class_id=None,
        assignment_id=None
    )

    assert mission.id is not None
    assert mission.name == "Test Mission"
    assert mission.mission_type == "exam_prep"
    assert mission.state == MissionState.DRAFT.value

    print("[PASS] test_create_mission")


def test_list_missions():
    """Test mission listing."""
    db = setup_test_db()

    # Create multiple missions
    MissionService.create_mission(db, "Mission 1", "exam_prep")
    MissionService.create_mission(db, "Mission 2", "code_review")
    MissionService.create_mission(db, "Mission 3", "exam_prep", class_id=1)

    # List all
    all_missions = MissionService.list_missions(db)
    assert len(all_missions) == 3

    # Filter by type
    exam_missions = MissionService.list_missions(db, mission_type="exam_prep")
    assert len(exam_missions) == 2

    # Filter by class
    class_missions = MissionService.list_missions(db, class_id=1)
    assert len(class_missions) == 1

    print("[PASS] test_list_missions")


def test_get_mission_detail():
    """Test getting mission with full detail."""
    db = setup_test_db()

    mission = MissionService.create_mission(db, "Detail Test", "exam_prep")
    detail = MissionService.get_mission_detail(db, mission.id)

    assert detail is not None
    assert detail['mission'].id == mission.id
    assert 'boxes' in detail
    assert 'artifacts' in detail
    assert 'practice_sessions' in detail

    print("[PASS] test_get_mission_detail")


def test_update_mission_state():
    """Test mission state transitions."""
    db = setup_test_db()

    mission = MissionService.create_mission(db, "State Test", "exam_prep")
    assert mission.state == MissionState.DRAFT.value

    # Update to active
    updated = MissionService.update_mission_state(db, mission.id, MissionState.ACTIVE.value)
    assert updated.state == MissionState.ACTIVE.value

    # Update to done
    updated = MissionService.update_mission_state(db, mission.id, MissionState.DONE.value)
    assert updated.state == MissionState.DONE.value

    # Try invalid state
    try:
        MissionService.update_mission_state(db, mission.id, "invalid_state")
        assert False, "Should have raised error"
    except MissionServiceError:
        pass  # Expected

    print("[PASS] test_update_mission_state")


def test_delete_mission():
    """Test mission deletion."""
    db = setup_test_db()

    mission = MissionService.create_mission(db, "Delete Test", "exam_prep")
    mission_id = mission.id

    # Delete
    deleted = MissionService.delete_mission(db, mission_id)
    assert deleted is True

    # Verify deleted
    mission = MissionService.get_mission(db, mission_id)
    assert mission is None

    # Try deleting non-existent
    deleted = MissionService.delete_mission(db, 99999)
    assert deleted is False

    print("[PASS] test_delete_mission")


def test_create_exam_prep_template():
    """Test exam prep template creation."""
    db = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="PHYS214 Midterm Prep",
        class_id=None,
        assignment_id=None
    )

    # Verify mission
    assert mission.id is not None
    assert mission.name == "PHYS214 Midterm Prep"
    assert mission.mission_type == "exam_prep"

    # Verify boxes created
    boxes = mission.boxes
    assert len(boxes) == 6, f"Expected 6 boxes, got {len(boxes)}"

    # Verify box types and order
    expected_types = ['inbox', 'extract', 'ask', 'practice', 'checker', 'citations']
    actual_types = [box.box_type for box in sorted(boxes, key=lambda b: b.order_index)]
    assert actual_types == expected_types, f"Expected {expected_types}, got {actual_types}"

    # Verify all boxes start in IDLE state
    for box in boxes:
        assert box.state == BoxState.IDLE.value

    # Verify config exists
    for box in boxes:
        assert box.config_json is not None

    print("[PASS] test_create_exam_prep_template")


def test_invalid_template():
    """Test error handling for invalid template."""
    db = setup_test_db()

    try:
        MissionService.create_from_template(
            db=db,
            template_name="nonexistent_template",
            mission_name="Test",
            class_id=None,
            assignment_id=None
        )
        assert False, "Should have raised error"
    except MissionServiceError as e:
        assert "Unknown template" in str(e)

    print("[PASS] test_invalid_template")


def test_box_order_preserved():
    """Test that boxes maintain execution order."""
    db = setup_test_db()

    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="Order Test"
    )

    boxes = sorted(mission.boxes, key=lambda b: b.order_index)

    # Verify sequential ordering
    for i, box in enumerate(boxes):
        assert box.order_index == i, f"Box {i} has order_index {box.order_index}"

    print("[PASS] test_box_order_preserved")


def run_all_tests():
    """Run all v0.44-alpha tests."""
    print("=" * 70)
    print("MARCUS v0.44-ALPHA INTEGRATION TESTS")
    print("=" * 70)

    tests = [
        test_create_mission,
        test_list_missions,
        test_get_mission_detail,
        test_update_mission_state,
        test_delete_mission,
        test_create_exam_prep_template,
        test_invalid_template,
        test_box_order_preserved
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except Exception as e:
            print(f"[FAIL] {test.__name__}: {e}")
            failed += 1

    print("=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed")
    print("=" * 70)

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
