-- Marcus v0.47a: Universal Items Table
-- Migration to add Items table for unified capture/routing

CREATE TABLE IF NOT EXISTS items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,

    -- Core fields
    item_type TEXT NOT NULL,  -- note|task|document|event|artifact_ref|mission_ref
    title TEXT NOT NULL,
    content_md TEXT,
    content_json TEXT,  -- flexible storage for metadata

    -- Routing/classification
    status TEXT DEFAULT 'inbox',  -- inbox|active|done|archived|snoozed
    context_kind TEXT,  -- class|project|personal|none
    context_id INTEGER,  -- class_id or project_id if applicable
    confidence REAL,  -- 0.0-1.0 classification confidence
    suggested_route_json TEXT,  -- what auto-classifier suggested

    -- Organization
    tags_json TEXT,  -- JSON array of tags
    links_json TEXT,  -- references to artifact_ids, mission_ids, etc.
    pinned INTEGER DEFAULT 0,

    -- Scheduling (for tasks/events)
    due_at DATETIME,
    completed_at DATETIME,
    snooze_until DATETIME,

    -- Timestamps
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    filed_at DATETIME  -- when moved from inbox to context
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_items_status ON items(status);
CREATE INDEX IF NOT EXISTS idx_items_context ON items(context_kind, context_id);
CREATE INDEX IF NOT EXISTS idx_items_due_at ON items(due_at);
CREATE INDEX IF NOT EXISTS idx_items_created_at ON items(created_at DESC);

-- Full-text search index for title and content
CREATE VIRTUAL TABLE IF NOT EXISTS items_fts USING fts5(
    title,
    content_md,
    content='items',
    content_rowid='id'
);

-- Triggers to keep FTS index updated
CREATE TRIGGER IF NOT EXISTS items_ai AFTER INSERT ON items BEGIN
    INSERT INTO items_fts(rowid, title, content_md)
    VALUES (new.id, new.title, new.content_md);
END;

CREATE TRIGGER IF NOT EXISTS items_ad AFTER DELETE ON items BEGIN
    DELETE FROM items_fts WHERE rowid = old.id;
END;

CREATE TRIGGER IF NOT EXISTS items_au AFTER UPDATE ON items BEGIN
    DELETE FROM items_fts WHERE rowid = old.id;
    INSERT INTO items_fts(rowid, title, content_md)
    VALUES (new.id, new.title, new.content_md);
END;

-- Update timestamp trigger
CREATE TRIGGER IF NOT EXISTS items_update_timestamp
AFTER UPDATE ON items
FOR EACH ROW
BEGIN
    UPDATE items SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;
