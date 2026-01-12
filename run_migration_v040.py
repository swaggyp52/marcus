"""
V0.40: Database Migration Script
Creates all new tables for Dev Mode
"""

from marcus_app.core.models import Base
from marcus_app.core.database import engine

if __name__ == "__main__":
    print("=" * 70)
    print("V0.40 Database Migration")
    print("=" * 70)
    
    Base.metadata.create_all(engine)
    
    print("✓ Migration completed successfully")
    print("✓ New tables created:")
    print("  - dev_changesets")
    print("  - dev_changeset_files")
    print("  - github_tokens")
    print("  - life_graph_nodes")
    print("  - life_graph_edges")
    print("=" * 70)
