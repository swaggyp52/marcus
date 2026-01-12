"""
Export service for generating deliverable bundles.
"""

import json
import shutil
from pathlib import Path
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from zipfile import ZipFile

from ..core.models import Assignment, Artifact, ExtractedText, Plan


class ExportService:
    """Service for exporting assignment bundles."""

    def __init__(self, exports_path: Path):
        self.exports_path = exports_path
        self.exports_path.mkdir(parents=True, exist_ok=True)

    def export_assignment_bundle(
        self,
        assignment: Assignment,
        db: Session,
        include_artifacts: bool = True,
        include_extracted: bool = True,
        include_plans: bool = True
    ) -> Path:
        """
        Export a complete assignment bundle as a ZIP file.
        """
        # Create timestamped export directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        export_name = f"{assignment.title.replace(' ', '_')}_{timestamp}"
        export_dir = self.exports_path / export_name
        export_dir.mkdir(exist_ok=True)

        # Create manifest
        manifest = {
            "assignment": {
                "id": assignment.id,
                "title": assignment.title,
                "description": assignment.description,
                "due_date": assignment.due_date.isoformat() if assignment.due_date else None,
                "status": assignment.status,
                "exported_at": datetime.now().isoformat()
            },
            "contents": []
        }

        # Export plan if available
        if include_plans:
            plans = db.query(Plan).filter(Plan.assignment_id == assignment.id).all()
            if plans:
                plans_dir = export_dir / "plans"
                plans_dir.mkdir(exist_ok=True)

                for i, plan in enumerate(plans, 1):
                    plan_md = self._generate_plan_markdown(plan)
                    plan_file = plans_dir / f"plan_{i}.md"
                    with open(plan_file, 'w', encoding='utf-8') as f:
                        f.write(plan_md)

                    manifest["contents"].append({
                        "type": "plan",
                        "file": str(plan_file.relative_to(export_dir))
                    })

        # Export artifacts
        if include_artifacts:
            artifacts = db.query(Artifact).filter(
                Artifact.assignment_id == assignment.id
            ).all()

            if artifacts:
                artifacts_dir = export_dir / "artifacts"
                artifacts_dir.mkdir(exist_ok=True)

                for artifact in artifacts:
                    src = Path(artifact.file_path)
                    if src.exists():
                        dst = artifacts_dir / artifact.original_filename
                        shutil.copy2(src, dst)

                        manifest["contents"].append({
                            "type": "artifact",
                            "original_filename": artifact.original_filename,
                            "file_type": artifact.file_type,
                            "file": str(dst.relative_to(export_dir))
                        })

        # Export extracted text
        if include_extracted:
            all_extracted = []
            artifacts = db.query(Artifact).filter(
                Artifact.assignment_id == assignment.id
            ).all()

            for artifact in artifacts:
                extracted_texts = db.query(ExtractedText).filter(
                    ExtractedText.artifact_id == artifact.id,
                    ExtractedText.extraction_status == "success"
                ).all()

                for ext in extracted_texts:
                    all_extracted.append({
                        "source_file": artifact.original_filename,
                        "method": ext.extraction_method,
                        "content": ext.content
                    })

            if all_extracted:
                extracted_md = self._generate_extracted_text_markdown(all_extracted)
                extracted_file = export_dir / "extracted_text.md"
                with open(extracted_file, 'w', encoding='utf-8') as f:
                    f.write(extracted_md)

                manifest["contents"].append({
                    "type": "extracted_text",
                    "file": "extracted_text.md"
                })

        # Write manifest
        manifest_file = export_dir / "manifest.json"
        with open(manifest_file, 'w', encoding='utf-8') as f:
            json.dump(manifest, f, indent=2)

        # Create ZIP archive
        zip_path = self.exports_path / f"{export_name}.zip"
        with ZipFile(zip_path, 'w') as zipf:
            for file in export_dir.rglob('*'):
                if file.is_file():
                    zipf.write(file, file.relative_to(export_dir))

        # Clean up temporary directory
        shutil.rmtree(export_dir)

        return zip_path

    def _generate_plan_markdown(self, plan: Plan) -> str:
        """Generate markdown representation of a plan."""
        steps = json.loads(plan.steps or '[]')
        materials = json.loads(plan.required_materials or '[]')
        outputs = json.loads(plan.output_formats or '[]')

        md_parts = [
            f"# {plan.title}",
            "",
            f"**Generated:** {plan.created_at.strftime('%Y-%m-%d %H:%M')}",
            f"**Effort Estimate:** {plan.effort_estimate}",
            f"**Confidence:** {plan.confidence}",
            "",
            "---",
            ""
        ]

        if steps:
            md_parts.append("## Steps")
            md_parts.append("")
            for step in steps:
                md_parts.append(f"{step['order']}. **{step['description']}** (Effort: {step['effort']})")
            md_parts.append("")

        if materials:
            md_parts.append("## Required Materials")
            md_parts.append("")
            for material in materials:
                md_parts.append(f"- {material}")
            md_parts.append("")

        if outputs:
            md_parts.append("## Output Formats")
            md_parts.append("")
            for output in outputs:
                md_parts.append(f"- {output}")
            md_parts.append("")

        if plan.draft_outline:
            md_parts.append("## Draft Outline")
            md_parts.append("")
            md_parts.append(plan.draft_outline)
            md_parts.append("")

        if plan.assumptions:
            md_parts.append("## Assumptions")
            md_parts.append("")
            md_parts.append(plan.assumptions)
            md_parts.append("")

        if plan.risks_unknowns and plan.risks_unknowns != "None identified at this time":
            md_parts.append("## Risks & Unknowns")
            md_parts.append("")
            md_parts.append(plan.risks_unknowns)
            md_parts.append("")

        return "\n".join(md_parts)

    def _generate_extracted_text_markdown(self, extracted_list: List[dict]) -> str:
        """Generate markdown with all extracted text."""
        md_parts = [
            "# Extracted Text from Assignment Files",
            "",
            f"**Extracted:** {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "",
            "---",
            ""
        ]

        for item in extracted_list:
            md_parts.append(f"## {item['source_file']}")
            md_parts.append("")
            md_parts.append(f"**Extraction Method:** {item['method']}")
            md_parts.append("")
            md_parts.append("```")
            md_parts.append(item['content'])
            md_parts.append("```")
            md_parts.append("")
            md_parts.append("---")
            md_parts.append("")

        return "\n".join(md_parts)
