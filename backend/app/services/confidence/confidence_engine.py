from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.confidence import ConfidenceMetadata
from app.models.candidate_fragment import CandidateFragment

class ConfidenceEngine(ABC):
    """
    Interface for assessing reliability metrics and calculating field/profile confidence.
    """

    @abstractmethod
    def calculate_field_confidence(self, field_name: str, value: Any, fragment: CandidateFragment) -> ConfidenceMetadata:
        """
        Assesses confidence score for a single field extraction.
        """
        pass

    @abstractmethod
    def calculate_profile_completeness(self, first_name: str, last_name: str, emails: list, phones: list) -> float:
        """
        Calculates a completeness score for a candidate profile based on field presence.
        """
        pass

class DefaultConfidenceEngine(ConfidenceEngine):
    """
    Mock implementation of ConfidenceEngine for Phase 1.
    """

    def calculate_field_confidence(self, field_name: str, value: Any, fragment: CandidateFragment) -> ConfidenceMetadata:
        # Simple heuristic based on source type
        score = 0.5
        if fragment.source_type == "ats_json":
            score = 0.95
        elif fragment.source_type == "resume_pdf":
            score = 0.85
        elif fragment.source_type == "recruiter_csv":
            score = 0.70
            
        return ConfidenceMetadata(
            score=score,
            confidence_method="heuristic_by_source",
            assessment_details={"source_type": fragment.source_type, "field": field_name}
        )

    def calculate_profile_completeness(self, first_name: str, last_name: str, emails: list, phones: list) -> float:
        score = 0.0
        if first_name: score += 0.2
        if last_name: score += 0.2
        if emails: score += 0.4
        if phones: score += 0.2
        return score
