"""
Text extraction from various file types.
"""

from pathlib import Path
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from ..core.models import Artifact, ExtractedText


class ExtractionService:
    """Service for extracting text from uploaded files."""

    def extract_from_artifact(self, artifact: Artifact, db: Session) -> ExtractedText:
        """
        Extract text from an artifact based on its file type.
        """
        file_path = Path(artifact.file_path)

        if artifact.file_type == 'pdf':
            return self._extract_pdf(artifact, file_path, db)
        elif artifact.file_type == 'image':
            return self._extract_image(artifact, file_path, db)
        elif artifact.file_type == 'docx':
            return self._extract_docx(artifact, file_path, db)
        elif artifact.file_type == 'text':
            return self._extract_text(artifact, file_path, db)
        elif artifact.file_type == 'code':
            return self._extract_text(artifact, file_path, db)
        else:
            # Unknown file type
            extracted = ExtractedText(
                artifact_id=artifact.id,
                content="",
                extraction_method="none",
                extraction_status="failed",
                error_message=f"Unsupported file type: {artifact.file_type}"
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

    def _extract_pdf(self, artifact: Artifact, file_path: Path, db: Session) -> ExtractedText:
        """Extract text from PDF."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    text_parts.append(f"--- Page {i+1} ---\n{page_text}")

            content = "\n\n".join(text_parts)

            extracted = ExtractedText(
                artifact_id=artifact.id,
                content=content,
                extraction_method="pdf",
                extraction_status="success" if content else "partial"
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

        except Exception as e:
            extracted = ExtractedText(
                artifact_id=artifact.id,
                content="",
                extraction_method="pdf",
                extraction_status="failed",
                error_message=str(e)
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

    def _extract_image(self, artifact: Artifact, file_path: Path, db: Session) -> ExtractedText:
        """Extract text from image using OCR."""
        try:
            import pytesseract
            from PIL import Image

            image = Image.open(file_path)
            text = pytesseract.image_to_string(image)

            extracted = ExtractedText(
                artifact_id=artifact.id,
                content=text,
                extraction_method="ocr",
                extraction_status="success" if text.strip() else "partial"
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

        except Exception as e:
            # If Tesseract is not installed, provide helpful error
            error_msg = str(e)
            if "tesseract" in error_msg.lower():
                error_msg = "Tesseract OCR not installed. Install from: https://github.com/tesseract-ocr/tesseract"

            extracted = ExtractedText(
                artifact_id=artifact.id,
                content="",
                extraction_method="ocr",
                extraction_status="failed",
                error_message=error_msg
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

    def _extract_docx(self, artifact: Artifact, file_path: Path, db: Session) -> ExtractedText:
        """Extract text from DOCX."""
        try:
            from docx import Document

            doc = Document(str(file_path))
            paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
            content = "\n\n".join(paragraphs)

            extracted = ExtractedText(
                artifact_id=artifact.id,
                content=content,
                extraction_method="docx",
                extraction_status="success" if content else "partial"
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

        except Exception as e:
            extracted = ExtractedText(
                artifact_id=artifact.id,
                content="",
                extraction_method="docx",
                extraction_status="failed",
                error_message=str(e)
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

    def _extract_text(self, artifact: Artifact, file_path: Path, db: Session) -> ExtractedText:
        """Extract plain text."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

            extracted = ExtractedText(
                artifact_id=artifact.id,
                content=content,
                extraction_method="plain",
                extraction_status="success"
            )
            db.add(extracted)
            db.commit()
            db.refresh(extracted)
            return extracted

        except Exception as e:
            # Try with different encodings
            try:
                with open(file_path, 'r', encoding='latin-1') as f:
                    content = f.read()

                extracted = ExtractedText(
                    artifact_id=artifact.id,
                    content=content,
                    extraction_method="plain",
                    extraction_status="success"
                )
                db.add(extracted)
                db.commit()
                db.refresh(extracted)
                return extracted
            except Exception as e2:
                extracted = ExtractedText(
                    artifact_id=artifact.id,
                    content="",
                    extraction_method="plain",
                    extraction_status="failed",
                    error_message=str(e2)
                )
                db.add(extracted)
                db.commit()
                db.refresh(extracted)
                return extracted
