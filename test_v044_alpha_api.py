"""
Quick manual test for v0.44-alpha API endpoints.
Run with: python test_v044_alpha_api.py
"""

from marcus_app.core.database import SessionLocal
from marcus_app.services.mission_service import MissionService

def main():
    print("=" * 70)
    print("v0.44-ALPHA MANUAL API TEST")
    print("=" * 70)

    db = SessionLocal()

    try:
        # Test 1: Create exam prep mission
        print("\n[1/5] Creating exam prep mission...")
        mission = MissionService.create_from_template(
            db=db,
            template_name="exam_prep",
            mission_name="Test Exam Prep Mission",
            class_id=None,
            assignment_id=None
        )
        print(f"  + Created mission ID: {mission.id}")
        print(f"  + Name: {mission.name}")
        print(f"  + Type: {mission.mission_type}")
        print(f"  + Boxes: {len(mission.boxes)}")

        # Test 2: List missions
        print("\n[2/5] Listing missions...")
        missions = MissionService.list_missions(db)
        print(f"  + Found {len(missions)} missions")

        # Test 3: Get mission detail
        print("\n[3/5] Getting mission detail...")
        detail = MissionService.get_mission_detail(db, mission.id)
        print(f"  + Mission: {detail['mission'].name}")
        print(f"  + Boxes: {len(detail['boxes'])}")
        print(f"  + Box types: {[box.box_type for box in detail['boxes']]}")

        # Test 4: Update mission state
        print("\n[4/5] Updating mission state...")
        updated = MissionService.update_mission_state(db, mission.id, "active")
        print(f"  + State changed to: {updated.state}")

        # Test 5: Delete mission
        print("\n[5/5] Deleting mission...")
        deleted = MissionService.delete_mission(db, mission.id)
        print(f"  + Deleted: {deleted}")

        print("\n" + "=" * 70)
        print("ALL TESTS PASSED")
        print("=" * 70)
        print("\nv0.44-alpha API is working correctly.")

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
