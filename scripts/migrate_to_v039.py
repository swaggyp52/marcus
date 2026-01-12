"""
Database migration for v0.39 - Projects Module.

Adds three new tables:
- projects: Main project metadata
- project_files: File metadata within projects
- project_notes: Markdown notes for projects

This migration creates the necessary tables and relationships.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os
from pathlib import Path

# Import existing setup
BASE_PATH = Path(__file__).parent.parent
DB_PATH = BASE_PATH / "storage" / "marcus.db"


def run_v039_migration():
    """
    Run v0.39 migration: Create projects tables.
    
    This is idempotent - it will not fail if tables already exist.
    """
    from marcus_app.core.database import engine
    from marcus_app.core.models import Project, ProjectFile, ProjectNote, Base
    
    print("[v0.39 Migration] Creating projects tables...")
    
    try:
        # Create tables (existing tables are ignored)
        Base.metadata.create_all(engine)
        print("[v0.39 Migration] ✓ Tables created successfully")
        
        # Create project storage directory
        project_dir = Path("M:/Marcus/projects")
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f"[v0.39 Migration] ✓ Project directory ready: {project_dir}")
        
    except Exception as e:
        print(f"[v0.39 Migration] ✗ Error: {e}")
        raise


if __name__ == "__main__":
    run_v039_migration()
