"""
Marcus - Main entry point
Local-first academic operating environment
"""

import uvicorn
from pathlib import Path

if __name__ == "__main__":
    print("=" * 70)
    print("MARCUS - Local-First Academic Operating Environment")
    print("=" * 70)
    print()
    print("Starting Marcus server...")
    print()
    print("Once started, open your browser to: http://localhost:8000")
    print()
    print("Press Ctrl+C to stop the server")
    print("=" * 70)
    print()

    uvicorn.run(
        "marcus_app.backend.api:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
        log_level="info"
    )
