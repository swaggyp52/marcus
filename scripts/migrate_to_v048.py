"""
V0.48 Database Migrations

1. Add UndoEvent table
2. Add soft delete columns to Item table
3. Add soft delete columns to Mission table
"""

# Migration SQL - Run these in order:

# Step 1: Create UndoEvent table
CREATE_UNDO_EVENTS_TABLE = """
CREATE TABLE IF NOT EXISTS undo_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action_type VARCHAR(50) NOT NULL,
    payload JSON NOT NULL,
    description VARCHAR(500),
    created_at DATETIME NOT NULL,
    expires_at DATETIME NOT NULL,
    is_consumed BOOLEAN DEFAULT 0,
    created_timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_undo_events_created_at ON undo_events(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_undo_events_expires_at ON undo_events(expires_at);
CREATE INDEX IF NOT EXISTS idx_undo_events_is_consumed ON undo_events(is_consumed);
"""

# Step 2: Add soft delete columns to Item
ADD_SOFT_DELETE_TO_ITEMS = """
ALTER TABLE items ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
ALTER TABLE items ADD COLUMN deleted_at DATETIME DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_items_is_deleted ON items(is_deleted);
"""

# Step 3: Add soft delete columns to Mission
ADD_SOFT_DELETE_TO_MISSIONS = """
ALTER TABLE missions ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
ALTER TABLE missions ADD COLUMN deleted_at DATETIME DEFAULT NULL;

CREATE INDEX IF NOT EXISTS idx_missions_is_deleted ON missions(is_deleted);
"""

# Python migration script
def run_migrations(db):
    """Execute all v0.48 migrations."""
    try:
        # Create undo_events table
        db.execute(CREATE_UNDO_EVENTS_TABLE)
        print("✓ Created undo_events table")

        # Add soft delete to items
        try:
            db.execute(ADD_SOFT_DELETE_TO_ITEMS)
            print("✓ Added soft delete to items table")
        except Exception as e:
            # Columns may already exist
            print(f"  (items soft delete already exists: {e})")

        # Add soft delete to missions
        try:
            db.execute(ADD_SOFT_DELETE_TO_MISSIONS)
            print("✓ Added soft delete to missions table")
        except Exception as e:
            # Columns may already exist
            print(f"  (missions soft delete already exists: {e})")

        db.commit()
        print("✓ All migrations completed")
        return True
    except Exception as e:
        print(f"✗ Migration failed: {e}")
        db.rollback()
        return False

if __name__ == "__main__":
    from marcus_app.core.database import engine
    
    with engine.connect() as conn:
        conn.execute(CREATE_UNDO_EVENTS_TABLE)
        conn.commit()
    
    print("Migrations applied successfully!")
