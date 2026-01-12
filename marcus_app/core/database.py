"""
Database initialization and session management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from pathlib import Path
import os
import sys
from .models import Base

# Load environment configuration
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent.parent / "marcus.env")

# Check if encrypted storage is mounted
# REQUIRED: M:\Marcus\ must exist and be writable (or use dev storage for testing)
REQUIRED_MOUNT = Path("M:\\Marcus")

# Find dev storage - when running as bundled EXE, look in current directory or project path
_dev_storage = None
_search_paths = [
    Path(__file__).parent.parent.parent / "storage" / "packaging_temp",  # From source
    Path.cwd() / "storage" / "packaging_temp",  # Where EXE is run from
    Path("C:\\Users\\conno\\marcus") / "storage" / "packaging_temp",  # Project fallback
]
for _p in _search_paths:
    if _p.exists():
        _dev_storage = _p
        break

# Use whichever exists (dev for testing, production M: for real use)
if REQUIRED_MOUNT.exists():
    ACTIVE_MOUNT = REQUIRED_MOUNT
elif _dev_storage:
    ACTIVE_MOUNT = _dev_storage
else:
    print("=" * 70)
    print("[SECURITY] Marcus encrypted storage NOT MOUNTED")
    print("=" * 70)
    print(f"Expected encrypted drive at: {REQUIRED_MOUNT}")
    print(f"Or dev storage at: {DEV_MOUNT}")
    print("")
    print("To start Marcus:")
    print("1. For production: Mount VeraCrypt container to M:\\Marcus")
    print("2. For development: Create test storage at storage/packaging_temp")
    print("3. Verify M:\\Marcus\\ or storage/packaging_temp exists and is accessible")
    print("4. Restart Marcus")
    print("=" * 70)
    sys.exit(1)

# Verify mount is writable (catches permission issues)
try:
    test_file = ACTIVE_MOUNT / f".marcus_write_test_{id(Path)}.tmp"
    test_file.write_text("test")
    test_file.unlink()
except Exception as e:
    print("=" * 70)
    print("[SECURITY] Marcus encrypted storage NOT WRITABLE")
    print("=" * 70)
    print(f"Path exists: {ACTIVE_MOUNT}")
    print(f"But not writable: {e}")
    print("")
    print("To fix:")
    print("1. Check that the VeraCrypt container is fully mounted")
    print("2. Verify file permissions allow write access")
    print("3. Restart Marcus")
    print("=" * 70)
    sys.exit(1)

# Set paths based on active mount (M:\Marcus or storage/packaging_temp)
MARCUS_DATA_ROOT = str(ACTIVE_MOUNT)

# Database file location (on encrypted drive or dev storage)
# Always build from ACTIVE_MOUNT, ignore env var to avoid M: path issues
DB_PATH = Path(ACTIVE_MOUNT / "marcus.db")
DB_PATH.parent.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False}, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """Initialize database and create all tables."""
    Base.metadata.create_all(bind=engine)
    print(f"Database initialized at: {DB_PATH}")


def get_db() -> Session:
    """Dependency for getting database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
