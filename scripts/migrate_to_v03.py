"""
Migration script: v0.2 -> v0.3
Adds new columns to text_chunks table for semantic search.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from marcus_app.core.database import SessionLocal
from marcus_app.core.models import TextChunk, Artifact, Assignment


def migrate_database():
    """Add v0.3 columns to text_chunks table."""

    db_path = Path(__file__).parent.parent / "storage" / "marcus.db"

    print("="*70)
    print("Marcus v0.3 Database Migration")
    print("="*70)
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check current schema
    cursor.execute("PRAGMA table_info(text_chunks)")
    columns = {row[1]: row for row in cursor.fetchall()}

    print(f"\nCurrent columns: {list(columns.keys())}")

    # Add new columns if they don't exist
    new_columns = [
        ("artifact_id", "INTEGER"),
        ("assignment_id", "INTEGER"),
        ("class_id", "INTEGER"),
        ("char_start", "INTEGER"),
        ("char_end", "INTEGER"),
        ("embedding_model", "VARCHAR(100)")
    ]

    added = []
    for col_name, col_type in new_columns:
        if col_name not in columns:
            print(f"\n[ADDING] {col_name} ({col_type})")
            cursor.execute(f"ALTER TABLE text_chunks ADD COLUMN {col_name} {col_type}")
            added.append(col_name)
        else:
            print(f"[SKIP] {col_name} already exists")

    conn.commit()

    # Backfill denormalized foreign keys
    if added:
        print("\n" + "="*70)
        print("Backfilling denormalized foreign keys...")
        print("="*70)

        db = SessionLocal()

        chunks = db.query(TextChunk).all()
        print(f"\nFound {len(chunks)} chunks to backfill")

        for chunk in chunks:
            # Get artifact
            if chunk.extracted_text and chunk.extracted_text.artifact:
                artifact = chunk.extracted_text.artifact
                chunk.artifact_id = artifact.id
                chunk.assignment_id = artifact.assignment_id

                # Get class_id through assignment
                if artifact.assignment_id:
                    assignment = db.query(Assignment).filter(
                        Assignment.id == artifact.assignment_id
                    ).first()
                    if assignment:
                        chunk.class_id = assignment.class_id

        db.commit()
        db.close()

        print("[OK] Backfill complete")

    conn.close()

    print("\n" + "="*70)
    print("[OK] Migration to v0.3 complete!")
    print("="*70)
    print("\nNew schema supports:")
    print("- Fast class/assignment filtering")
    print("- Character position tracking")
    print("- Embedding model metadata")
    print("\nYou can now run: python scripts/load_test_data.py")


if __name__ == "__main__":
    migrate_database()
