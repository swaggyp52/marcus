"""
Service for managing Answer Contracts: claims, support, and verification.
"""

from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from ..core.models import Plan, Claim, ClaimSupport, ClaimVerification, Artifact, ExtractedText
import json
import re


class ClaimService:
    """
    Handles creation, linking, and verification of claims.
    Implements the Answer Contracts model for trustworthy outputs.
    """

    def extract_claims_from_plan(self, plan: Plan, db: Session) -> List[Claim]:
        """
        Extract atomic claims from a plan's steps, assumptions, and risks.
        Each claim is a verifiable statement.
        """
        claims = []

        # Parse steps
        if plan.steps:
            try:
                steps = json.loads(plan.steps)
                for step in steps:
                    if isinstance(step, dict) and 'description' in step:
                        # Extract factual claims from step descriptions
                        step_claims = self._extract_claims_from_text(
                            step['description'],
                            confidence="medium"
                        )
                        claims.extend(step_claims)
            except json.JSONDecodeError:
                pass

        # Parse assumptions (these are lower confidence claims)
        if plan.assumptions:
            assumption_claims = self._extract_claims_from_text(
                plan.assumptions,
                confidence="low"
            )
            claims.extend(assumption_claims)

        # Create claim objects
        claim_objects = []
        for claim_text in claims:
            claim = Claim(
                plan_id=plan.id,
                statement=claim_text['statement'],
                confidence=claim_text['confidence'],
                verification_status="unverified"
            )
            db.add(claim)
            claim_objects.append(claim)

        db.commit()
        return claim_objects

    def _extract_claims_from_text(self, text: str, confidence: str) -> List[Dict]:
        """
        Simple claim extraction: split by sentences, filter for factual statements.
        In v0.3, this will use NLP for better extraction.
        """
        claims = []

        # Split into sentences (basic version)
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if len(sentence) < 10:  # Skip very short fragments
                continue

            # Filter out questions and commands
            if sentence.endswith('?'):
                continue
            if sentence.lower().startswith(('if ', 'when ', 'should ')):
                continue

            # This is a potential claim
            claims.append({
                'statement': sentence,
                'confidence': confidence
            })

        return claims

    def link_claim_to_source(
        self,
        claim_id: int,
        artifact_id: int,
        extracted_text_id: Optional[int],
        quote: str,
        page_number: Optional[int],
        section_title: Optional[str],
        relevance_score: int,
        db: Session
    ) -> ClaimSupport:
        """
        Create a citation link between a claim and source material.
        """
        support = ClaimSupport(
            claim_id=claim_id,
            artifact_id=artifact_id,
            extracted_text_id=extracted_text_id,
            quote=quote,
            page_number=page_number,
            section_title=section_title,
            relevance_score=relevance_score
        )
        db.add(support)
        db.commit()
        db.refresh(support)
        return support

    def verify_claim(
        self,
        claim_id: int,
        verification_result: str,
        verification_method: Optional[str],
        notes: Optional[str],
        db: Session
    ) -> ClaimVerification:
        """
        Record user verification of a claim.
        Updates claim verification status.
        """
        verification = ClaimVerification(
            claim_id=claim_id,
            verification_result=verification_result,
            verification_method=verification_method,
            notes=notes
        )
        db.add(verification)

        # Update claim status
        claim = db.query(Claim).filter(Claim.id == claim_id).first()
        if claim:
            claim.verification_status = verification_result
            from datetime import datetime
            claim.verified_at = datetime.utcnow()

        db.commit()
        db.refresh(verification)
        return verification

    def find_supporting_evidence(
        self,
        claim: Claim,
        assignment_artifacts: List[Artifact],
        db: Session
    ) -> List[Dict]:
        """
        Search through assignment artifacts for evidence supporting a claim.
        Returns potential supporting quotes with relevance scores.

        In v0.3, this will use semantic search.
        For v0.2, we use simple keyword matching.
        """
        evidence = []

        # Extract keywords from claim
        keywords = self._extract_keywords(claim.statement)

        for artifact in assignment_artifacts:
            # Get extracted text
            extracted_texts = db.query(ExtractedText).filter(
                ExtractedText.artifact_id == artifact.id
            ).all()

            for extracted in extracted_texts:
                # Search for keywords in content
                content = extracted.content.lower()
                matches = []

                for keyword in keywords:
                    if keyword.lower() in content:
                        matches.append(keyword)

                if matches:
                    # Calculate simple relevance score
                    relevance = min(10, len(matches) * 2)

                    # Extract quote (context around first keyword)
                    first_keyword = matches[0]
                    idx = content.find(first_keyword.lower())
                    start = max(0, idx - 100)
                    end = min(len(content), idx + 100)
                    quote = extracted.content[start:end]

                    evidence.append({
                        'artifact_id': artifact.id,
                        'extracted_text_id': extracted.id,
                        'quote': quote,
                        'relevance_score': relevance,
                        'matches': matches
                    })

        # Sort by relevance
        evidence.sort(key=lambda x: x['relevance_score'], reverse=True)
        return evidence[:5]  # Top 5 matches

    def _extract_keywords(self, text: str) -> List[str]:
        """
        Extract important keywords from claim text.
        Simple version: remove stop words and short words.
        """
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at',
            'to', 'for', 'of', 'with', 'by', 'is', 'are', 'was', 'were'
        }

        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [
            word for word in words
            if len(word) > 3 and word not in stop_words
        ]

        return keywords

    def get_verification_suggestions(self, claim: Claim) -> List[Dict]:
        """
        Generate suggestions for how to verify a claim.
        Provides actionable steps for the user.
        """
        suggestions = []

        # Low confidence claims need more verification
        if claim.confidence == "low":
            suggestions.append({
                'method': 'cross_reference',
                'description': 'Find this information in multiple source documents',
                'estimated_time': '3-5 minutes'
            })

        # All claims can be manually checked
        suggestions.append({
            'method': 'manual_check',
            'description': 'Read the original source material directly',
            'estimated_time': '2 minutes'
        })

        # For technical claims, suggest calculation verification
        if any(word in claim.statement.lower() for word in ['calculate', 'formula', 'equation', 'result']):
            suggestions.append({
                'method': 'recalculate',
                'description': 'Perform the calculation yourself to verify',
                'estimated_time': '5-10 minutes'
            })

        # For factual claims, suggest external lookup
        if claim.confidence in ["low", "medium"]:
            suggestions.append({
                'method': 'external_lookup',
                'description': 'Verify against textbook or trusted reference',
                'estimated_time': '5 minutes'
            })

        return suggestions
