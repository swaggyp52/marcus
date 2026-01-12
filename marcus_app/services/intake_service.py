"""
Marcus v0.50: Syllabus Intake Service

Handles batch file uploads, classification, class/item creation, and receipts.
No new schema. Uses existing items/artifacts/classes/inbox.
Deterministic language. Undo-able operations.
"""

import json
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict


@dataclass
class IntakeReceipt:
    """
    Traceable receipt for every intake operation.
    Stored as a Note artifact, auditable and undoable.
    """
    receipt_id: str
    timestamp: str
    user_action: str  # "syllabus_intake", "document_batch", etc.
    files_processed: int
    classes_created: int
    classes_updated: int
    items_created: int
    artifacts_pinned: int
    errors: List[Dict[str, Any]]
    warnings: List[Dict[str, Any]]
    low_confidence_items: List[Dict[str, Any]]  # routed to inbox
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)
    
    def to_markdown(self) -> str:
        """Render as markdown for audit trail."""
        lines = [
            f"# Intake Receipt: {self.receipt_id}",
            f"**Timestamp:** {self.timestamp}",
            f"**Action:** {self.user_action}",
            "",
            "## Summary",
            f"- Files processed: {self.files_processed}",
            f"- Classes created: {self.classes_created}",
            f"- Classes updated: {self.classes_updated}",
            f"- Items created: {self.items_created}",
            f"- Artifacts pinned: {self.artifacts_pinned}",
        ]
        
        if self.errors:
            lines.extend(["", "## Errors"])
            for err in self.errors:
                lines.append(f"- **{err.get('file', 'unknown')}**: {err.get('message', 'unknown error')}")
        
        if self.warnings:
            lines.extend(["", "## Warnings"])
            for warn in self.warnings:
                lines.append(f"- **{warn.get('file', 'unknown')}**: {warn.get('message', 'warning')}")
        
        if self.low_confidence_items:
            lines.extend(["", "## Low Confidence Items (in Inbox)"])
            for item in self.low_confidence_items:
                lines.append(f"- {item.get('title', 'unknown')}: {item.get('reason', 'low confidence')}")
        
        return "\n".join(lines)


