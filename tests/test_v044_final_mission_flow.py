"""
End-to-end integration test for v0.44-final: Complete mission workflow

Tests the full exam_prep mission flow:
1. Create mission from template
2. InboxBox: Link artifacts
3. ExtractBox: Chunk documents
4. AskBox: Ask question
5. PracticeBox: Generate practice session
6. CheckerBox: Verify answer
7. CitationsBox: Generate citation report

Verifies that all artifacts, states, and claims are created correctly.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json

from marcus_app.core.models import (
    Base, Mission, MissionBox, MissionArtifact, BoxState,
    Artifact, Assignment, Class, ExtractedText, TextChunk,
    PracticeSession, PracticeItem
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
    test_class = Class(code="PHYS214", name="Quantum Mechanics")
    db.add(test_class)
    db.commit()

    # Create test assignment
    test_assignment = Assignment(
        class_id=test_class.id,
        title="Midterm Exam Prep"
    )
    db.add(test_assignment)
    db.commit()

    # Create test artifact with extracted text and chunks
    test_artifact = Artifact(
        assignment_id=test_assignment.id,
        filename="quantum_notes.pdf",
        original_filename="quantum_notes.pdf",
        file_path="/fake/path/quantum_notes.pdf",
        file_type="pdf"
    )
    db.add(test_artifact)
    db.commit()

    # Add extracted text
    extracted_text = ExtractedText(
        artifact_id=test_artifact.id,
        content="Quantum mechanics is the study of matter and energy at the atomic scale. "
                "The Schrodinger equation is defined as: H*psi = E*psi where H is the Hamiltonian operator. "
                "Wave-particle duality demonstrates that particles exhibit both wave and particle properties.",
        extraction_method="test",
        extraction_status="success"
    )
    db.add(extracted_text)
    db.commit()

    # Add chunks
    chunks_content = [
        "Quantum mechanics is the study of matter and energy at the atomic scale.",
        "The Schrodinger equation is defined as: H*psi = E*psi where H is the Hamiltonian operator.",
        "Wave-particle duality demonstrates that particles exhibit both wave and particle properties."
    ]

    for i, content in enumerate(chunks_content):
        chunk = TextChunk(
            extracted_text_id=extracted_text.id,
            chunk_index=i,
            content=content,
            artifact_id=test_artifact.id,
            assignment_id=test_assignment.id,
            class_id=test_class.id,
            chunk_type="paragraph",
            word_count=len(content.split())
        )
        db.add(chunk)

    db.commit()

    return db, test_class, test_assignment, test_artifact


def test_full_mission_flow():
    """
    Test complete exam_prep mission flow from start to finish.

    This is the canonical demonstration that v0.44 works end-to-end.
    """
    print("\n" + "=" * 70)
    print("MARCUS v0.44-FINAL: END-TO-END MISSION FLOW TEST")
    print("=" * 70)

    db, test_class, test_assignment, test_artifact = setup_test_db()

    # Step 1: Create mission from template
    print("\n[1/7] Creating exam_prep mission...")
    mission = MissionService.create_from_template(
        db=db,
        template_name="exam_prep",
        mission_name="PHYS214 Midterm Prep"
    )
    assert mission.mission_type == 'exam_prep'
    assert len(mission.boxes) == 6
    print(f"  + Mission created: {mission.name}")
    print(f"  + Boxes: {[box.box_type for box in mission.boxes]}")

    # Get box references
    inbox_box = next(box for box in mission.boxes if box.box_type == 'inbox')
    extract_box = next(box for box in mission.boxes if box.box_type == 'extract')
    ask_box = next(box for box in mission.boxes if box.box_type == 'ask')
    practice_box = next(box for box in mission.boxes if box.box_type == 'practice')
    checker_box = next(box for box in mission.boxes if box.box_type == 'checker')
    citations_box = next(box for box in mission.boxes if box.box_type == 'citations')

    # Step 2: Run InboxBox
    print("\n[2/7] Running InboxBox to link artifacts...")
    inbox_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=inbox_box.id,
        input_payload={'artifact_ids': [test_artifact.id]}
    )
    assert inbox_result['state'] == BoxState.DONE.value
    assert len(inbox_result['artifacts']) == 1
    print(f"  + Linked {len(inbox_result['artifacts'])} document(s)")

    # Verify mission artifacts created
    mission_docs = db.query(MissionArtifact).filter(
        MissionArtifact.mission_id == mission.id,
        MissionArtifact.artifact_type == 'document'
    ).all()
    assert len(mission_docs) == 1
    print(f"  + Mission artifacts: {len(mission_docs)}")

    # Step 3: Run ExtractBox
    print("\n[3/7] Running ExtractBox to ensure chunking...")
    extract_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=extract_box.id,
        input_payload={}
    )
    assert extract_result['state'] == BoxState.DONE.value
    print(f"  + Extraction complete")

    # Verify chunks exist
    chunks = db.query(TextChunk).filter(TextChunk.artifact_id == test_artifact.id).all()
    assert len(chunks) > 0
    print(f"  + Chunks available: {len(chunks)}")

    # Step 4: Run AskBox
    print("\n[4/7] Running AskBox to answer question...")
    ask_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=ask_box.id,
        input_payload={
            'question': 'What is quantum mechanics?',
            'use_search': True
        }
    )
    assert ask_result['state'] == BoxState.DONE.value
    assert len(ask_result['artifacts']) == 1
    qa_artifact = ask_result['artifacts'][0]
    assert qa_artifact['type'] == 'qa'
    assert 'answer' in qa_artifact
    print(f"  + Question answered")
    print(f"  + Citations: {len(qa_artifact.get('citations', []))}")

    # Step 5: Run PracticeBox
    print("\n[5/7] Running PracticeBox to generate practice questions...")
    practice_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=practice_box.id,
        input_payload={
            'question_count': 3
        }
    )
    assert practice_result['state'] == BoxState.DONE.value
    assert len(practice_result['artifacts']) == 1
    practice_artifact = practice_result['artifacts'][0]
    assert practice_artifact['type'] == 'practice_session'
    session_id = practice_artifact['session_id']
    question_count = practice_artifact['question_count']
    print(f"  + Practice session created: {session_id}")
    print(f"  + Questions generated: {question_count}")

    # Verify practice session and items
    session = db.query(PracticeSession).filter(PracticeSession.id == session_id).first()
    assert session is not None
    assert session.state == 'active'
    assert len(session.items) == question_count
    print(f"  + Practice items in DB: {len(session.items)}")

    # Step 6: Answer a question and run CheckerBox
    print("\n[6/7] Running CheckerBox to verify answer...")

    # Get first practice item
    practice_item = session.items[0]
    item_id = practice_item.id

    # Submit answer
    user_answer = "Quantum mechanics studies the behavior of matter and energy at very small scales, like atoms and subatomic particles."

    checker_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=checker_box.id,
        input_payload={
            'session_id': session_id,
            'item_id': item_id,
            'user_answer': user_answer
        }
    )
    assert checker_result['state'] == BoxState.DONE.value
    assert len(checker_result['artifacts']) == 1
    verification = checker_result['artifacts'][0]
    assert verification['type'] == 'verification'
    assert 'result' in verification
    print(f"  + Answer verified: {verification['result']}")

    # Verify practice item updated
    db.refresh(practice_item)
    assert practice_item.user_answer == user_answer
    assert practice_item.state in ['correct', 'incorrect']
    print(f"  + Practice item state: {practice_item.state}")

    # Verify session score updated
    db.refresh(session)
    score = json.loads(session.score_json)
    assert score['attempted'] == 1
    print(f"  + Session score: {score}")

    # Step 7: Run CitationsBox
    print("\n[7/7] Running CitationsBox to generate citation report...")
    citations_result = BoxRunner.run_box(
        db=db,
        mission_id=mission.id,
        box_id=citations_box.id,
        input_payload={}
    )
    assert citations_result['state'] == BoxState.DONE.value
    assert len(citations_result['artifacts']) == 1
    citation_artifact = citations_result['artifacts'][0]
    assert citation_artifact['type'] == 'citation'
    print(f"  + Citation report generated")
    print(f"  + Total citations tracked: {citation_artifact['total_citations']}")

    # Final verification: Check all boxes completed
    print("\n" + "=" * 70)
    print("FINAL VERIFICATION")
    print("=" * 70)

    db.refresh(mission)

    box_states = {}
    for box in mission.boxes:
        db.refresh(box)
        box_states[box.box_type] = box.state
        print(f"  {box.box_type:12} -> {box.state}")

    # Verify all boxes reached done state
    assert inbox_box.state == BoxState.DONE.value
    assert extract_box.state == BoxState.DONE.value
    assert ask_box.state == BoxState.DONE.value
    assert practice_box.state == BoxState.DONE.value
    assert checker_box.state == BoxState.DONE.value
    assert citations_box.state == BoxState.DONE.value

    # Count artifacts created
    all_artifacts = db.query(MissionArtifact).filter(
        MissionArtifact.mission_id == mission.id
    ).all()

    print(f"\n  Total mission artifacts: {len(all_artifacts)}")

    artifact_types = {}
    for artifact in all_artifacts:
        artifact_types[artifact.artifact_type] = artifact_types.get(artifact.artifact_type, 0) + 1

    print(f"  Artifact breakdown:")
    for artifact_type, count in artifact_types.items():
        print(f"    - {artifact_type}: {count}")

    print("\n" + "=" * 70)
    print("END-TO-END TEST PASSED")
    print("=" * 70)
    print("\nv0.44-final workflow proven: All 6 boxes executed successfully.")
    print("Mission state machine works. Artifact creation works. Citations work.")
    print("\nMarcus missions are now end-to-end executable.")

    return True


if __name__ == "__main__":
    try:
        success = test_full_mission_flow()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n[FAIL] End-to-end test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
