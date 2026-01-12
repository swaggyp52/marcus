"""
Migration script: v0.36 -> v0.37
Adds FTS5 virtual table for better search and search_aliases table.
"""

import sqlite3
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from marcus_app.core.database import SessionLocal
from marcus_app.core.models import TextChunk


def migrate_database():
    """Add FTS5 virtual table and search_aliases table."""

    db_path = Path(__file__).parent.parent / "storage" / "marcus.db"

    # Check if using encrypted storage
    import os
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / "marcus.env")

    encrypted_db = os.getenv("MARCUS_DB_PATH")
    if encrypted_db:
        db_path = Path(encrypted_db)

    print("=" * 70)
    print("Marcus v0.37 Database Migration")
    print("=" * 70)
    print(f"\nDatabase: {db_path}")

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Check if FTS5 is available
    cursor.execute("PRAGMA compile_options")
    compile_options = [row[0] for row in cursor.fetchall()]
    fts5_enabled = any('FTS5' in opt for opt in compile_options)

    print(f"\nFTS5 support: {'[OK] Enabled' if fts5_enabled else '[NO] Disabled'}")

    if not fts5_enabled:
        print("\n[WARNING] FTS5 not available in this SQLite build.")
        print("Search quality upgrade will use enhanced LIKE search instead.")
        conn.close()
        # Continue anyway - we'll use enhanced LIKE as fallback
    else:
        # Create FTS5 virtual table
        print("\n[CREATING] FTS5 virtual table...")

        # Check if already exists
        cursor.execute("""
            SELECT name FROM sqlite_master
            WHERE type='table' AND name='text_chunks_fts'
        """)

        if cursor.fetchone():
            print("[SKIP] text_chunks_fts already exists")
        else:
            cursor.execute("""
                CREATE VIRTUAL TABLE text_chunks_fts USING fts5(
                    content,
                    section_title,
                    content='text_chunks',
                    content_rowid='id',
                    tokenize='porter unicode61'
                )
            """)

            # Populate FTS5 table from existing chunks
            cursor.execute("""
                INSERT INTO text_chunks_fts(rowid, content, section_title)
                SELECT id, content, section_title FROM text_chunks
            """)

            conn.commit()
            print("[OK] Created and populated text_chunks_fts")

    # Create search_aliases table
    print("\n[CREATING] search_aliases table...")

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS search_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            term TEXT NOT NULL,
            canonical_term TEXT NOT NULL,
            category TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alias_term ON search_aliases(term)")

    conn.commit()
    print("[OK] Created search_aliases table")

    # Populate with common academic aliases
    print("\n[POPULATING] Common academic aliases...")

    aliases = [
        # Abbreviations
        ("FSM", "finite state machine", "abbreviation"),
        ("MESI", "modified exclusive shared invalid", "abbreviation"),
        ("MOESI", "modified owned exclusive shared invalid", "abbreviation"),
        ("TLB", "translation lookaside buffer", "abbreviation"),
        ("MMU", "memory management unit", "abbreviation"),
        ("ALU", "arithmetic logic unit", "abbreviation"),
        ("CPU", "central processing unit", "abbreviation"),
        ("GPU", "graphics processing unit", "abbreviation"),
        ("RAM", "random access memory", "abbreviation"),
        ("ROM", "read only memory", "abbreviation"),

        # Hyphenation variations
        ("side channel", "side-channel", "variation"),
        ("sidechannel", "side-channel", "variation"),
        ("setup time", "setup-time", "variation"),
        ("hold time", "hold-time", "variation"),
        ("cache coherence", "cache-coherence", "variation"),

        # Common synonyms
        ("finite state machine", "FSM", "synonym"),
        ("rotational motion", "rotational dynamics", "synonym"),
        ("angular velocity", "rotational velocity", "synonym"),
        ("moment of inertia", "rotational inertia", "synonym"),

        # Security terms
        ("threat modeling", "threat model", "variation"),
        ("threat modelling", "threat model", "variation"),
        ("STRIDE", "spoofing tampering repudiation information disclosure denial of service elevation of privilege", "abbreviation"),
    ]

    # Check what already exists
    cursor.execute("SELECT COUNT(*) FROM search_aliases")
    existing_count = cursor.fetchone()[0]

    if existing_count == 0:
        cursor.executemany("""
            INSERT INTO search_aliases (term, canonical_term, category)
            VALUES (?, ?, ?)
        """, aliases)
        conn.commit()
        print(f"[OK] Added {len(aliases)} aliases")
    else:
        print(f"[SKIP] {existing_count} aliases already exist")

    conn.close()

    print("\n" + "=" * 70)
    print("[OK] Migration to v0.37 complete!")
    print("=" * 70)
    print("\nNew features:")
    print("- FTS5 full-text search (BM25 ranking)")
    print("- Search aliases (FSM, side-channel, etc.)")
    print("- Query normalization")
    print("- Better relevance scoring")
    print("\nTest search with:")
    print("  python scripts/load_test_data.py")


if __name__ == "__main__":
    migrate_database()