class IntakeService:
    """
    Syllabus intake workflow: batch upload → classify → confirm → create.
    
    Deterministic parsing. Graceful error handling. Full audit trail.
    """
    
    def __init__(self):
        """Initialize the intake service."""
        self.current_receipt: Optional[IntakeReceipt] = None
    
    def classify_file(self, filename: str, content: str, lLM_adapter: Optional[Any] = None) -> Dict[str, Any]:
        """
        Classify a file: extract class code, name, confidence.
        
        Args:
            filename: uploaded filename
            content: file text content (OCR'd if PDF)
            llm_adapter: optional LLM adapter for enhanced extraction
        
        Returns:
            {
              "filename": str,
              "class_code": str | None,
              "class_name": str | None,
              "confidence": float [0-1],
              "deadlines": List[Dict],
              "meeting_times": List[str],
              "instructor": str | None,
              "grading_breakdown": Dict | None,
              "method": "llm" | "heuristic" | "manual"
            }
        """
        
        # Try LLM first if available
        if lLM_adapter and lLM_adapter.is_available():
            try:
                return lLM_adapter.classify_syllabus(filename, content)
            except Exception as e:
                # Fall back to heuristic, log warning
                pass
        
        # Deterministic heuristic fallback
        return self._classify_heuristic(filename, content)
    
    def _classify_heuristic(self, filename: str, content: str) -> Dict[str, Any]:
        """
        Deterministic syllabus classification via pattern matching.
        
        Looks for:
        - Course codes (PHYS214, ECE347, etc.)
        - "Instructor", "Professor", "Course Title", "Course Name"
        - Dates and deadline keywords
        - Grading patterns
        """
        
        result = {
            "filename": filename,
            "class_code": None,
            "class_name": None,
            "confidence": 0.0,
            "deadlines": [],
            "meeting_times": [],
            "instructor": None,
            "grading_breakdown": None,
            "method": "heuristic"
        }
        
        # Extract course code (e.g., PHYS214, CS101)
        import re
        code_match = re.search(r'\b([A-Z]{2,4}\d{3,4})\b', content)
        if code_match:
            result["class_code"] = code_match.group(1)
            result["confidence"] += 0.25
        
        # Extract instructor name
        instr_patterns = [
            r"[Ii]nstructor:?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
            r"[Pp]rofessor:?\s+([A-Z][a-z]+\s+[A-Z][a-z]+)",
        ]
        for pattern in instr_patterns:
            instr_match = re.search(pattern, content)
            if instr_match:
                result["instructor"] = instr_match.group(1)
                result["confidence"] += 0.15
                break
        
        # Extract deadlines (simple: "Due X" or date patterns)
        deadline_patterns = [
            r"[Dd]ue\s+([A-Za-z]+\s+\d{1,2}(?:,?\s*\d{4})?)",
            r"([Dd]eadline|[Ss]ubmission).*?([A-Za-z]+\s+\d{1,2})",
        ]
        for pattern in deadline_patterns:
            matches = re.findall(pattern, content)
            for match in matches[:5]:  # limit to 5
                date_str = match if isinstance(match, str) else match[0] if isinstance(match, tuple) else None
                if date_str:
                    result["deadlines"].append({
                        "description": "Assignment/Exam",
                        "date": date_str,
                        "confidence": 0.7
                    })
        
        if result["deadlines"]:
            result["confidence"] += 0.25
        
        # Confidence floor: always at least "unconfirmed"
        if not result["class_code"] and not result["instructor"]:
            result["confidence"] = 0.3  # low confidence, needs manual review
        
        result["confidence"] = min(result["confidence"], 1.0)
        
        return result
    
    def confirm_and_create(
        self,
        classifications: List[Dict[str, Any]],
        confirmations: Dict[str, Dict[str, Any]],
        user_id: str = "system"
    ) -> Tuple[IntakeReceipt, List[Dict[str, Any]]]:
        """
        Confirm classifications and create classes/items/artifacts.
        
        Args:
            classifications: list of raw classifications
            confirmations: {filename: {class_code, class_name, ...}} with user edits
            user_id: for audit trail
        
        Returns:
            (receipt, created_objects) for undo tracking
        """
        
        receipt = IntakeReceipt(
            receipt_id=str(uuid.uuid4())[:8],
            timestamp=datetime.utcnow().isoformat(),
            user_action="syllabus_intake",
            files_processed=len(classifications),
            classes_created=0,
            classes_updated=0,
            items_created=0,
            artifacts_pinned=0,
            errors=[],
            warnings=[],
            low_confidence_items=[]
        )
        
        created_objects = []
        
        for classification in classifications:
            filename = classification["filename"]
            confirmed = confirmations.get(filename, {})
            
            # Use confirmed data or fallback to classification
            class_code = confirmed.get("class_code") or classification.get("class_code")
            class_name = confirmed.get("class_name") or classification.get("class_name")
            
            if not class_code or not class_name:
                # Low confidence, route to inbox
                receipt.low_confidence_items.append({
                    "title": filename,
                    "reason": "Missing class code or name"
                })
                continue
            
            try:
                # Simulate class creation
                class_obj = {
                    "id": str(uuid.uuid4())[:8],
                    "code": class_code,
                    "name": class_name,
                    "instructor": confirmed.get("instructor") or classification.get("instructor"),
                    "created_at": datetime.utcnow().isoformat()
                }
                receipt.classes_created += 1
                created_objects.append(("class", class_obj))
                
                # Create syllabus artifact pinned to class
                artifact_obj = {
                    "id": str(uuid.uuid4())[:8],
                    "type": "syllabus",
                    "title": f"Syllabus: {class_code}",
                    "class_id": class_obj["id"],
                    "created_at": datetime.utcnow().isoformat()
                }
                receipt.artifacts_pinned += 1
                created_objects.append(("artifact", artifact_obj))
                
                # Create deadline items
                for deadline in classification.get("deadlines", []):
                    item_obj = {
                        "id": str(uuid.uuid4())[:8],
                        "type": "task",
                        "title": deadline.get("description", "Assignment"),
                        "context": class_code,
                        "due_date": deadline.get("date"),
                        "state": "active",
                        "created_at": datetime.utcnow().isoformat()
                    }
                    receipt.items_created += 1
                    created_objects.append(("item", item_obj))
                
            except Exception as e:
                receipt.errors.append({
                    "file": filename,
                    "message": str(e)
                })
        
        self.current_receipt = receipt
        return receipt, created_objects
    
    def get_receipt_markdown(self) -> str:
        """Return current receipt as markdown (for display/audit)."""
        if not self.current_receipt:
            return "No intake receipt available."
        return self.current_receipt.to_markdown()
    
    def to_system_response(self, receipt: IntakeReceipt) -> Dict[str, Any]:
        """
        Convert receipt to deterministic system response.
        
        Same structure every time: icon + primary + details + secondary + cta
        """
        
        primary = f"Intake complete: {receipt.classes_created} classes, {receipt.items_created} deadlines"
        
        details_lines = []
        if receipt.files_processed > 0:
            details_lines.append(f"Processed {receipt.files_processed} files")
        if receipt.errors:
            details_lines.append(f"{len(receipt.errors)} errors (see receipt)")
        if receipt.low_confidence_items:
            details_lines.append(f"{len(receipt.low_confidence_items)} items need review (in Inbox)")
        
        return {
            "icon": "📚",
            "primary": primary,
            "details": " | ".join(details_lines) if details_lines else "All processed successfully",
            "secondary": f"Receipt: {receipt.receipt_id}",
            "cta": "View receipt",
            "cta_action": f"show_receipt:{receipt.receipt_id}"
        }
