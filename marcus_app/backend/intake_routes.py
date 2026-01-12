"""
Marcus Intake Routes (DEPRECATED as of v0.51)

This module contains legacy Flask blueprint routes that are no longer used.
The functionality has been migrated to the FastAPI application in api.py.

DEPRECATED ENDPOINTS (not in use):
- POST /api/intake/classify
- POST /api/intake/confirm
- GET /api/intake/runbook
- GET /api/diagnostics
- GET /api/diagnostics/storage
- GET /api/diagnostics/database
- GET /api/diagnostics/audit-log
- POST /api/diagnostics/export-debug

ACTIVE ENDPOINTS (see api.py):
- POST /api/chat
- POST /api/chat/upload
- GET /api/classes
- GET /api/assignments
- GET /api/inbox
- POST /api/search
... and others

This file is kept for historical reference only and is NOT imported
by the active application. It can be safely deleted after backup.

History:
- v0.36-0.50: Used Flask blueprints for intake workflow
- v0.51+: Migrated to FastAPI with heuristic-based chat interface

For details, see V051_CHAT_REDESIGN_COMPLETE.md
"""

from typing import Optional, Any

# Stub to prevent import errors if referenced elsewhere
intake_service: Optional[Any] = None
ollama_adapter: Optional[Any] = None
runbook_service: Optional[Any] = None
diagnostics_service: Optional[Any] = None
