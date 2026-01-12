"""
File upload, storage, and extraction services.
"""

import hashlib
import shutil
from pathlib import Path
from datetime import datetime
from typing import Tuple, Optional
from sqlalchemy.orm import Session

from ..core.models import Artifact, ExtractedText


class FileService:
    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.vault_path.mkdir(parents=True, exist_ok=True)

    def save_file(
        self,
        file_content: bytes,
        original_filename: str,
        assignment_id: int,
        db: Session
    ) -> Artifact:
        """
        Save uploaded file to vault and create artifact record.
        """
        # Compute hash
        file_hash = hashlib.sha256(file_content).hexdigest()

        # Determine file type
        file_type = self._get_file_type(original_filename)

        # Create stable filename: hash + original extension
        ext = Path(original_filename).suffix
        filename = f"{file_hash}{ext}"
        file_path = self.vault_path / filename

        # Write file
        with open(file_path, "wb") as f:
            f.write(file_content)

        # Create artifact record
        artifact = Artifact(
            assignment_id=assignment_id,
            filename=filename,
            original_filename=original_filename,
            file_path=str(file_path),
            file_type=file_type,
            file_size=len(file_content),
            file_hash=file_hash
        )
        db.add(artifact)
        db.commit()
        db.refresh(artifact)

        return artifact

    def _get_file_type(self, filename: str) -> str:
        """Determine file type from extension."""
        ext = Path(filename).suffix.lower()

        if ext == '.pdf':
            return 'pdf'
        elif ext in ['.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.gif']:
            return 'image'
        elif ext in ['.docx', '.doc']:
            return 'docx'
        elif ext in ['.txt', '.md']:
            return 'text'
        elif ext in ['.py', '.js', '.java', '.c', '.cpp', '.h', '.cs', '.go', '.rs']:
            return 'code'
        else:
            return 'unknown'
