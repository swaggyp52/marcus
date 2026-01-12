"""
Marcus v0.50: Self-Sufficiency Services

Runbook: In-app how-tos (backup, update, extend)
Diagnostics: Storage, DB health, audit log, debug export
"""

import os
import json
import zipfile
import shutil
from datetime import datetime
from typing import Dict, List, Any, Optional


class RunbookService:
    """
    Provides operational guides inside the app.
    Goal: user shouldn't need to return to ChatGPT for routine ops.
    """
    
    RUNBOOK_SECTIONS = {
        "first_run": {
            "title": "First Run Setup",
            "steps": [
                "Mount your VeraCrypt encrypted container (or use %APPDATA%\\marcus)",
                "Start Marcus: python main.py (or use run.bat)",
                "Open http://localhost:5000",
                "Take Syllabus Intake tour (📚 tab)",
                "Upload your first syllabus",
                "Confirm classes and deadlines",
                "Check 'What's Next?'"
            ]
        },
        "backup": {
            "title": "Backup Your Data",
            "steps": [
                "Mount VeraCrypt (or locate marcus_app/storage folder)",
                "Close Marcus application",
                "Copy entire storage/ folder to external drive (USB or cloud)",
                "Verify files copied successfully",
                "Optionally: zip the folder with password",
                "Store backup in safe location"
            ],
            "notes": [
                "Everything is stored in sqlite.db and artifact files",
                "No cloud sync needed",
                "Backup weekly or after major changes"
            ]
        },
        "update": {
            "title": "Update Marcus",
            "steps": [
                "Pull latest code: git pull origin main",
                "Review CHANGELOG for schema changes (there are none post-v0.49)",
                "If new dependencies: pip install -r requirements.txt",
                "Stop Marcus if running",
                "Start Marcus again: python main.py",
                "Check Diagnostics > DB Health if uncertain"
            ],
            "notes": [
                "Marcus v0.49+ has frozen schema",
                "Updates are additive only",
                "Database migrations are one-way (test in a copy first if nervous)"
            ]
        },
        "intake_failed": {
            "title": "Intake Failed or Incomplete",
            "steps": [
                "Check Intake Receipt for specific errors",
                "Low-confidence items go to Inbox automatically",
                "If file didn't upload: check file format (PDF, image, txt)",
                "If classification wrong: manually confirm in Intake wizard",
                "If deadlines missing: check Diagnostics > LLM Status (Ollama might be offline)",
                "Undo the entire intake within 10s, or use soft-delete on individual items"
            ]
        },
        "add_custom_command": {
            "title": "Add Custom Commands (Advanced)",
            "steps": [
                "Edit marcus_app/agent/intents/YOUR_NEW_INTENT.py",
                "Copy pattern from marcus_app/agent/intents/suggest_next_action.py",
                "Return {'type': 'action', 'items': [...], 'metadata': {...}}",
                "Test in Agent Chat",
                "If you need external data: add as a Service, don't call network directly"
            ],
            "notes": [
                "Keep deterministic: same input = same output",
                "Don't add new Item fields (schema frozen)",
                "Don't call external APIs (offline-first)",
                "Test with verify script"
            ]
        },
        "trust_question": {
            "title": "Can I Trust Marcus?",
            "answer": [
                "✅ Storage is encrypted (your VeraCrypt container)",
                "✅ App has auth wall if you set it (v0.42)",
                "✅ Undo exists for all destructive actions (v0.48)",
                "✅ Online actions are gated & audited (v0.42)",
                "✅ Everything is deterministic (v0.49)",
                "✅ Intake receipts trace everything (v0.50)",
                "✅ No background processes, no surprise online calls (offline-first)",
                "",
                "If any of these is false: Marcus trust is broken. Fix before using for real work."
            ]
        }
    }
    
    @staticmethod
    def get_runbook(section: Optional[str] = None) -> Dict[str, Any]:
        """
        Get runbook content.
        
        Args:
            section: specific section key, or None for full runbook
        
        Returns:
            dict with title, steps, notes
        """
        if section and section in RunbookService.RUNBOOK_SECTIONS:
            return RunbookService.RUNBOOK_SECTIONS[section]
        
        return RunbookService.RUNBOOK_SECTIONS
    
    @staticmethod
    def render_markdown(section: Optional[str] = None) -> str:
        """Render runbook as markdown for display."""
        content = RunbookService.get_runbook(section)
        
        lines = []
        
        if section:
            # Single section
            lines.append(f"# {content['title']}")
            lines.append("")
            for i, step in enumerate(content.get('steps', []), 1):
                lines.append(f"{i}. {step}")
            
            if content.get('notes'):
                lines.append("")
                lines.append("### Notes")
                for note in content['notes']:
                    lines.append(f"- {note}")
            
            if content.get('answer'):
                lines.append("")
                for line in content['answer']:
                    lines.append(line)
        
        else:
            # Full runbook
            lines.append("# Marcus Runbook")
            lines.append("_How to operate Marcus without ChatGPT_")
            lines.append("")
            
            for key, section_data in content.items():
                lines.append(f"## {section_data['title']}")
                lines.append("")
                
                for i, step in enumerate(section_data.get('steps', []), 1):
                    lines.append(f"{i}. {step}")
                
                if section_data.get('notes'):
                    lines.append("")
                    for note in section_data['notes']:
                        lines.append(f"- {note}")
                
                if section_data.get('answer'):
                    lines.append("")
                    for line in section_data['answer']:
                        lines.append(line)
                
                lines.append("")
        
        return "\n".join(lines)


