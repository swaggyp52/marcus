"""
Plan generation service.
Generates structured plans for assignments with or without LLM.
"""

import json
from datetime import datetime
from typing import List, Dict, Any
from sqlalchemy.orm import Session

from ..core.models import Assignment, Plan, Artifact, ExtractedText, AuditLog
from .claim_service import ClaimService


class PlanService:
    """Service for generating assignment plans."""

    def __init__(self, online_mode: bool = False):
        self.online_mode = online_mode

    def generate_plan(self, assignment: Assignment, db: Session) -> Plan:
        """
        Generate a structured plan for an assignment.
        Uses template-based approach (can be upgraded to LLM later).
        """
        # Gather context
        artifacts = db.query(Artifact).filter(
            Artifact.assignment_id == assignment.id
        ).all()

        extracted_texts = []
        for artifact in artifacts:
            texts = db.query(ExtractedText).filter(
                ExtractedText.artifact_id == artifact.id
            ).all()
            extracted_texts.extend(texts)

        # Build plan using deterministic template
        plan_data = self._build_template_plan(assignment, artifacts, extracted_texts)

        # Create plan record
        plan = Plan(
            assignment_id=assignment.id,
            title=plan_data["title"],
            steps=json.dumps(plan_data["steps"]),
            required_materials=json.dumps(plan_data["required_materials"]),
            output_formats=json.dumps(plan_data["output_formats"]),
            draft_outline=plan_data["draft_outline"],
            effort_estimate=plan_data["effort_estimate"],
            risks_unknowns=plan_data["risks_unknowns"],
            assumptions=plan_data["assumptions"],
            confidence=plan_data["confidence"]
        )

        db.add(plan)

        # Log the plan generation
        audit_log = AuditLog(
            event_type="plan_generated",
            online_mode="online" if self.online_mode else "offline",
            user_action=f"Generated plan for assignment: {assignment.title}",
            extra_data=json.dumps({
                "assignment_id": assignment.id,
                "artifact_count": len(artifacts),
                "extracted_text_count": len(extracted_texts)
            })
        )
        db.add(audit_log)

        db.commit()
        db.refresh(plan)

        # V0.2: Extract claims from plan
        claim_service = ClaimService()
        claims = claim_service.extract_claims_from_plan(plan, db)

        # Auto-link claims to supporting evidence
        for claim in claims:
            evidence = claim_service.find_supporting_evidence(claim, artifacts, db)

            # Create support links for top evidence
            for ev in evidence[:3]:  # Link top 3 pieces of evidence
                claim_service.link_claim_to_source(
                    claim_id=claim.id,
                    artifact_id=ev['artifact_id'],
                    extracted_text_id=ev.get('extracted_text_id'),
                    quote=ev['quote'],
                    page_number=None,  # TODO: extract from PDF metadata in v0.3
                    section_title=None,
                    relevance_score=ev['relevance_score'],
                    db=db
                )

        return plan

    def _build_template_plan(
        self,
        assignment: Assignment,
        artifacts: List[Artifact],
        extracted_texts: List[ExtractedText]
    ) -> Dict[str, Any]:
        """
        Build a plan using deterministic templates.
        This provides a baseline that works without LLM.
        """
        # Analyze what we have
        has_pdf = any(a.file_type == 'pdf' for a in artifacts)
        has_images = any(a.file_type == 'image' for a in artifacts)
        has_code = any(a.file_type == 'code' for a in artifacts)
        has_extracted = any(et.extraction_status == 'success' for et in extracted_texts)

        # Build steps
        steps = [
            {
                "order": 1,
                "description": "Review all uploaded materials and extracted content",
                "effort": "S"
            },
            {
                "order": 2,
                "description": "Identify key requirements and objectives from assignment description",
                "effort": "M"
            },
            {
                "order": 3,
                "description": "Break down the assignment into specific tasks",
                "effort": "M"
            },
            {
                "order": 4,
                "description": "Research any unclear concepts or requirements",
                "effort": "M"
            },
            {
                "order": 5,
                "description": "Create solution outline or draft structure",
                "effort": "L"
            },
            {
                "order": 6,
                "description": "Implement/write the solution",
                "effort": "L"
            },
            {
                "order": 7,
                "description": "Review, test, and refine",
                "effort": "M"
            },
            {
                "order": 8,
                "description": "Format and prepare final deliverable",
                "effort": "S"
            }
        ]

        # Required materials
        required_materials = [
            f"Assignment description: {assignment.title}",
        ]

        if assignment.description:
            required_materials.append("Detailed requirements (see description)")

        for artifact in artifacts:
            required_materials.append(f"{artifact.original_filename} ({artifact.file_type})")

        # Output formats (suggest common academic formats)
        output_formats = [
            "PDF document",
            "Markdown notes",
            "DOCX report"
        ]

        if has_code:
            output_formats.append("Source code files")
            output_formats.append("Code documentation")

        # Draft outline
        outline_parts = [
            f"# {assignment.title}",
            "",
            "## Overview",
            f"Due: {assignment.due_date.strftime('%Y-%m-%d %H:%M') if assignment.due_date else 'Not set'}",
            "",
            "## Approach",
            "1. Analyze the problem/requirements",
            "2. Plan the solution strategy",
            "3. Execute the implementation",
            "4. Verify and document results",
            "",
            "## Resources Available"
        ]

        for material in required_materials:
            outline_parts.append(f"- {material}")

        outline_parts.extend([
            "",
            "## Deliverables"
        ])

        for fmt in output_formats:
            outline_parts.append(f"- {fmt}")

        draft_outline = "\n".join(outline_parts)

        # Effort estimate
        effort_estimate = "M"  # Default to Medium
        if len(artifacts) > 5 or (assignment.description and len(assignment.description) > 500):
            effort_estimate = "L"
        elif len(artifacts) <= 2 and (not assignment.description or len(assignment.description) < 200):
            effort_estimate = "S"

        # Risks and unknowns
        risks = []
        if not has_extracted:
            risks.append("No text extracted from uploaded files yet")
        if not assignment.description:
            risks.append("No detailed assignment description provided")
        if not assignment.due_date:
            risks.append("No due date set - timeline unclear")

        risks_unknowns = "; ".join(risks) if risks else "None identified at this time"

        # Assumptions
        assumptions_list = [
            "All required materials have been uploaded",
            "Assignment description is complete and accurate",
        ]

        if has_extracted:
            assumptions_list.append("Extracted text is representative of file content")

        assumptions = "; ".join(assumptions_list)

        # Confidence
        confidence = "medium"
        if has_extracted and assignment.description and assignment.due_date:
            confidence = "high"
        elif not has_extracted or not assignment.description:
            confidence = "low"

        return {
            "title": f"Plan for: {assignment.title}",
            "steps": steps,
            "required_materials": required_materials,
            "output_formats": output_formats,
            "draft_outline": draft_outline,
            "effort_estimate": effort_estimate,
            "risks_unknowns": risks_unknowns,
            "assumptions": assumptions,
            "confidence": confidence
        }
