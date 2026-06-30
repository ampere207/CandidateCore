import re
from abc import ABC, abstractmethod
from typing import List, Dict, Any
from app.models.candidate_fragment import CandidateFragment

class ValidationService(ABC):
    """
    Service interface for running schema-level constraints on CandidateFragments.
    """

    @abstractmethod
    def validate_fragment(self, fragment: CandidateFragment) -> List[Dict[str, Any]]:
        pass

class SimpleValidationService(ValidationService):
    """
    Basic mock implementation of ValidationService.
    """
    def validate_fragment(self, fragment: CandidateFragment) -> List[Dict[str, Any]]:
        errors = []
        if not fragment.emails and not fragment.phones:
            errors.append({
                "field": "contact",
                "error_type": "missing_contact",
                "message": "Both email and phone lists are empty",
                "critical": False
            })
        return errors

class PipelineValidationService(ValidationService):
    """
    Production-grade implementation of ValidationService.
    Asserts check limits on candidate fields and reports detailed non-blocking warnings.
    """

    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$")
    PHONE_REGEX = re.compile(r"^\+?\d{7,15}$")
    DATE_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}$")
    URL_REGEX = re.compile(r"^https?://(?:www\.)?[-a-zA-Z0-9@:%._\+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b(?:[-a-zA-Z0-9()@:%_\+.~#?&//=]*)$")

    def validate_fragment(self, fragment: CandidateFragment) -> List[Dict[str, Any]]:
        warnings = []
        source_id = fragment.source_id

        # 1. Email Validations
        for email in fragment.emails:
            if not self.EMAIL_REGEX.match(email):
                warnings.append({
                    "source": source_id,
                    "field": "emails",
                    "error_type": "invalid_email_format",
                    "message": f"Email address '{email}' is formatted incorrectly",
                    "critical": False
                })

        # 2. Phone Validations
        for phone in fragment.phones:
            digits_only = re.sub(r"[^\d+]", "", phone)
            if not self.PHONE_REGEX.match(digits_only):
                warnings.append({
                    "source": source_id,
                    "field": "phones",
                    "error_type": "invalid_phone_format",
                    "message": f"Phone number '{phone}' does not meet standard length bounds",
                    "critical": False
                })

        # 3. Date Validations in experience or education
        for exp in fragment.experience:
            dates = exp.get("dates", "")
            parts = re.split(r"[-–to]+", dates)
            for part in parts:
                clean_part = part.strip().lower()
                if not clean_part or clean_part in ["present", "current"]:
                    continue
                if len(clean_part) == 10 and not self.DATE_REGEX.match(clean_part):
                    warnings.append({
                        "source": source_id,
                        "field": "experience.dates",
                        "error_type": "invalid_date_format",
                        "message": f"Experience date entry '{part}' is not in YYYY-MM-DD format",
                        "critical": False
                    })

        # 4. URL checks in raw data
        profile_url = fragment.raw_payload.get("linkedin_url") or fragment.raw_payload.get("github_url")
        if profile_url and not self.URL_REGEX.match(str(profile_url)):
            warnings.append({
                "source": source_id,
                "field": "linkedin_url",
                "error_type": "invalid_url_format",
                "message": f"URL '{profile_url}' is not a valid web URL format",
                "critical": False
            })

        # 5. Required identification check
        if not fragment.emails and not fragment.phones:
            warnings.append({
                "source": source_id,
                "field": "identity_attributes",
                "error_type": "missing_contact_details",
                "message": "Candidate fragment is missing both email and phone contact identifiers",
                "critical": True
            })

        return warnings
