"""
V0.39 Projects Module - Integration Tests

Tests project creation, file operations, notes, and API endpoints.
"""

import pytest
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Setup path for imports
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from marcus_app.core.database import SessionLocal, Base, engine
from marcus_app.core.models import Project, ProjectFile, ProjectNote
from marcus_app.core.schemas import (
    ProjectCreateRequest, ProjectFileCreateRequest, 
    ProjectNoteCreateRequest, ProjectNoteUpdateRequest
)
from marcus_app.services.project_service import ProjectService


@pytest.fixture
def db_session():
    """Create a test database session."""
    Base.metadata.create_all(engine)
    session = SessionLocal()
    yield session
    session.close()
    # Clean up
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def cleanup_projects():
    """Cleanup project directories after tests."""
    yield
    # Cleanup would go here
    pass


class TestProjectService:
    """Test ProjectService functionality."""
    
    def test_ensure_base_dir(self):
        """Test that base directory is created."""
        assert ProjectService.ensure_base_dir() == True
        assert ProjectService.BASE_PROJECT_DIR.exists()
    
    def test_get_project_root(self):
        """Test getting project root path."""
        root = ProjectService.get_project_root("TestProject")
        assert "TestProject" in str(root)
        assert "Marcus" in str(root)
    
    def test_sanitize_project_name(self):
        """Test that invalid characters are sanitized."""
        root = ProjectService.get_project_root("RedByte-2.0_Project")
        assert "RedByte-2" in str(root)
    
    def test_create_project(self, db_session, cleanup_projects):
        """Test creating a new project."""
        request = ProjectCreateRequest(
            name="RedByte",
            description="A test web project",
            project_type="web"
        )
        
        project = ProjectService.create_project(db_session, request)
        
        assert project.id is not None
        assert project.name == "RedByte"
        assert project.description == "A test web project"
        assert project.project_type == "web"
        assert project.status == "active"
        assert Path(project.root_path).exists()
    
    def test_create_duplicate_project_fails(self, db_session, cleanup_projects):
        """Test that creating duplicate project names fails."""
        request = ProjectCreateRequest(name="Duplicate", project_type="web")
        
        ProjectService.create_project(db_session, request)
        
        with pytest.raises(ValueError, match="already exists"):
            ProjectService.create_project(db_session, request)
    
    def test_list_projects(self, db_session, cleanup_projects):
        """Test listing projects."""
        # Create several projects
        for i in range(3):
            request = ProjectCreateRequest(
                name=f"Project{i}",
                project_type="web"
            )
            ProjectService.create_project(db_session, request)
        
        projects = ProjectService.list_projects(db_session)
        assert len(projects) == 3
    
    def test_create_file(self, db_session, cleanup_projects):
        """Test creating a file in a project."""
        # Create project
        proj_req = ProjectCreateRequest(name="TestProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        # Create file
        file_req = ProjectFileCreateRequest(
            relative_path="index.html",
            content="<html><body>Hello</body></html>"
        )
        
        db_file = ProjectService.create_file(db_session, project.id, file_req)
        
        assert db_file.id is not None
        assert db_file.relative_path == "index.html"
        assert db_file.file_type == "html"
        assert db_file.file_size > 0
        
        # Verify file exists on disk
        file_path = Path(project.root_path) / "index.html"
        assert file_path.exists()
        assert file_path.read_text() == "<html><body>Hello</body></html>"
    
    def test_create_nested_file(self, db_session, cleanup_projects):
        """Test creating a file in nested directories."""
        proj_req = ProjectCreateRequest(name="NestedProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        file_req = ProjectFileCreateRequest(
            relative_path="css/styles.css",
            content="body { color: blue; }"
        )
        
        db_file = ProjectService.create_file(db_session, project.id, file_req)
        
        file_path = Path(project.root_path) / "css" / "styles.css"
        assert file_path.exists()
        assert "color: blue" in file_path.read_text()
    
    def test_read_file(self, db_session, cleanup_projects):
        """Test reading a file from a project."""
        proj_req = ProjectCreateRequest(name="ReadProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        # Create file
        content = '{"app": "Marcus"}'
        file_req = ProjectFileCreateRequest(
            relative_path="config.json",
            content=content
        )
        ProjectService.create_file(db_session, project.id, file_req)
        
        # Read it back
        read_content, db_file = ProjectService.read_file(db_session, project.id, "config.json")
        
        assert read_content == content
        assert db_file.file_type == "json"
    
    def test_list_files(self, db_session, cleanup_projects):
        """Test listing files in a project."""
        proj_req = ProjectCreateRequest(name="ListProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        # Create multiple files
        files_to_create = [
            ("index.html", "<html></html>"),
            ("style.css", "body {}"),
            ("app.js", "console.log('hi');")
        ]
        
        for path, content in files_to_create:
            req = ProjectFileCreateRequest(relative_path=path, content=content)
            ProjectService.create_file(db_session, project.id, req)
        
        files = ProjectService.list_files(db_session, project.id)
        assert len(files) == 3
        assert sorted([f.relative_path for f in files]) == sorted([p[0] for p in files_to_create])
    
    def test_delete_file(self, db_session, cleanup_projects):
        """Test deleting a file."""
        proj_req = ProjectCreateRequest(name="DelProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        file_req = ProjectFileCreateRequest(relative_path="temp.txt", content="temporary")
        ProjectService.create_file(db_session, project.id, file_req)
        
        # Verify file exists
        file_path = Path(project.root_path) / "temp.txt"
        assert file_path.exists()
        
        # Delete it
        success = ProjectService.delete_file(db_session, project.id, "temp.txt")
        
        assert success == True
        assert not file_path.exists()
    
    def test_create_note(self, db_session, cleanup_projects):
        """Test creating a project note."""
        proj_req = ProjectCreateRequest(name="NoteProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        note_req = ProjectNoteCreateRequest(
            title="Architecture Notes",
            content="# Design Decisions\n\nUse React for frontend"
        )
        
        note = ProjectService.create_note(db_session, project.id, note_req)
        
        assert note.id is not None
        assert note.project_id == project.id
        assert note.title == "Architecture Notes"
        assert "React" in note.content
    
    def test_list_notes(self, db_session, cleanup_projects):
        """Test listing project notes."""
        proj_req = ProjectCreateRequest(name="NoteListProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        # Create multiple notes
        for i in range(3):
            note_req = ProjectNoteCreateRequest(
                title=f"Note {i}",
                content=f"Content {i}"
            )
            ProjectService.create_note(db_session, project.id, note_req)
        
        notes = ProjectService.list_notes(db_session, project.id)
        assert len(notes) == 3
    
    def test_update_note(self, db_session, cleanup_projects):
        """Test updating a note."""
        proj_req = ProjectCreateRequest(name="UpdateProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        note_req = ProjectNoteCreateRequest(
            title="Original",
            content="Original content"
        )
        note = ProjectService.create_note(db_session, project.id, note_req)
        
        updated = ProjectService.update_note(
            db_session,
            note.id,
            title="Updated",
            content="Updated content"
        )
        
        assert updated.title == "Updated"
        assert updated.content == "Updated content"
    
    def test_delete_project(self, db_session, cleanup_projects):
        """Test deleting a project."""
        proj_req = ProjectCreateRequest(name="DeleteMeProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        project_root = Path(project.root_path)
        assert project_root.exists()
        
        # Delete project
        success = ProjectService.delete_project(db_session, project.id)
        
        assert success == True
        assert not project_root.exists()
    
    def test_directory_traversal_prevented(self, db_session, cleanup_projects):
        """Test that directory traversal attacks are prevented."""
        proj_req = ProjectCreateRequest(name="SecurityProj", project_type="web")
        project = ProjectService.create_project(db_session, proj_req)
        
        # Try to create a file outside project directory
        bad_req = ProjectFileCreateRequest(
            relative_path="../../../etc/passwd",
            content="dangerous"
        )
        
        with pytest.raises(ValueError):
            ProjectService.create_file(db_session, project.id, bad_req)


if __name__ == "__main__":
    # Run basic sanity checks
    print("Running v0.39 Projects Module Tests...")
    
    # Ensure base directory
    if ProjectService.ensure_base_dir():
        print("✓ Base directory accessible")
    else:
        print("✗ Base directory NOT accessible - check M:/Marcus/projects")
        exit(1)
    
    # Test project root path
    root = ProjectService.get_project_root("TestProject")
    print(f"✓ Project root: {root}")
    
    print("\nAll sanity checks passed!")
    print("Run: pytest tests/test_v039_projects.py -v")
