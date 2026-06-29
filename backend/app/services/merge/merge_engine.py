import uuid
from abc import ABC, abstractmethod
from typing import List, Optional
from datetime import datetime, timezone
from app.models.candidate_fragment import CandidateFragment
from app.models.canonical_candidate import CanonicalCandidate, CanonicalField
from app.models.field_metadata import FieldMetadata
from app.models.provenance import ProvenanceMetadata
from app.models.confidence import ConfidenceMetadata
from app.services.merge.conflict_resolver import ConflictResolver, SourcePriorityConflictResolver

class MergeEngine(ABC):
    """
    Interface for merging multiple CandidateFragments into a single CanonicalCandidate.
    """

    @abstractmethod
    def merge(self, fragments: List[CandidateFragment], candidate_id: Optional[str] = None) -> CanonicalCandidate:
        """
        Unifies fragments into a single CanonicalCandidate.
        
        Args:
            fragments: List of parsed and normalized CandidateFragments.
            candidate_id: Optional existing candidate ID to append to.
            
        Returns:
            CanonicalCandidate: The merged immutable profile.
        """
        pass

class DefaultMergeEngine(MergeEngine):
    """
    Mock implementation of MergeEngine utilizing SourcePriorityConflictResolver.
    """

    def __init__(self, resolver: Optional[ConflictResolver] = None):
        self.resolver = resolver or SourcePriorityConflictResolver()

    def merge(self, fragments: List[CandidateFragment], candidate_id: Optional[str] = None) -> CanonicalCandidate:
        if not fragments:
            raise ValueError("Cannot merge an empty list of candidate fragments")

        resolved_id = candidate_id or str(uuid.uuid4())
        
        # Phase 1 simple mock merging logic:
        # Group values for each field, map to FieldMetadata, and use ConflictResolver.
        first_names = []
        last_names = []
        emails_list = []
        phones_list = []
        locations = []
        skills_nested = []
        
        for frag in fragments:
            # Build basic FieldMetadata for each fragment's field
            prov = ProvenanceMetadata(
                source_id=frag.source_id,
                source_type=frag.source_type,
                extraction_timestamp=frag.extracted_at,
                raw_value=None,  # Or original field value
                extractor_version="1.0.0"
            )
            conf = ConfidenceMetadata(
                score=1.0 if frag.source_type == "ats_json" else 0.8,
                confidence_method="source_type_default",
                assessment_details={"default": True}
            )
            meta = FieldMetadata(provenance=prov, confidence=conf)

            if frag.first_name:
                first_names.append((frag.first_name, meta))
            if frag.last_name:
                last_names.append((frag.last_name, meta))
            if frag.emails:
                emails_list.append((frag.emails, meta))
            if frag.phones:
                phones_list.append((frag.phones, meta))
            if frag.location:
                locations.append((frag.location, meta))
            if frag.skills:
                skills_nested.append((frag.skills, meta))

        # Use resolver to determine winning fields
        resolved_fn, fn_meta = self.resolver.resolve(first_names) if first_names else ("Unknown", FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))
        resolved_ln, ln_meta = self.resolver.resolve(last_names) if last_names else ("Candidate", FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))
        
        # Email resolution: combine or choose winning
        resolved_emails, emails_meta = self.resolver.resolve(emails_list) if emails_list else ([], FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))

        # Phone resolution
        resolved_phones, phones_meta = self.resolver.resolve(phones_list) if phones_list else ([], FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))

        # Location resolution
        resolved_loc, loc_meta = self.resolver.resolve(locations) if locations else (None, FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))

        # Skills resolution: union list or choose winning.
        # Let's say we choose winning list of skills for Phase 1.
        resolved_skills, skills_meta = self.resolver.resolve(skills_nested) if skills_nested else ([], FieldMetadata(
            provenance=ProvenanceMetadata(source_id="system", source_type="default"),
            confidence=ConfidenceMetadata(score=0.0, confidence_method="none")
        ))

        return CanonicalCandidate(
            candidate_id=resolved_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            first_name=CanonicalField[str](
                value=resolved_fn,
                metadata=fn_meta,
                history=[m for _, m in first_names]
            ),
            last_name=CanonicalField[str](
                value=resolved_ln,
                metadata=ln_meta,
                history=[m for _, m in last_names]
            ),
            emails=CanonicalField[List[str]](
                value=resolved_emails,
                metadata=emails_meta,
                history=[m for _, m in emails_list]
            ),
            phones=CanonicalField[List[str]](
                value=resolved_phones,
                metadata=phones_meta,
                history=[m for _, m in phones_list]
            ),
            location=CanonicalField[str](
                value=resolved_loc,
                metadata=loc_meta,
                history=[m for _, m in locations]
            ) if resolved_loc else None,
            skills=CanonicalField[List[str]](
                value=resolved_skills,
                metadata=skills_meta,
                history=[m for _, m in skills_nested]
            )
        )
