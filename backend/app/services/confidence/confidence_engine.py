from abc import ABC, abstractmethod
from typing import Any, Dict, List
from app.models.confidence import ConfidenceMetadata
from app.models.candidate_fragment import CandidateFragment

class ConfidenceEngine(ABC):
    """
    Interface for calculating field-level and overall profile confidence.
    """

    @abstractmethod
    def calculate_field_confidence(
        self, 
        field_name: str, 
        value: Any, 
        source_type: str, 
        has_validation_errors: bool,
        normalization_success: bool,
        agreement_count: int
    ) -> ConfidenceMetadata:
        """
        Computes a deterministic score between 0.0 and 1.0.
        """
        pass

    @abstractmethod
    def calculate_profile_completeness(self, first_name: str, last_name: str, emails: list, phones: list) -> float:
        """
        Measures structural profile content completeness.
        """
        pass

class DefaultConfidenceEngine(ConfidenceEngine):
    """
    Standard implementation of ConfidenceEngine.
    Uses source priority, validation logs, normalization outcomes, and consensus count.
    """
    
    SOURCE_BASE_RELIABILITY = {
        "ats_json": 0.95,
        "resume_pdf": 0.85,
        "recruiter_csv": 0.75,
        "recruiter_notes": 0.60
    }

    def calculate_field_confidence(
        self, 
        field_name: str, 
        value: Any, 
        source_type: str, 
        has_validation_errors: bool,
        normalization_success: bool,
        agreement_count: int
    ) -> ConfidenceMetadata:
        # 1. Base score from source type
        base_score = self.SOURCE_BASE_RELIABILITY.get(source_type, 0.50)
        
        # 2. Adjustments based on validation
        validation_penalty = 0.20 if has_validation_errors else 0.0
        
        # 3. Adjustments based on normalization
        normalization_bonus = 0.05 if normalization_success else -0.15
        
        # 4. Consensus agreement bonus (+0.10 for each matching source value)
        consensus_bonus = min(0.20, agreement_count * 0.10)
        
        # Calculate final aggregated score
        final_score = base_score - validation_penalty + normalization_bonus + consensus_bonus
        
        # Enforce boundary limits [0.0, 1.0]
        final_score = max(0.0, min(1.0, final_score))
        
        # Round to 2 decimal places for deterministic representation
        final_score = round(final_score, 2)
        
        details = {
            "base_reliability": base_score,
            "has_validation_warnings": has_validation_errors,
            "normalization_status": "success" if normalization_success else "fallback",
            "cross_source_agreements": agreement_count,
            "bonuses": {
                "normalization": normalization_bonus,
                "consensus": consensus_bonus
            },
            "penalties": {
                "validation": validation_penalty
            }
        }
        
        return ConfidenceMetadata(
            score=final_score,
            confidence_method="multi_factor_deterministic_v1",
            assessment_details=details
        )

    def calculate_profile_completeness(self, first_name: str, last_name: str, emails: list, phones: list) -> float:
        score = 0.0
        if first_name: score += 0.2
        if last_name: score += 0.2
        if emails and len(emails) > 0: score += 0.4
        if phones and len(phones) > 0: score += 0.2
        return round(score, 2)
