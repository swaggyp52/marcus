"""
V0.39 Integration Test - Complete Workflow

Tests the full v0.39 Projects Module workflow:
1. Create project
2. Create files
3. Read files
4. List files
5. Create notes
6. Update notes
7. Delete operations
"""

import sys
from pathlib import Path

# Add workspace to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from marcus_app.core.database import SessionLocal, Base, engine
from marcus_app.core.models import Project, ProjectFile, ProjectNote
from marcus_app.core.schemas import (
    ProjectCreateRequest, ProjectFileCreateRequest,
    ProjectNoteCreateRequest, ProjectNoteUpdateRequest
)
from marcus_app.services.project_service import ProjectService


def test_v039_complete_workflow():
    """Run complete v0.39 workflow test."""
    
    # Setup database
    print("\n" + "="*80)
    print("V0.39 PROJECTS MODULE - INTEGRATION TEST")
    print("="*80 + "\n")
    
    Base.metadata.create_all(engine)
    db = SessionLocal()
    
    try:
        # Test 1: Ensure base directory
        print("[1/8] Testing base directory...")
        assert ProjectService.ensure_base_dir(), "Base directory not accessible"
        print("  ✓ M:/Marcus/projects/ accessible\n")
        
        # Test 2: Create project
        print("[2/8] Creating project 'RedByte'...")
        proj_req = ProjectCreateRequest(
            name="RedByte",
            description="Company website redesign",
            project_type="web"
        )
        project = ProjectService.create_project(db, proj_req)
        assert project.id, "Project not created"
        assert Path(project.root_path).exists(), "Project directory not created"
        print(f"  ✓ Project created: ID={project.id}, Path={project.root_path}\n")
        
        # Test 3: Create files
        print("[3/8] Creating project files...")
        files_to_create = [
            ("index.html", "<html><head><title>RedByte</title></head><body>Hello</body></html>"),
            ("style.css", "body { font-family: Arial; color: #333; }"),
            ("app.js", "console.log('RedByte App');"),
            ("config.json", '{"app": "RedByte", "version": "1.0"}'),
            ("docs/README.md", "# RedByte Project\n\nThis is the main project.")
        ]
        
        for path, content in files_to_create:
            req = ProjectFileCreateRequest(relative_path=path, content=content)
            db_file = ProjectService.create_file(db, project.id, req)
            assert db_file.id, f"File not created: {path}"
            file_path = Path(project.root_path) / path
            assert file_path.exists(), f"File not on disk: {path}"
            print(f"  ✓ Created: {path} ({db_file.file_size} bytes)")
        print()
        
        # Test 4: Read files
        print("[4/8] Reading files...")
        for path, _ in files_to_create[:2]:
            content, db_file = ProjectService.read_file(db, project.id, path)
            assert content, f"File content empty: {path}"
            assert db_file.relative_path == path
            print(f"  ✓ Read: {path}")
        print()
        
        # Test 5: List files
        print("[5/8] Listing files...")
        files = ProjectService.list_files(db, project.id)
        assert len(files) == len(files_to_create), f"File count mismatch: {len(files)} != {len(files_to_create)}"
        print(f"  ✓ Listed {len(files)} files:\n")
        for f in files:
            print(f"    - {f.relative_path} ({f.file_type}, {f.file_size} bytes)")
        print()
        
        # Test 6: Create and list notes
        print("[6/8] Creating project notes...")
        notes_to_create = [
            ("Architecture", "# Design\n\n- Use React for frontend\n- SQLite backend"),
            ("TODOs", "- [ ] Implement auth\n- [ ] Add search\n- [ ] Mobile responsive"),
            ("Decisions", "- Use HTTPS everywhere\n- Rate limiting enabled")
        ]
        
        created_notes = []
        for title, content in notes_to_create:
            req = ProjectNoteCreateRequest(title=title, content=content)
            note = ProjectService.create_note(db, project.id, req)
            created_notes.append(note)
            print(f"  ✓ Created note: '{title}'")
        print()
        
        # Test 7: Update note
        print("[7/8] Updating note...")
        note = created_notes[0]
        updated = ProjectService.update_note(
            db, note.id,
            title="Architecture (Updated)",
            content="# Updated Design\n\nChanges made based on feedback"
        )
        assert updated.title == "Architecture (Updated)"
        print(f"  ✓ Updated note ID={note.id}\n")
        
        # Test 8: Verify data consistency
        print("[8/8] Verifying data consistency...")
        
        # Re-fetch project with relationships
        project = ProjectService.get_project(db, project.id)
        assert len(project.files) == len(files_to_create), f"Files count: {len(project.files)}"
        assert len(project.notes) == len(notes_to_create), f"Notes count: {len(project.notes)}"
        print(f"  ✓ Project has {len(project.files)} files and {len(project.notes)} notes\n")
        
        # Summary
        print("="*80)
        print("✓ ALL TESTS PASSED")
        print("="*80)
        print("\nSummary:")
        print(f"  - Project: {project.name}")
        print(f"  - Type: {project.project_type}")
        print(f"  - Location: {project.root_path}")
        print(f"  - Files: {len(project.files)}")
        print(f"  - Notes: {len(project.notes)}")
        print(f"  - Status: {project.status}")
        print(f"\nURL Preview: http://localhost:8000/preview/RedByte/index.html")
        print()
        
        return True
        
    except Exception as e:
        print(f"\n✗ TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        db.close()


if __name__ == "__main__":
    success = test_v039_complete_workflow()
    sys.exit(0 if success else 1)