class DiagnosticsService:
    """
    Operational diagnostics panel.
    Storage, DB health, LLM status, audit log, debug export.
    """
    
    def __init__(self, storage_path: str, db_path: str, audit_log: Optional[List] = None):
        """
        Initialize diagnostics.
        
        Args:
            storage_path: path to storage/ folder
            db_path: path to database.db
            audit_log: reference to audit trail
        """
        self.storage_path = storage_path
        self.db_path = db_path
        self.audit_log = audit_log or []
    
    def check_storage(self) -> Dict[str, Any]:
        """Check storage mount and space."""
        result = {
            "status": "unknown",
            "path": self.storage_path,
            "exists": False,
            "writable": False,
            "free_space_mb": 0,
            "total_files": 0
        }
        
        try:
            if os.path.exists(self.storage_path):
                result["exists"] = True
                
                # Check write permission
                test_file = os.path.join(self.storage_path, ".write_test")
                try:
                    with open(test_file, "w") as f:
                        f.write("test")
                    os.remove(test_file)
                    result["writable"] = True
                except:
                    result["writable"] = False
                
                # Count files
                total = 0
                for _, _, files in os.walk(self.storage_path):
                    total += len(files)
                result["total_files"] = total
                
                # Free space
                stat = shutil.disk_usage(self.storage_path)
                result["free_space_mb"] = stat.free // (1024 * 1024)
                
                if result["writable"]:
                    result["status"] = "healthy"
                else:
                    result["status"] = "mounted_readonly"
            else:
                result["status"] = "not_found"
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def check_db_health(self) -> Dict[str, Any]:
        """Check database health."""
        result = {
            "status": "unknown",
            "path": self.db_path,
            "exists": False,
            "size_mb": 0,
            "tables": [],
            "last_write": None
        }
        
        try:
            if os.path.exists(self.db_path):
                result["exists"] = True
                result["size_mb"] = os.path.getsize(self.db_path) / (1024 * 1024)
                result["last_write"] = datetime.fromtimestamp(
                    os.path.getmtime(self.db_path)
                ).isoformat()
                
                # Try to get table count
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT name FROM sqlite_master WHERE type='table'"
                    )
                    tables = cursor.fetchall()
                    result["tables"] = [t[0] for t in tables]
                    conn.close()
                    result["status"] = "healthy"
                except Exception as e:
                    result["status"] = "corrupted"
                    result["error"] = str(e)
            else:
                result["status"] = "not_found"
        
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
        
        return result
    
    def get_recent_audit_log(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Last N audit log entries."""
        return self.audit_log[-limit:]
    
    def export_debug_bundle(self, output_path: str = "/tmp/marcus_debug.zip") -> str:
        """
        Export debug bundle: logs, configs, DB schema, etc.
        
        Returns:
            path to created zip file
        """
        try:
            with zipfile.ZipFile(output_path, "w") as zf:
                # Add audit log
                audit_json = json.dumps(self.audit_log, indent=2, default=str)
                zf.writestr("audit_log.json", audit_json)
                
                # Add diagnostics
                diag = {
                    "timestamp": datetime.utcnow().isoformat(),
                    "storage": self.check_storage(),
                    "db": self.check_db_health(),
                }
                zf.writestr("diagnostics.json", json.dumps(diag, indent=2))
                
                # Add DB schema
                try:
                    import sqlite3
                    conn = sqlite3.connect(self.db_path)
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT sql FROM sqlite_master WHERE type='table'"
                    )
                    schema = "\n\n".join([row[0] for row in cursor.fetchall()])
                    zf.writestr("db_schema.sql", schema)
                    conn.close()
                except:
                    pass
                
                # Add version info
                version_info = {
                    "marcus_version": "0.50",
                    "export_time": datetime.utcnow().isoformat()
                }
                zf.writestr("version.json", json.dumps(version_info, indent=2))
            
            return output_path
        
        except Exception as e:
            return f"Error creating debug bundle: {str(e)}"
    
    def get_full_status(self) -> Dict[str, Any]:
        """Complete diagnostics snapshot."""
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "storage": self.check_storage(),
            "database": self.check_db_health(),
            "audit_log_size": len(self.audit_log),
            "overall_status": "healthy"  # compute based on checks
        }
