"""
Search service for Marcus v0.37.
FTS5-based search with query normalization and alias expansion.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text
import json
import re

from ..core.models import TextChunk, Artifact, Class, Assignment


class SearchService:
    """
    Production-grade search with FTS5 + BM25 ranking.

    Features:
    - FTS5 full-text search with BM25 ranking
    - Query normalization (lowercase, hyphens, punctuation)
    - Alias expansion (FSM → finite state machine)
    - Semantic search fallback (if embeddings available)
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
                print("[SearchService] Embeddings enabled (hybrid mode)")
            else:
                print("[SearchService] Using FTS5 only")
        except ImportError:
            print("[SearchService] Using FTS5 only")

    def normalize_query(self, query: str) -> str:
        """
        Normalize query for better matching.

        - Lowercase
        - Normalize hyphens (side-channel → side channel)
        - Collapse whitespace
        - Remove special chars (carefully)
        """
        # Lowercase
        normalized = query.lower()

        # Replace hyphens with spaces (helps with variations)
        normalized = normalized.replace('-', ' ')

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Strip leading/trailing whitespace
        normalized = normalized.strip()

        return normalized

    def expand_query_with_aliases(self, query: str, db: Session) -> List[str]:
        """
        Expand query with aliases.

        Returns list of query variants:
        - Original query
        - Aliases (if found)
        - Canonical forms (if found)
        """
        normalized = self.normalize_query(query)
        variants = [normalized]

        try:
            # Check for exact match (normalized query → canonical)
            sql_forward = """
                SELECT DISTINCT canonical_term
                FROM search_aliases
                WHERE term = :query
            """
            result = db.execute(text(sql_forward), {"query": normalized})
            for row in result:
                canonical = row[0]
                if canonical not in variants:
                    variants.append(canonical)
            
            # Check for reverse match (canonical → term)
            sql_reverse = """
                SELECT DISTINCT term
                FROM search_aliases
                WHERE canonical_term = :query
            """
            result = db.execute(text(sql_reverse), {"query": normalized})
            for row in result:
                term = row[0]
                if term not in variants:
                    variants.append(term)
            
            # Also check individual terms
            terms = normalized.split()
            for term in terms:
                sql_term_forward = """
                    SELECT DISTINCT canonical_term
                    FROM search_aliases
                    WHERE term = :term
                """
                result = db.execute(text(sql_term_forward), {"term": term})
                for row in result:
                    canonical = row[0]
                    if canonical not in variants:
                        variants.append(canonical)
                
                sql_term_reverse = """
                    SELECT DISTINCT term
                    FROM search_aliases
                    WHERE canonical_term = :term
                """
                result = db.execute(text(sql_term_reverse), {"term": term})
                for row in result:
                    found_term = row[0]
                    if found_term not in variants:
                        variants.append(found_term)
        except Exception:
            # Aliases table might not exist in older versions
            pass

        return variants

    def search(
        self,
        query: str,
        class_id: Optional[int] = None,
        assignment_id: Optional[int] = None,
        limit: int = 10,
        db: Session = None
    ) -> List[Dict]:
        """
        Search chunks with FTS5 + optional semantic search.
        """
        # Try FTS5 first (always available)
        fts_results = self._fts5_search(
            query, class_id, assignment_id, limit, db
        )

        # If semantic search available and FTS5 found few results, augment
        if self.embeddings_available and len(fts_results) < limit:
            try:
                semantic_results = self._semantic_search(
                    query, class_id, assignment_id, limit, db
                )

                # Merge results (deduplicate by chunk_id)
                seen_ids = {r['chunk_id'] for r in fts_results}
                for r in semantic_results:
                    if r['chunk_id'] not in seen_ids:
                        fts_results.append(r)
                        seen_ids.add(r['chunk_id'])

                # Re-sort by score
                fts_results.sort(key=lambda x: x['score'], reverse=True)
                fts_results = fts_results[:limit]
            except Exception as e:
                print(f"[SearchService] Semantic search failed: {e}")

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
        FTS5 full-text search with BM25 ranking.
        """
        # Normalize and expand query
        query_variants = self.expand_query_with_aliases(query, db)

        # Build FTS5 query - try multiple strategies
        # Strategy 1: Exact phrase match (highest priority)
        fts_queries = []
        for variant in query_variants:
            # Escape quotes
            escaped = variant.replace('"', '""')
            # Add phrase match (all terms together)
            fts_queries.append(f'"{escaped}"')
        
        # Strategy 2: Individual terms (AND - all terms must match)
        individual_terms = []
        for variant in query_variants:
            # Split into terms and create AND query
            terms = variant.split()
            if len(terms) > 1:
                # For multi-word queries, also add AND combination
                # Use parentheses to group: (term1 AND term2) OR (term3 AND term4)
                term_and = '(' + ' AND '.join(terms) + ')'
                individual_terms.append(term_and)
            else:
                # Single term - just add it
                individual_terms.append(terms[0])
        
        # Combine: try exact match OR individual terms
        # Wrap phrase matches in parens too
        phrase_group = '(' + ' OR '.join(fts_queries) + ')'
        if individual_terms:
            terms_group = ' OR '.join(individual_terms)
            fts_query = f'{phrase_group} OR {terms_group}'
        else:
            fts_query = phrase_group

        # Build SQL with FTS5
        sql_parts = ["""
            SELECT
                tc.id,
                tc.content,
                tc.section_title,
                tc.page_number,
                tc.artifact_id,
                tc.class_id,
                tc.assignment_id,
                text_chunks_fts.rank AS bm25_score
            FROM text_chunks tc
            JOIN text_chunks_fts ON tc.id = text_chunks_fts.rowid
            WHERE text_chunks_fts MATCH :fts_query
        """]

        params = {'fts_query': fts_query, 'limit': limit}

        # Add filters
        if class_id:
            sql_parts.append("AND tc.class_id = :class_id")
            params['class_id'] = class_id

        if assignment_id:
            sql_parts.append("AND tc.assignment_id = :assignment_id")
            params['assignment_id'] = assignment_id

        # Order by BM25 rank (lower is better in FTS5)
        sql_parts.append("ORDER BY text_chunks_fts.rank")
        sql_parts.append("LIMIT :limit")

        sql = " ".join(sql_parts)

        # Execute search
        try:
            result = db.execute(text(sql), params)
            rows = result.fetchall()
        except Exception as e:
            print(f"[SearchService] FTS5 search failed: {e}")
            # Fallback to LIKE search
            return self._fallback_like_search(query, class_id, assignment_id, limit, db)

        # Format results
        results = []
        for row in rows:
            chunk = db.query(TextChunk).filter(TextChunk.id == row[0]).first()
            if not chunk:
                continue

            # Get artifact info
            artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()

            # Generate snippet
            snippet = self._generate_snippet(chunk.content, query)

            # Convert BM25 rank to 0-1 score (lower rank = better)
            # BM25 ranks are negative, closer to 0 is better
            # Use exponential normalization to handle wide range of values
            bm25_rank = row[7]
            # Convert: rank -30 → score ~0.1, rank -1 → score ~0.9
            score = max(0.0, min(1.0, 1.0 / (1.0 + abs(bm25_rank))))  # Sigmoid-like

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
                'search_method': 'fts5'
            })

        return results

    def _fallback_like_search(
        self,
        query: str,
        class_id: Optional[int],
        assignment_id: Optional[int],
        limit: int,
        db: Session
    ) -> List[Dict]:
        """
        Fallback LIKE search if FTS5 fails.
        Uses query normalization and alias expansion.
        """
        query_variants = self.expand_query_with_aliases(query, db)

        # Build LIKE query (OR all variants)
        where_clauses = []
        params = {'limit': limit}

        for i, variant in enumerate(query_variants):
            param_name = f'pattern{i}'
            where_clauses.append(f"tc.content LIKE :{param_name}")
            params[param_name] = f"%{variant}%"

        # Add filters
        filter_clauses = []
        if class_id:
            filter_clauses.append("tc.class_id = :class_id")
            params['class_id'] = class_id

        if assignment_id:
            filter_clauses.append("tc.assignment_id = :assignment_id")
            params['assignment_id'] = assignment_id

        # Combine WHERE clauses
        all_where = []
        if where_clauses:
            all_where.append(f"({' OR '.join(where_clauses)})")
        if filter_clauses:
            all_where.extend(filter_clauses)

        sql = f"""
            SELECT tc.* FROM text_chunks tc
            WHERE {' AND '.join(all_where)}
            ORDER BY tc.word_count DESC
            LIMIT :limit
        """

        result = db.execute(text(sql), params)
        rows = result.fetchall()

        # Format results (similar to FTS5)
        results = []
        for row in rows:
            chunk = db.query(TextChunk).filter(TextChunk.id == row.id).first()
            if not chunk:
                continue

            artifact = db.query(Artifact).filter(Artifact.id == chunk.artifact_id).first()
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
                'search_method': 'like_fallback'
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
        Semantic search using embeddings (optional augmentation).
        """
        query_embedding = self.embedding_service.embed_text(query)

        query_obj = db.query(TextChunk)

        if class_id:
            query_obj = query_obj.filter(TextChunk.class_id == class_id)

        if assignment_id:
            query_obj = query_obj.filter(TextChunk.assignment_id == assignment_id)

        query_obj = query_obj.filter(TextChunk.embedding_vector.isnot(None))
        chunks = query_obj.all()

        scored_chunks = []
        for chunk in chunks:
            try:
                chunk_embedding = json.loads(chunk.embedding_vector)
                similarity = self.embedding_service.cosine_similarity(
                    query_embedding,
                    chunk_embedding
                )
                scored_chunks.append((chunk, similarity))
            except Exception:
                continue

        scored_chunks.sort(key=lambda x: x[1], reverse=True)

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
        """Generate snippet with query context."""
        # Normalize query for matching
        query_normalized = self.normalize_query(query)
        content_lower = content.lower()

        # Try to find normalized query
        idx = content_lower.find(query_normalized)

        # If not found, try individual terms
        if idx == -1:
            terms = query_normalized.split()
            for term in terms:
                idx = content_lower.find(term)
                if idx != -1:
                    break

        if idx == -1:
            return content[:context_chars * 2] + "..."

        start = max(0, idx - context_chars)
        end = min(len(content), idx + len(query_normalized) + context_chars)

        snippet = content[start:end]

        if start > 0:
            snippet = "..." + snippet
        if end < len(content):
            snippet = snippet + "..."

        return snippet

    def _calculate_relevance_score(self, content: str, query: str) -> float:
        """Simple keyword-based relevance score."""
        content_lower = content.lower()
        query_lower = self.normalize_query(query)

        query_terms = query_lower.split()
        matches = sum(content_lower.count(term) for term in query_terms)

        words_in_content = len(content_lower.split())
        if words_in_content == 0:
            return 0.0

        score = min(1.0, matches / (words_in_content / 100))
        return score

    def get_chunk_with_context(
        self,
        chunk_id: int,
        context_chunks: int = 1,
        db: Session = None
    ) -> Dict:
        """Get a chunk with surrounding context."""
        chunk = db.query(TextChunk).filter(TextChunk.id == chunk_id).first()
        if not chunk:
            return None

        all_chunks = db.query(TextChunk).filter(
            TextChunk.extracted_text_id == chunk.extracted_text_id
        ).order_by(TextChunk.chunk_index).all()

        current_idx = next((i for i, c in enumerate(all_chunks) if c.id == chunk_id), None)
        if current_idx is None:
            return None

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
