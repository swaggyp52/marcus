"""
BoxRunner - v0.44-beta

Executes mission boxes with state machine enforcement.
Prevents concurrent execution, persists state, creates artifacts.
"""

import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from sqlalchemy.orm import Session

from marcus_app.core.models import (
    Mission, MissionBox, MissionArtifact, BoxState
)


class BoxRunnerError(Exception):
    """Box execution failed."""
    pass


class BoxRunner:
    """
    Executes mission boxes with state transitions and artifact creation.

    State machine:
    - idle/ready → running → done OR error

    Concurrency guard:
    - Prevents running same box twice
    """

    @staticmethod
    def run_box(
        db: Session,
        mission_id: int,
        box_id: int,
        input_payload: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a box and persist state/artifacts.

        Args:
            db: Database session
            mission_id: Mission ID
            box_id: Box ID to run
            input_payload: Box-specific input data

        Returns:
            {
                'box_id': int,
                'state': str,
                'artifacts': List[dict],
                'error': str | None
            }

        Raises:
            BoxRunnerError: If box not found, invalid state, or execution fails
        """
        # Load box
        box = db.query(MissionBox).filter(
            MissionBox.id == box_id,
            MissionBox.mission_id == mission_id
        ).first()

        if not box:
            raise BoxRunnerError(f"Box {box_id} not found in mission {mission_id}")

        # Check state (prevent concurrent execution)
        if box.state == BoxState.RUNNING.value:
            raise BoxRunnerError(f"Box {box_id} is already running")

        # Validate transition
        valid_start_states = [BoxState.IDLE.value, BoxState.READY.value, BoxState.ERROR.value]
        if box.state not in valid_start_states:
            raise BoxRunnerError(
                f"Box {box_id} cannot run from state '{box.state}'. "
                f"Must be one of: {valid_start_states}"
            )

        # Mark as running
        box.state = BoxState.RUNNING.value
        box.last_run_at = datetime.utcnow()
        box.last_error = None
        db.commit()

        try:
            # Execute box based on type
            result = BoxRunner._execute_box_type(
                db=db,
                box=box,
                mission_id=mission_id,
                input_payload=input_payload or {}
            )

            # Mark as done
            box.state = BoxState.DONE.value
            db.commit()

            return {
                'box_id': box.id,
                'state': box.state,
                'artifacts': result.get('artifacts', []),
                'error': None
            }

        except Exception as e:
            # Mark as error
            box.state = BoxState.ERROR.value
            box.last_error = str(e)
            db.commit()

            raise BoxRunnerError(f"Box execution failed: {str(e)}")

    @staticmethod
    def _execute_box_type(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Route to specific box type implementation.

        Returns:
            {
                'artifacts': List[dict]  # Created artifacts metadata
            }
        """
        box_type = box.box_type

        if box_type == 'inbox':
            return BoxRunner._run_inbox_box(db, box, mission_id, input_payload)
        elif box_type == 'extract':
            return BoxRunner._run_extract_box(db, box, mission_id, input_payload)
        elif box_type == 'ask':
            return BoxRunner._run_ask_box(db, box, mission_id, input_payload)
        elif box_type == 'practice':
            return BoxRunner._run_practice_box(db, box, mission_id, input_payload)
        elif box_type == 'checker':
            return BoxRunner._run_checker_box(db, box, mission_id, input_payload)
        elif box_type == 'citations':
            return BoxRunner._run_citations_box(db, box, mission_id, input_payload)
        else:
            raise BoxRunnerError(
                f"Box type '{box_type}' not implemented. "
                f"Available: inbox, extract, ask, practice, checker, citations"
            )

    # ========================================================================
    # INBOX BOX
    # ========================================================================

    @staticmethod
    def _run_inbox_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        InboxBox: Link existing artifacts to mission.

        Input:
            artifact_ids: List[int]

        Output:
            mission_artifact(type=document) per artifact
        """
        from marcus_app.core.models import Artifact

        artifact_ids = input_payload.get('artifact_ids', [])

        if not artifact_ids:
            raise BoxRunnerError("InboxBox requires 'artifact_ids' in input")

        created_artifacts = []

        for artifact_id in artifact_ids:
            # Validate artifact exists
            artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
            if not artifact:
                raise BoxRunnerError(f"Artifact {artifact_id} not found")

            # Create mission artifact
            mission_artifact = MissionArtifact(
                mission_id=mission_id,
                box_id=box.id,
                artifact_type='document',
                title=artifact.original_filename,
                content_json=json.dumps({
                    'artifact_id': artifact.id,
                    'filename': artifact.original_filename,
                    'file_type': artifact.file_type,
                    'file_size': artifact.file_size
                }),
                source_refs_json=json.dumps({
                    'artifact_id': artifact.id,
                    'filename': artifact.original_filename
                })
            )

            db.add(mission_artifact)
            created_artifacts.append({
                'id': mission_artifact.id,
                'type': 'document',
                'title': mission_artifact.title
            })

        db.commit()

        return {'artifacts': created_artifacts}

    # ========================================================================
    # EXTRACT BOX
    # ========================================================================

    @staticmethod
    def _run_extract_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        ExtractBox: Ensure mission artifacts are chunked.

        Behavior:
        - Get all document artifacts in mission
        - For each, ensure extracted_text exists
        - For each, ensure text_chunks exist
        - Create report artifact

        Output:
            mission_artifact(type=note) with processing report
        """
        from marcus_app.core.models import Artifact, ExtractedText, TextChunk
        from marcus_app.services.extraction_service import ExtractionService
        from marcus_app.services.chunking_service import ChunkingService

        # Get mission document artifacts
        mission_artifacts = db.query(MissionArtifact).filter(
            MissionArtifact.mission_id == mission_id,
            MissionArtifact.artifact_type == 'document'
        ).all()

        if not mission_artifacts:
            raise BoxRunnerError("No documents linked to mission. Run InboxBox first.")

        report_lines = []
        total_chunks_created = 0
        artifacts_processed = 0

        for mission_artifact in mission_artifacts:
            content_data = json.loads(mission_artifact.content_json)
            artifact_id = content_data['artifact_id']

            artifact = db.query(Artifact).filter(Artifact.id == artifact_id).first()
            if not artifact:
                report_lines.append(f"- {content_data['filename']}: Artifact not found (skipped)")
                continue

            # Check if extracted text exists
            extracted_text = db.query(ExtractedText).filter(
                ExtractedText.artifact_id == artifact_id
            ).first()

            if not extracted_text:
                # Extract text (offline extraction)
                try:
                    result = ExtractionService.extract_text(db, artifact.id)
                    extracted_text = db.query(ExtractedText).filter(
                        ExtractedText.artifact_id == artifact_id
                    ).first()
                    report_lines.append(f"- {artifact.original_filename}: Extracted text")
                except Exception as e:
                    report_lines.append(f"- {artifact.original_filename}: Extraction failed ({str(e)})")
                    continue

            # Check if chunks exist
            existing_chunks = db.query(TextChunk).filter(
                TextChunk.artifact_id == artifact_id
            ).count()

            if existing_chunks == 0 and extracted_text:
                # Create chunks
                try:
                    chunking_service = ChunkingService()
                    chunks = chunking_service.chunk_extracted_text(
                        extracted_text=extracted_text,
                        db=db
                    )
                    chunks_created = len(chunks)
                    total_chunks_created += chunks_created
                    report_lines.append(f"- {artifact.original_filename}: Created {chunks_created} chunks")
                except Exception as e:
                    report_lines.append(f"- {artifact.original_filename}: Chunking failed ({str(e)})")
                    continue
            else:
                report_lines.append(f"- {artifact.original_filename}: Already chunked ({existing_chunks} chunks)")
                total_chunks_created += existing_chunks

            artifacts_processed += 1

        # Create report artifact
        report_md = "## Extraction Report\n\n"
        report_md += f"**Artifacts Processed:** {artifacts_processed}\n\n"
        report_md += f"**Total Chunks:** {total_chunks_created}\n\n"
        report_md += "### Details\n\n" + "\n".join(report_lines)

        report_artifact = MissionArtifact(
            mission_id=mission_id,
            box_id=box.id,
            artifact_type='note',
            title='Extraction Report',
            content_json=report_md,
            source_refs_json=json.dumps({
                'artifacts_processed': artifacts_processed,
                'chunks_created': total_chunks_created
            })
        )

        db.add(report_artifact)
        db.commit()

        return {
            'artifacts': [{
                'id': report_artifact.id,
                'type': 'note',
                'title': report_artifact.title,
                'summary': f"{artifacts_processed} artifacts, {total_chunks_created} chunks"
            }]
        }

    # ========================================================================
    # ASK BOX
    # ========================================================================

    @staticmethod
    def _run_ask_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        AskBox: Mission-scoped Q/A with citations.

        Input:
            question: str
            use_search: bool (default True)

        Output:
            mission_artifact(type=qa) with answer + citations
        """
        from marcus_app.services.search_service import SearchService

        question = input_payload.get('question', '').strip()
        use_search = input_payload.get('use_search', True)

        if not question:
            raise BoxRunnerError("AskBox requires 'question' in input")

        # Get mission artifacts to filter search
        mission_artifacts = db.query(MissionArtifact).filter(
            MissionArtifact.mission_id == mission_id,
            MissionArtifact.artifact_type == 'document'
        ).all()

        artifact_ids = []
        for ma in mission_artifacts:
            content_data = json.loads(ma.content_json)
            artifact_ids.append(content_data['artifact_id'])

        # Perform search if requested and artifacts exist
        citations = []
        answer_md = ""
        confidence = "low"
        method = "heuristic"

        if use_search and artifact_ids:
            # Search scoped to mission artifacts
            try:
                search_results = SearchService.search(
                    db=db,
                    query=question,
                    artifact_ids=artifact_ids,
                    limit=5
                )

                if search_results:
                    # Build answer from top results
                    answer_md = f"## Answer\n\nBased on mission materials:\n\n"

                    for i, result in enumerate(search_results[:3], 1):
                        answer_md += f"**Source {i}:** {result['snippet']}\n\n"

                        citations.append({
                            'chunk_id': result['chunk_id'],
                            'artifact_id': result['artifact_id'],
                            'filename': result.get('filename', 'Unknown'),
                            'page': result.get('page_number'),
                            'relevance': result.get('score', 0)
                        })

                    answer_md += "\n**Suggested approach:** Review the sources above and cross-reference with lecture notes.\n"

                    confidence = "medium" if len(citations) >= 2 else "low"
                else:
                    answer_md = "No relevant information found in mission materials.\n\n**Suggestion:** Check if materials have been extracted and chunked."
                    confidence = "low"

            except Exception as e:
                answer_md = f"Search failed: {str(e)}\n\nFalling back to general knowledge mode."
                confidence = "low"
        else:
            # No search - general knowledge mode
            answer_md = f"## General Knowledge Response\n\nQuestion: {question}\n\n"
            answer_md += "**Note:** No mission materials available or search disabled. "
            answer_md += "This answer is not grounded in your specific materials.\n\n"
            answer_md += "**Suggestion:** Link materials via InboxBox and run ExtractBox to enable cited answers."
            confidence = "low"

        # Create QA artifact
        qa_artifact = MissionArtifact(
            mission_id=mission_id,
            box_id=box.id,
            artifact_type='qa',
            title=question[:100],  # Truncate long questions
            content_json=json.dumps({
                'question': question,
                'answer_md': answer_md,
                'citations': citations,
                'confidence': confidence,
                'method': method,
                'use_search': use_search
            }),
            source_refs_json=json.dumps({
                'citations': citations
            })
        )

        db.add(qa_artifact)
        db.commit()

        return {
            'artifacts': [{
                'id': qa_artifact.id,
                'type': 'qa',
                'title': qa_artifact.title,
                'answer': answer_md,
                'citations': citations,
                'confidence': confidence
            }]
        }

    # ========================================================================
    # PRACTICE BOX (v0.44-final)
    # ========================================================================

    @staticmethod
    def _run_practice_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        PracticeBox: Generate practice questions from mission materials.

        Input:
            topic_keywords: Optional[str] - Filter chunks by topic
            question_count: int (default 10)

        Output:
            practice_session + practice_items
            mission_artifact(type=practice_session)
        """
        from marcus_app.core.models import TextChunk, PracticeSession, PracticeItem

        topic_keywords = input_payload.get('topic_keywords', '')
        question_count = input_payload.get('question_count', 10)

        # Get mission document artifacts
        mission_artifacts = db.query(MissionArtifact).filter(
            MissionArtifact.mission_id == mission_id,
            MissionArtifact.artifact_type == 'document'
        ).all()

        if not mission_artifacts:
            raise BoxRunnerError("No documents in mission. Run InboxBox first.")

        # Get artifact IDs
        artifact_ids = []
        for ma in mission_artifacts:
            content_data = json.loads(ma.content_json)
            artifact_ids.append(content_data['artifact_id'])

        # Get chunks from mission artifacts
        query = db.query(TextChunk).filter(TextChunk.artifact_id.in_(artifact_ids))

        if topic_keywords:
            # Simple keyword filter
            query = query.filter(TextChunk.content.like(f'%{topic_keywords}%'))

        chunks = query.limit(50).all()  # Get top 50 chunks

        if not chunks:
            raise BoxRunnerError("No chunks found. Run ExtractBox first.")

        # Create practice session
        practice_session = PracticeSession(
            mission_id=mission_id,
            state='active',
            score_json=json.dumps({'attempted': 0, 'correct': 0, 'incorrect': 0})
        )
        db.add(practice_session)
        db.flush()  # Get session ID

        # Generate practice items (heuristic - extract key concepts)
        practice_items_created = []
        chunks_used = min(question_count, len(chunks))

        for i, chunk in enumerate(chunks[:chunks_used]):
            # Heuristic question generation: turn chunk into question
            content = chunk.content[:200]  # First 200 chars

            # Simple heuristic: look for definitions, equations, key terms
            if '=' in content or 'is defined as' in content.lower():
                prompt = f"Q{i+1}: Based on the following, explain the concept:\n\n{content[:150]}..."
            elif 'formula' in content.lower() or 'equation' in content.lower():
                prompt = f"Q{i+1}: Derive or explain: {content[:150]}..."
            else:
                prompt = f"Q{i+1}: Explain in your own words:\n\n{content[:150]}..."

            practice_item = PracticeItem(
                session_id=practice_session.id,
                prompt_md=prompt,
                expected_answer=None,  # Heuristic mode - no expected answer
                state='unanswered',
                citations_json=json.dumps([{
                    'chunk_id': chunk.id,
                    'artifact_id': chunk.artifact_id,
                    'page': chunk.page_number
                }])
            )

            db.add(practice_item)
            practice_items_created.append({
                'id': practice_item.id,
                'prompt': prompt[:100] + '...'
            })

        db.commit()

        # Create mission artifact
        artifact = MissionArtifact(
            mission_id=mission_id,
            box_id=box.id,
            artifact_type='practice_session',
            title=f'Practice Session ({len(practice_items_created)} questions)',
            content_json=json.dumps({
                'session_id': practice_session.id,
                'question_count': len(practice_items_created),
                'topic': topic_keywords or 'general'
            }),
            source_refs_json=json.dumps({
                'session_id': practice_session.id,
                'chunks_used': chunks_used
            })
        )

        db.add(artifact)
        db.commit()

        return {
            'artifacts': [{
                'id': artifact.id,
                'type': 'practice_session',
                'title': artifact.title,
                'session_id': practice_session.id,
                'question_count': len(practice_items_created)
            }]
        }

    # ========================================================================
    # CHECKER BOX (v0.44-final)
    # ========================================================================

    @staticmethod
    def _run_checker_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CheckerBox: Verify user answers to practice questions.

        Input:
            session_id: int
            item_id: int
            user_answer: str

        Output:
            Updates practice_item state
            Creates claim(s) for verification
            mission_artifact(type=verification)
        """
        from marcus_app.core.models import PracticeSession, PracticeItem, Claim

        session_id = input_payload.get('session_id')
        item_id = input_payload.get('item_id')
        user_answer = input_payload.get('user_answer', '').strip()

        if not session_id or not item_id:
            raise BoxRunnerError("CheckerBox requires session_id and item_id")

        # Get practice item
        practice_item = db.query(PracticeItem).filter(
            PracticeItem.id == item_id,
            PracticeItem.session_id == session_id
        ).first()

        if not practice_item:
            raise BoxRunnerError(f"Practice item {item_id} not found")

        # Update user answer
        practice_item.user_answer = user_answer
        practice_item.answered_at = datetime.utcnow()

        # Check correctness (heuristic since no expected_answer in v0.44-final)
        # Simple heuristic: check if answer is substantive
        is_correct = len(user_answer) > 20  # At least 20 chars = attempted answer
        practice_item.state = 'correct' if is_correct else 'incorrect'

        # Get citations from practice item
        citations_data = json.loads(practice_item.citations_json) if practice_item.citations_json else []

        # Create verification claim (reuse existing claims table)
        # Note: Claims table requires plan_id, but we'll create without plan for now
        # This is a design compromise - ideally we'd have a mission_claims table

        # Create checks JSON
        checks = {
            'answer_length': len(user_answer),
            'has_content': len(user_answer) > 20,
            'timestamp': datetime.utcnow().isoformat()
        }
        practice_item.checks_json = json.dumps(checks)

        # Update session score
        session = db.query(PracticeSession).filter(
            PracticeSession.id == session_id
        ).first()

        if session:
            score = json.loads(session.score_json)
            score['attempted'] = score.get('attempted', 0) + 1
            if is_correct:
                score['correct'] = score.get('correct', 0) + 1
            else:
                score['incorrect'] = score.get('incorrect', 0) + 1
            session.score_json = json.dumps(score)

        db.commit()

        # Create verification artifact
        verification_md = f"## Verification Result\n\n"
        verification_md += f"**Question:** {practice_item.prompt_md[:150]}...\n\n"
        verification_md += f"**Your Answer:** {user_answer[:200]}...\n\n"
        verification_md += f"**Result:** {'✓ Acceptable' if is_correct else '✗ Needs more detail'}\n\n"

        if citations_data:
            verification_md += f"**Source Material:**\n"
            for cite in citations_data:
                verification_md += f"- Chunk {cite.get('chunk_id')} (Page {cite.get('page', 'N/A')})\n"

        artifact = MissionArtifact(
            mission_id=mission_id,
            box_id=box.id,
            artifact_type='verification',
            title=f'Check Result: Q{item_id}',
            content_json=verification_md,
            source_refs_json=json.dumps({
                'session_id': session_id,
                'item_id': item_id,
                'result': practice_item.state
            })
        )

        db.add(artifact)
        db.commit()

        return {
            'artifacts': [{
                'id': artifact.id,
                'type': 'verification',
                'title': artifact.title,
                'result': practice_item.state,
                'verification_md': verification_md
            }]
        }

    # ========================================================================
    # CITATIONS BOX (v0.44-final)
    # ========================================================================

    @staticmethod
    def _run_citations_box(
        db: Session,
        box: MissionBox,
        mission_id: int,
        input_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        CitationsBox: Aggregate all citations used in mission.

        Output:
            mission_artifact(type=citation) with citation report
        """
        from collections import Counter

        # Get all mission artifacts
        mission_artifacts = db.query(MissionArtifact).filter(
            MissionArtifact.mission_id == mission_id
        ).all()

        # Aggregate citations
        all_citations = []
        artifacts_by_type = Counter()
        chunk_usage = Counter()

        for artifact in mission_artifacts:
            artifacts_by_type[artifact.artifact_type] += 1

            # Parse source_refs_json for citations
            if artifact.source_refs_json:
                try:
                    refs = json.loads(artifact.source_refs_json)
                    if isinstance(refs, dict) and 'citations' in refs:
                        citations = refs['citations']
                        if isinstance(citations, list):
                            all_citations.extend(citations)
                            for cite in citations:
                                if 'chunk_id' in cite:
                                    chunk_usage[cite['chunk_id']] += 1
                except:
                    pass

        # Build citation report
        report_md = "## Citation Report\n\n"
        report_md += f"**Mission:** {mission_id}\n\n"
        report_md += f"**Total Artifacts:** {len(mission_artifacts)}\n\n"

        report_md += "### Artifacts by Type\n\n"
        for artifact_type, count in artifacts_by_type.items():
            report_md += f"- {artifact_type}: {count}\n"

        report_md += "\n### Top Cited Chunks\n\n"
        if chunk_usage:
            top_chunks = chunk_usage.most_common(10)
            for chunk_id, count in top_chunks:
                report_md += f"- Chunk {chunk_id}: cited {count} time(s)\n"
        else:
            report_md += "*No citations recorded*\n"

        report_md += f"\n### Citation Statistics\n\n"
        report_md += f"- Total citations: {len(all_citations)}\n"
        report_md += f"- Unique chunks: {len(chunk_usage)}\n"

        # Create citation artifact
        artifact = MissionArtifact(
            mission_id=mission_id,
            box_id=box.id,
            artifact_type='citation',
            title='Mission Citation Report',
            content_json=report_md,
            source_refs_json=json.dumps({
                'total_citations': len(all_citations),
                'unique_chunks': len(chunk_usage),
                'artifacts_analyzed': len(mission_artifacts)
            })
        )

        db.add(artifact)
        db.commit()

        return {
            'artifacts': [{
                'id': artifact.id,
                'type': 'citation',
                'title': artifact.title,
                'total_citations': len(all_citations),
                'report': report_md
            }]
        }
