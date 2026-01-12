"""
Chunking service for Marcus v0.3.
Deterministic text chunking with heading-awareness and context preservation.
"""

from typing import List, Dict, Optional
import re
from sqlalchemy.orm import Session

from ..core.models import ExtractedText, TextChunk, Artifact, Assignment


class ChunkingService:
    """
    Chunks extracted text into semantic units for search and retrieval.

    Chunking strategy:
    1. Detect headings (markdown-style # or all-caps lines)
    2. Split by paragraphs (double newline)
    3. Ensure min/max chunk sizes with overlap
    4. Preserve context (previous heading, page number)

    Deterministic: same input always produces same chunks.
    """

    def __init__(
        self,
        min_chunk_size: int = 100,
        max_chunk_size: int = 800,
        overlap_size: int = 50
    ):
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

    def chunk_extracted_text(
        self,
        extracted_text: ExtractedText,
        db: Session
    ) -> List[TextChunk]:
        """
        Chunk an ExtractedText object into TextChunk records.
        Returns created chunks.
        """
        # Get artifact context
        artifact = db.query(Artifact).filter(
            Artifact.id == extracted_text.artifact_id
        ).first()

        if not artifact:
            raise ValueError(f"Artifact not found for extracted_text {extracted_text.id}")

        # Get assignment/class context
        assignment = None
        class_id = None
        if artifact.assignment_id:
            assignment = db.query(Assignment).filter(
                Assignment.id == artifact.assignment_id
            ).first()
            if assignment:
                class_id = assignment.class_id

        # Perform chunking
        raw_chunks = self._split_into_chunks(extracted_text.content)

        # Create TextChunk records
        chunks = []
        for idx, chunk_data in enumerate(raw_chunks):
            chunk = TextChunk(
                extracted_text_id=extracted_text.id,
                artifact_id=artifact.id,
                assignment_id=artifact.assignment_id,
                class_id=class_id,
                chunk_index=idx,
                content=chunk_data['text'],
                chunk_type=chunk_data['type'],
                section_title=chunk_data.get('section_title'),
                page_number=chunk_data.get('page_number'),
                word_count=len(chunk_data['text'].split()),
                char_start=chunk_data['char_start'],
                char_end=chunk_data['char_end']
            )
            db.add(chunk)
            chunks.append(chunk)

        db.commit()
        return chunks

    def _split_into_chunks(self, text: str) -> List[Dict]:
        """
        Split text into chunks with metadata.
        Returns list of dicts with: text, type, section_title, char_start, char_end
        """
        if not text or len(text.strip()) == 0:
            return []

        chunks = []
        current_section = None

        # Strategy 1: Detect headings
        lines = text.split('\n')
        current_chunk = []
        current_chunk_start = 0
        char_pos = 0

        for line_idx, line in enumerate(lines):
            line_start = char_pos
            char_pos += len(line) + 1  # +1 for newline

            # Check if this line is a heading
            is_heading = self._is_heading(line)

            if is_heading:
                # Flush current chunk if exists
                if current_chunk:
                    chunk_text = '\n'.join(current_chunk)
                    if len(chunk_text.strip()) >= self.min_chunk_size:
                        chunks.append({
                            'text': chunk_text,
                            'type': 'paragraph',
                            'section_title': current_section,
                            'char_start': current_chunk_start,
                            'char_end': line_start
                        })

                # Update section title
                current_section = line.strip().lstrip('#').strip()

                # Start new chunk with heading
                current_chunk = [line]
                current_chunk_start = line_start

            else:
                # Add line to current chunk
                current_chunk.append(line)

                # Check if chunk is getting too large
                chunk_text = '\n'.join(current_chunk)
                if len(chunk_text) >= self.max_chunk_size:
                    # Split here
                    chunks.append({
                        'text': chunk_text,
                        'type': 'paragraph',
                        'section_title': current_section,
                        'char_start': current_chunk_start,
                        'char_end': char_pos
                    })

                    # Start new chunk with overlap
                    overlap_lines = current_chunk[-3:] if len(current_chunk) >= 3 else current_chunk
                    current_chunk = overlap_lines
                    current_chunk_start = char_pos - sum(len(l) + 1 for l in overlap_lines)

        # Flush final chunk
        if current_chunk:
            chunk_text = '\n'.join(current_chunk)
            if len(chunk_text.strip()) >= self.min_chunk_size:
                chunks.append({
                    'text': chunk_text,
                    'type': 'paragraph',
                    'section_title': current_section,
                    'char_start': current_chunk_start,
                    'char_end': len(text)
                })

        # If no chunks created (text too short or no structure), create one chunk
        if not chunks and text.strip():
            chunks.append({
                'text': text,
                'type': 'full_text',
                'section_title': None,
                'char_start': 0,
                'char_end': len(text)
            })

        return chunks

    def _is_heading(self, line: str) -> bool:
        """
        Detect if a line is likely a heading.

        Heading indicators:
        - Starts with # (Markdown)
        - All caps (more than 50% uppercase letters)
        - Short line followed by ====== or ------
        - Ends with colon and is short
        """
        line = line.strip()

        if not line:
            return False

        # Markdown heading
        if line.startswith('#'):
            return True

        # All caps (at least 3 words, >50% uppercase)
        words = line.split()
        if len(words) >= 2 and len(line) >= 10:
            alpha_chars = [c for c in line if c.isalpha()]
            if alpha_chars:
                upper_ratio = sum(1 for c in alpha_chars if c.isupper()) / len(alpha_chars)
                if upper_ratio > 0.7:
                    return True

        # Ends with colon (and is short)
        if line.endswith(':') and len(line) < 100 and len(words) <= 10:
            return True

        return False

    def get_chunk_context(
        self,
        chunk: TextChunk,
        context_chunks: int = 1,
        db: Session = None
    ) -> Dict:
        """
        Get surrounding context for a chunk.
        Returns dict with: previous_chunks, current_chunk, next_chunks, metadata
        """
        if not db:
            return {
                'previous_chunks': [],
                'current_chunk': chunk,
                'next_chunks': [],
                'metadata': {}
            }

        # Get surrounding chunks
        all_chunks = db.query(TextChunk).filter(
            TextChunk.extracted_text_id == chunk.extracted_text_id
        ).order_by(TextChunk.chunk_index).all()

        current_idx = None
        for idx, c in enumerate(all_chunks):
            if c.id == chunk.id:
                current_idx = idx
                break

        if current_idx is None:
            return {
                'previous_chunks': [],
                'current_chunk': chunk,
                'next_chunks': [],
                'metadata': {}
            }

        # Get context
        prev_start = max(0, current_idx - context_chunks)
        next_end = min(len(all_chunks), current_idx + context_chunks + 1)

        previous_chunks = all_chunks[prev_start:current_idx]
        next_chunks = all_chunks[current_idx + 1:next_end]

        # Get artifact metadata
        artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()

        metadata = {
            'artifact_filename': artifact.original_filename if artifact else None,
            'section_title': chunk.section_title,
            'page_number': chunk.page_number,
            'chunk_index': chunk.chunk_index,
            'total_chunks': len(all_chunks)
        }

        return {
            'previous_chunks': previous_chunks,
            'current_chunk': chunk,
            'next_chunks': next_chunks,
            'metadata': metadata
        }

    def chunk_all_extracted_texts(self, db: Session, force_rechunk: bool = False):
        """
        Chunk all ExtractedText records that don't have chunks yet.
        Used for batch processing and migrations.
        """
        # Find extracted texts without chunks
        extracted_texts = db.query(ExtractedText).all()

        chunked_count = 0
        for extracted_text in extracted_texts:
            # Check if already chunked
            existing_chunks = db.query(TextChunk).filter(
                TextChunk.extracted_text_id == extracted_text.id
            ).count()

            if existing_chunks > 0 and not force_rechunk:
                continue

            # Delete old chunks if rechunking
            if force_rechunk and existing_chunks > 0:
                db.query(TextChunk).filter(
                    TextChunk.extracted_text_id == extracted_text.id
                ).delete()
                db.commit()

            # Chunk it
            try:
                chunks = self.chunk_extracted_text(extracted_text, db)
                chunked_count += 1
                print(f"Chunked extracted_text {extracted_text.id}: {len(chunks)} chunks")
            except Exception as e:
                print(f"Error chunking extracted_text {extracted_text.id}: {e}")

        return chunked_count
