"""
Quick demonstration of v0.44-final: Complete Mission Workflow

This script demonstrates all 6 box types working together in a real mission.
Run with: python demo_v044_mission.py
"""

from marcus_app.core.database import SessionLocal
from marcus_app.services.mission_service import MissionService
from marcus_app.services.box_runner import BoxRunner
from marcus_app.core.models import (
    Class, Assignment, Artifact, ExtractedText, TextChunk
)
import json


def create_test_data(db):
    """Create minimal test data for demo."""
    # Create class
    test_class = Class(code="DEMO101", name="Demo Class")
    db.add(test_class)
    db.commit()

    # Create assignment
    test_assignment = Assignment(
        class_id=test_class.id,
        title="Demo Assignment"
    )
    db.add(test_assignment)
    db.commit()

    # Create artifact
    test_artifact = Artifact(
        assignment_id=test_assignment.id,
        filename="demo.pdf",
        original_filename="demo.pdf",
        file_path="/demo/path/demo.pdf",
        file_type="pdf"
    )
    db.add(test_artifact)
    db.commit()

    # Add extracted text
    extracted_text = ExtractedText(
        artifact_id=test_artifact.id,
        content="Machine learning is the study of algorithms that improve through experience. "
                "The fundamental equation is: Loss = f(y_pred, y_true). "
                "Neural networks are composed of layers of interconnected nodes.",
        extraction_method="demo",
        extraction_status="success"
    )
    db.add(extracted_text)
    db.commit()

    # Add chunks
    chunks_content = [
        "Machine learning is the study of algorithms that improve through experience.",
        "The fundamental equation is: Loss = f(y_pred, y_true).",
        "Neural networks are composed of layers of interconnected nodes."
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

    return test_artifact.id


def main():
    print("\n" + "=" * 70)
    print("MARCUS v0.44-FINAL DEMONSTRATION")
    print("Complete Mission Workflow - All 6 Boxes")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Setup
        print("\n[SETUP] Creating test data...")
        artifact_id = create_test_data(db)
        print(f"  + Test artifact created: {artifact_id}")

        # Step 1: Create Mission
        print("\n[STEP 1/7] Creating exam_prep mission...")
        mission = MissionService.create_from_template(
            db=db,
            template_name="exam_prep",
            mission_name="ML Fundamentals Demo"
        )
        print(f"  + Mission created: {mission.name} (ID: {mission.id})")
        print(f"  + Boxes: {[box.box_type for box in mission.boxes]}")

        # Get box references
        boxes = {box.box_type: box for box in mission.boxes}

        # Step 2: InboxBox
        print("\n[STEP 2/7] Running InboxBox to link artifact...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['inbox'].id,
            input_payload={'artifact_ids': [artifact_id]}
        )
        print(f"  + State: {result['state']}")
        print(f"  + Artifacts linked: {len(result['artifacts'])}")

        # Step 3: ExtractBox
        print("\n[STEP 3/7] Running ExtractBox to ensure chunking...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['extract'].id,
            input_payload={}
        )
        print(f"  + State: {result['state']}")
        print(f"  + Extraction complete")

        # Step 4: AskBox
        print("\n[STEP 4/7] Running AskBox to answer question...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['ask'].id,
            input_payload={
                'question': 'What is machine learning?',
                'use_search': True
            }
        )
        print(f"  + State: {result['state']}")
        qa = result['artifacts'][0]
        print(f"  + Answer preview: {qa['answer'][:80]}...")
        print(f"  + Confidence: {qa['confidence']}")

        # Step 5: PracticeBox
        print("\n[STEP 5/7] Running PracticeBox to generate questions...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['practice'].id,
            input_payload={'question_count': 3}
        )
        print(f"  + State: {result['state']}")
        practice = result['artifacts'][0]
        session_id = practice['session_id']
        print(f"  + Practice session: {session_id}")
        print(f"  + Questions generated: {practice['question_count']}")

        # Get practice items
        from marcus_app.core.models import PracticeSession
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id
        ).first()
        first_item = session.items[0]

        print(f"\n  Example question:")
        print(f"  {first_item.prompt_md[:100]}...")

        # Step 6: CheckerBox
        print("\n[STEP 6/7] Running CheckerBox to verify answer...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['checker'].id,
            input_payload={
                'session_id': session_id,
                'item_id': first_item.id,
                'user_answer': "Machine learning involves algorithms that learn from data and improve their performance over time through experience."
            }
        )
        print(f"  + State: {result['state']}")
        verification = result['artifacts'][0]
        print(f"  + Result: {verification['result']}")

        # Check updated score
        db.refresh(session)
        score = json.loads(session.score_json)
        print(f"  + Session score: {score}")

        # Step 7: CitationsBox
        print("\n[STEP 7/7] Running CitationsBox to generate report...")
        result = BoxRunner.run_box(
            db=db,
            mission_id=mission.id,
            box_id=boxes['citations'].id,
            input_payload={}
        )
        print(f"  + State: {result['state']}")
        citations = result['artifacts'][0]
        print(f"  + Total citations: {citations['total_citations']}")

        # Final Summary
        print("\n" + "=" * 70)
        print("MISSION COMPLETE")
        print("=" * 70)

        from marcus_app.core.models import MissionArtifact
        all_artifacts = db.query(MissionArtifact).filter(
            MissionArtifact.mission_id == mission.id
        ).all()

        print(f"\nMission: {mission.name}")
        print(f"Total artifacts created: {len(all_artifacts)}")
        print(f"\nArtifacts by type:")
        artifact_types = {}
        for artifact in all_artifacts:
            artifact_types[artifact.artifact_type] = artifact_types.get(artifact.artifact_type, 0) + 1
        for artifact_type, count in artifact_types.items():
            print(f"  - {artifact_type}: {count}")

        print(f"\nBox states:")
        for box in mission.boxes:
            db.refresh(box)
            print(f"  - {box.box_type:12} -> {box.state}")

        print("\n" + "=" * 70)
        print("DEMONSTRATION SUCCESSFUL")
        print("=" * 70)
        print("\nv0.44-final is working correctly.")
        print("All 6 boxes executed successfully.")
        print("Mission workflow is end-to-end functional.\n")

    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

    return True


if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
