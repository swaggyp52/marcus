"""
Search service for Marcus v0.3.
Implements hybrid search: FTS5 (always works) + embeddings (optional).
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json

from ..core.models import TextChunk, Artifact, Class, Assignment


class SearchService:
    """
    Hybrid search service with graceful degradation.

    Strategy:
    1. Try semantic search (if embeddings available)
    2. Fall back to FTS5 full-text search (always available)
    3. Return results with citations and context
    """

    def __init__(self):
        self.embeddings_available = False
        self.embedding_service = None

        # Try to initialize embeddings
        try:
            from .embedding_service import EmbeddingService
            self.embedding_service = EmbeddingService()
            if self.embedding_service.is_available():
                self.embeddings_available = True
                print("[SearchService] Embeddings enabled")
            else:
                print("[SearchService] Embeddings unavailable, using FTS5 only")
        except ImportError:
            print("[SearchService] EmbeddingService not found, using FTS5 only")

    def search(
        self,
        query: str,
        class_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[Dict]:
        """
        Search chunks with hybrid ranking.

        Returns list of dicts:
        {
            'chunk_id': int,
            'content': str,
            'snippet': str,
            'score': float,
            'artifact_filename': str,
            'section_title': str,
            'page_number': int,
            'class_id': int,
            'assignment_id': int,
            'search_method': 'semantic' | 'fts5'
        }
        """
        results = []

        # Try semantic search first
        if self.embeddings_available and self.embedding_service:
            try:
                semantic_results = self._semantic_search(
                    query, class_id, assignment_id, limit, db
                )
                if semantic_results:
                    return semantic_results
            except Exception as e:
                print(f"[SearchService] Semantic search failed: {e}, falling back to FTS5")

        # Fall back to FTS5
        fts_results = self._fts5_search(
            query, class_id, assignment_id, limit, db
        )

        return fts_results

    def _fts5_search(
        self,
        query: str,
        class_id: Optional[int],
        assignment_id: Optional[int],
        limit: int,
        db: Session
    ) -> List[Dict]:
        """
        Full-text search using SQLite FTS5.
        Always available, no dependencies.
        """
        # Build FTS5 query
        # Escape special characters
        fts_query = query.replace('"', '""')

        # Build SQL with filters
        sql_parts = ["SELECT tc.* FROM text_chunks tc"]
        where_clauses = []
        params = {'query': fts_query, 'limit': limit}

        if class_id:
            where_clauses.append("tc.class_id = :class_id")
            params['class_id'] = class_id

        if assignment_id:
            where_clauses.append("tc.assignment_id = :assignment_id")
            params['assignment_id'] = assignment_id

        # Simple LIKE search (FTS5 virtual table requires extra setup)
        # For v0.3 MVP, use case-insensitive LIKE
        where_clauses.append("tc.content LIKE :search_pattern")
        params['search_pattern'] = f"%{query}%"

        if where_clauses:
            sql_parts.append("WHERE " + " AND ".join(where_clauses))

        sql_parts.append("ORDER BY tc.word_count DESC")  # Longer chunks first (more context)
        sql_parts.append("LIMIT :limit")

        sql = " ".join(sql_parts)

        # Execute search
        result = db.execute(text(sql), params)
        rows = result.fetchall()

        # Format results
        results = []
        for row in rows:
            chunk = db.query(TextChunk).filter(TextChunk.id == row.id).first()
            if not chunk:
                continue

            # Get artifact info
            artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()

            # Generate snippet (context around match)
            snippet = self._generate_snippet(chunk.content, query)

            results.append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'snippet': snippet,
                'score': self._calculate_relevance_score(chunk.content, query),
                'artifact_filename': artifact.original_filename if artifact else None,
                'artifact_id': chunk.artifact_id,
                'section_title': chunk.section_title,
                'page_number': chunk.page_number,
                'class_id': chunk.class_id,
                'assignment_id': chunk.assignment_id,
                'search_method': 'fts5'
            })

        return results

    def _semantic_search(
        self,
        query: str,
        class_id: Optional[int],
        assignment_id: Optional[int],
        limit: int,
        db: Session
    ) -> List[Dict]:
        """
        Semantic search using embeddings.
        Only called if embeddings are available.
        """
        # Get query embedding
        query_embedding = self.embedding_service.embed_text(query)

        # Get all chunks (with filters)
        query_obj = db.query(TextChunk)

        if class_id:
            query_obj = query_obj.filter(TextChunk.class_id == class_id)

        if assignment_id:
            query_obj = query_obj.filter(TextChunk.assignment_id == assignment_id)

        # Only get chunks with embeddings
        query_obj = query_obj.filter(TextChunk.embedding_vector.isnot(None))

        chunks = query_obj.all()

        # Calculate similarities
        scored_chunks = []
        for chunk in chunks:
            try:
                chunk_embedding = json.loads(chunk.embedding_vector)
                similarity = self.embedding_service.cosine_similarity(
                    query_embedding,
                    chunk_embedding
                )

                # Hybrid: combine semantic + keyword match
                keyword_score = self._calculate_relevance_score(chunk.content, query)
                combined_score = 0.7 * similarity + 0.3 * keyword_score

                scored_chunks.append((chunk, combined_score))
            except Exception as e:
                print(f"Error scoring chunk {chunk.id}: {e}")
                continue

        # Sort by score
        scored_chunks.sort(key=lambda x: x[1], reverse=True)

        # Format results
        results = []
        for chunk, score in scored_chunks[:limit]:
            artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()
            snippet = self._generate_snippet(chunk.content, query)

            results.append({
                'chunk_id': chunk.id,
                'content': chunk.content,
                'snippet': snippet,
                'score': score,
                'artifact_filename': artifact.original_filename if artifact else None,
                'artifact_id': chunk.artifact_id,
                'section_title': chunk.section_title,
                'page_number': chunk.page_number,
                'class_id': chunk.class_id,
                'assignment_id': chunk.assignment_id,
                'search_method': 'semantic'
            })

        return results

    def _generate_snippet(self, content: str, query: str, context_chars: int = 150) -> str:
        """
        Generate a snippet showing query context.
        Returns text fragment with query highlighted.
        """
        query_lower = query.lower()
        content_lower = content.lower()

        # Find first occurrence
        idx = content_lower.find(query_lower)

        if idx == -1:
            # Query not found (semantic match), return first N chars
            return content[:context_chars * 2] + "..."

        # Extract context
        start = max(0, idx - context_chars)
        end = min(len(content), idx + len(query) + context_chars)

        snippet = content[start:end]

        # Add ellipsis
        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """
        Simple keyword-based relevance score.
        Returns 0.0 to 1.0.
        """
        content_lower = content.lower()
        query_lower = query.lower()

        # Count query term occurrences
        query_terms = query_lower.split()
        matches = sum(content_lower.count(term) for term in query_terms)

        # Normalize by content length
        words_in_content = len(content_lower.split())
        if words_in_content == 0:
            return 0.0

        # Score: matches per 100 words
        score = min(1.0, matches / (words_in_content / 100))

        return score

    def get_chunk_with_context(
        self,
        chunk_id: int,
        context_chunks: int = 1,
        db: Session = None
    ) -> Dict:
        """
        Get a chunk with surrounding context.
        Used when user clicks a search result.
        """
        chunk = db.query(TextChunk).filter(TextChunk.id == chunk_id).first()
        if not chunk:
            return None

        # Get surrounding chunks
        all_chunks = db.query(TextChunk).filter(
            TextChunk.extracted_text_id == chunk.extracted_text_id
        ).order_by(TextChunk.chunk_index).all()

        # Find current position
        current_idx = next((i for i, c in enumerate(all_chunks) if c.id == chunk_id), None)
        if current_idx is None:
            return None

        # Get context
        prev_start = max(0, current_idx - context_chunks)
        next_end = min(len(all_chunks), current_idx + context_chunks + 1)

        previous_chunks = [
            {'content': c.content, 'section_title': c.section_title}
            for c in all_chunks[prev_start:current_idx]
        ]

        next_chunks = [
            {'content': c.content, 'section_title': c.section_title}
            for c in all_chunks[current_idx + 1:next_end]
        ]

        # Get artifact
        artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()

        return {
            'chunk': {
                'id': chunk.id,
                'content': chunk.content,
                'section_title': chunk.section_title,
                'page_number': chunk.page_number,
                'chunk_index': chunk.chunk_index
            },
            'previous_chunks': previous_chunks,
            'next_chunks': next_chunks,
            'artifact': {
                'id': artifact.id,
                'filename': artifact.original_filename,
                'file_type': artifact.file_type
            } if artifact else None,
            'metadata': {
                'total_chunks': len(all_chunks),
                'current_position': current_idx + 1
            }
        }
