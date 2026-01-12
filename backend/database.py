"""Database initialization and connection management."""
from sqlmodel import SQLModel, create_engine, Session
from pathlib import Path
import os
import sys

# Determine database path
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    app_dir = Path(sys._MEIPASS)
    db_dir = Path(os.path.expanduser('~')) / 'Marcus'
    db_dir.mkdir(exist_ok=True)
    DATABASE_URL = f"sqlite:///{db_dir / 'marcus.db'}"
else:
    # Running as script
    DATABASE_URL = "sqlite:///marcus.db"

engine = create_engine(DATABASE_URL, echo=False)


def init_db():
    """Initialize the database and create all tables."""
    SQLModel.metadata.create_all(engine)


def get_session():
    """Get a database session."""
    with Session(engine) as session:
        yield session
