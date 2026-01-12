"""
Project management service for v0.39 local development workspace.

Manages:
- Project lifecycle (create, read, update, delete)
- File I/O operations (read, write, delete files in project directory)
- Project notes (create, update, delete)
- Directory structure management
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict, Tuple

from sqlalchemy.orm import Session
from sqlalchemy import desc

from marcus_app.core.models import Project, ProjectFile, ProjectNote, ProjectType
from marcus_app.core.schemas import (
    ProjectCreateRequest, ProjectResponse, 
    ProjectFileCreateRequest, ProjectFileResponse,
    ProjectNoteCreateRequest, ProjectNoteResponse
)


class ProjectService:
    """Service for managing projects and their files."""
    
    BASE_PROJECT_DIR = Path("M:/Marcus/projects")
    
    @staticmethod
    def ensure_base_dir():
        """Ensure base projects directory exists and is accessible."""
        try:
            ProjectService.BASE_PROJECT_DIR.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            print(f"ERROR: Cannot access project base directory: {e}")
            return False
    
    @staticmethod
    def get_project_root(project_name: str) -> Path:
        """Get the root directory path for a project."""
        # Sanitize project name to prevent directory traversal
        if ".." in project_name or "/" in project_name or "\\" in project_name:
            raise ValueError("Invalid project name - contains path separators")
        
        safe_name = "".join(c for c in project_name if c.isalnum() or c in "-_")
        if not safe_name:
            raise ValueError("Invalid project name")
        return ProjectService.BASE_PROJECT_DIR / safe_name
    
    @staticmethod
    def create_project(db: Session, request: ProjectCreateRequest) -> Project:
        """
        Create a new project.
        
        Creates directory structure in M:/Marcus/projects/
        """
        # Check if project name already exists in database
        existing = db.query(Project).filter(Project.name == request.name).first()
        if existing:
            raise ValueError(f"Project '{request.name}' already exists")
        
        # Get project root path
        project_root = ProjectService.get_project_root(request.name)
        
        # Create directory
        try:
            project_root.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            raise ValueError(f"Cannot create project directory: {e}")
        
        # Create database entry
        project = Project(
            name=request.name,
            description=request.description,
            project_type=request.project_type,
            root_path=str(project_root),
            status="active"
        )
        
        db.add(project)
        db.commit()
        db.refresh(project)
        
        return project
    
    @staticmethod
    def get_project(db: Session, project_id: int) -> Optional[Project]:
        """Get project by ID."""
        return db.query(Project).filter(Project.id == project_id).first()
    
    @staticmethod
    def get_project_by_name(db: Session, project_name: str) -> Optional[Project]:
        """Get project by name."""
        return db.query(Project).filter(Project.name == project_name).first()
    
    @staticmethod
    def list_projects(db: Session) -> List[Project]:
        """List all active projects."""
        return db.query(Project)\
            .filter(Project.status == "active")\
            .order_by(desc(Project.created_at))\
            .all()
    
    @staticmethod
    def delete_project(db: Session, project_id: int) -> bool:
        """
        Delete a project and all its files.
        
        Removes directory from disk and database entry.
        """
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        
        # Remove directory from disk
        try:
            project_root = Path(project.root_path)
            if project_root.exists():
                shutil.rmtree(project_root)
        except Exception as e:
            print(f"Warning: Could not delete project directory: {e}")
        
        # Delete from database (cascade will handle files and notes)
        db.delete(project)
        db.commit()
        
        return True
    
    @staticmethod
    def create_file(
        db: Session, 
        project_id: int, 
        request: ProjectFileCreateRequest
    ) -> ProjectFile:
        """
        Create or update a file in a project.
        
        - Writes content to disk
        - Creates/updates database entry
        - Creates subdirectories as needed
        """
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Validate relative path (prevent directory traversal)
        relative_path = request.relative_path.strip()
        if ".." in relative_path or relative_path.startswith("/"):
            raise ValueError("Invalid file path")
        
        # Get full file path
        project_root = Path(project.root_path)
        file_path = project_root / relative_path
        
        # Ensure file is within project directory
        try:
            file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            raise ValueError("File path outside project directory")
        
        # Create subdirectories if needed
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write file content
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(request.content)
        except Exception as e:
            raise ValueError(f"Cannot write file: {e}")
        
        # Get file metadata
        file_size = file_path.stat().st_size
        file_ext = file_path.suffix.lstrip('.') or 'text'
        
        # Update or create database entry
        db_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.relative_path == relative_path
        ).first()
        
        if db_file:
            db_file.file_size = file_size
            db_file.file_type = file_ext
            db_file.modified_at = datetime.utcnow()
        else:
            db_file = ProjectFile(
                project_id=project_id,
                relative_path=relative_path,
                file_type=file_ext,
                file_size=file_size
            )
            db.add(db_file)
        
        db.commit()
        db.refresh(db_file)
        
        return db_file
    
    @staticmethod
    def read_file(
        db: Session,
        project_id: int,
        relative_path: str
    ) -> Tuple[str, ProjectFile]:
        """
        Read a file from a project.
        
        Returns: (content, ProjectFile metadata)
        """
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError("Project not found")
        
        # Validate relative path
        relative_path = relative_path.strip()
        if ".." in relative_path or relative_path.startswith("/"):
            raise ValueError("Invalid file path")
        
        # Get file path
        project_root = Path(project.root_path)
        file_path = project_root / relative_path
        
        # Ensure file is within project directory
        try:
            file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            raise ValueError("File path outside project directory")
        
        # Read file
        if not file_path.exists():
            raise ValueError("File not found")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Cannot read file: {e}")
        
        # Get database entry
        db_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.relative_path == relative_path
        ).first()
        
        if not db_file:
            # Create entry if it doesn't exist
            file_size = file_path.stat().st_size
            file_ext = file_path.suffix.lstrip('.') or 'text'
            db_file = ProjectFile(
                project_id=project_id,
                relative_path=relative_path,
                file_type=file_ext,
                file_size=file_size
            )
            db.add(db_file)
            db.commit()
            db.refresh(db_file)
        
        return content, db_file
    
    @staticmethod
    def list_files(db: Session, project_id: int) -> List[ProjectFile]:
        """List all files in a project."""
        return db.query(ProjectFile)\
            .filter(ProjectFile.project_id == project_id)\
            .order_by(ProjectFile.relative_path)\
            .all()
    
    @staticmethod
    def delete_file(db: Session, project_id: int, relative_path: str) -> bool:
        """
        Delete a file from a project.
        
        Removes from disk and database.
        """
        project = ProjectService.get_project(db, project_id)
        if not project:
            return False
        
        # Validate relative path
        relative_path = relative_path.strip()
        if ".." in relative_path or relative_path.startswith("/"):
            return False
        
        # Get file path
        project_root = Path(project.root_path)
        file_path = project_root / relative_path
        
        # Ensure file is within project directory
        try:
            file_path.resolve().relative_to(project_root.resolve())
        except ValueError:
            return False
        
        # Remove from disk
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            print(f"Warning: Could not delete file: {e}")
        
        # Remove from database
        db_file = db.query(ProjectFile).filter(
            ProjectFile.project_id == project_id,
            ProjectFile.relative_path == relative_path
        ).first()
        
        if db_file:
            db.delete(db_file)
            db.commit()
        
        return True
    
    @staticmethod
    def create_note(
        db: Session,
        project_id: int,
        request: ProjectNoteCreateRequest
    ) -> ProjectNote:
        """Create a new project note."""
        project = ProjectService.get_project(db, project_id)
        if not project:
            raise ValueError("Project not found")
        
        note = ProjectNote(
            project_id=project_id,
            title=request.title,
            content=request.content
        )
        
        db.add(note)
        db.commit()
        db.refresh(note)
        
        return note
    
    @staticmethod
    def get_note(db: Session, note_id: int) -> Optional[ProjectNote]:
        """Get a note by ID."""
        return db.query(ProjectNote).filter(ProjectNote.id == note_id).first()
    
    @staticmethod
    def list_notes(db: Session, project_id: int) -> List[ProjectNote]:
        """List all notes for a project."""
        return db.query(ProjectNote)\
            .filter(ProjectNote.project_id == project_id)\
            .order_by(desc(ProjectNote.created_at))\
            .all()
    
    @staticmethod
    def update_note(
        db: Session,
        note_id: int,
        title: Optional[str] = None,
        content: Optional[str] = None
    ) -> Optional[ProjectNote]:
        """Update a note."""
        note = ProjectService.get_note(db, note_id)
        if not note:
            return None
        
        if title is not None:
            note.title = title
        if content is not None:
            note.content = content
        
        note.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(note)
        
        return note
    
    @staticmethod
    def delete_note(db: Session, note_id: int) -> bool:
        """Delete a note."""
        note = ProjectService.get_note(db, note_id)
        if not note:
            return False
        
        db.delete(note)
        db.commit()
        
        return True
