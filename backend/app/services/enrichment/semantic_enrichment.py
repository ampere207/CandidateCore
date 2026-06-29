from abc import ABC, abstractmethod
from typing import Dict, Any
from app.models.canonical_candidate import CanonicalCandidate

class SemanticEnrichmentEngine(ABC):
    """
    Interface for semantic profiling, e.g. taxonomy mappings, skill associations, or job-title classification.
    """

    @abstractmethod
    def enrich(self, candidate: CanonicalCandidate) -> CanonicalCandidate:
        """
        Enriches a CanonicalCandidate with semantic metadata tags.
        """
        pass

class DefaultSemanticEnrichmentEngine(SemanticEnrichmentEngine):
    """
    Mock implementation of SemanticEnrichmentEngine for Phase 1.
    """

    def enrich(self, candidate: CanonicalCandidate) -> CanonicalCandidate:
        # Phase 1: simple mock return with added run metadata
        updated_metadata = dict(candidate.metadata)
        updated_metadata["semantic_enrichment_applied"] = True
        updated_metadata["inferred_seniority"] = "Senior Engineer"
        
        # CanonicalCandidate is frozen, so return a new copy with modified metadata
        candidate_dict = candidate.model_dump()
        candidate_dict["metadata"] = updated_metadata
        
        return CanonicalCandidate(**candidate_dict)
