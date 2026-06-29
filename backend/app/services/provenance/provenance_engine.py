from abc import ABC, abstractmethod
from typing import Any
from app.models.provenance import ProvenanceMetadata
from app.models.candidate_fragment import CandidateFragment

class ProvenanceEngine(ABC):
    """
    Interface for tracking data origin lineage for each canonical attribute.
    """

    @abstractmethod
    def create_provenance(self, field_name: str, raw_value: Any, fragment: CandidateFragment) -> ProvenanceMetadata:
        """
        Derives ProvenanceMetadata for a normalized field back to its source fragment.
        """
        pass

class DefaultProvenanceEngine(ProvenanceEngine):
    """
    Mock implementation of ProvenanceEngine for Phase 1.
    """

    def create_provenance(self, field_name: str, raw_value: Any, fragment: CandidateFragment) -> ProvenanceMetadata:
        return ProvenanceMetadata(
            source_id=fragment.source_id,
            source_type=fragment.source_type,
            raw_value=raw_value,
            extractor_version="1.0.0"
        )
