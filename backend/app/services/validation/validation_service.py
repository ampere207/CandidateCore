from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.candidate_fragment import CandidateFragment

class ValidationService(ABC):
    """
    Service interface for running schema-level constraints on CandidateFragments.
    Allows capturing field-level validation reports.
    """

    @abstractmethod
    def validate_fragment(self, fragment: CandidateFragment) -> List[Dict[str, Any]]:
        """
        Performs validation checks against fields of a CandidateFragment.
        
        Args:
            fragment: The parsed and normalized CandidateFragment.
            
        Returns:
            List[Dict[str, Any]]: A list of field-level errors, where each error is represented by:
                {
                    "field": str,
                    "error_type": str,
                    "message": str,
                    "critical": bool
                }
        """
        pass

class SimpleValidationService(ValidationService):
    """
    Mock implementation of the ValidationService for Phase 1 structure.
    """
    def validate_fragment(self, fragment: CandidateFragment) -> List[Dict[str, Any]]:
        errors = []
        # Basic mock rules
        if not fragment.emails and not fragment.phones:
            errors.append({
                "field": "contact",
                "error_type": "missing_contact",
                "message": "Both email and phone lists are empty",
                "critical": False
            })
        return errors
