import re
from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class PhoneNormalizer(Normalizer):
    """
    Standardizes phone numbers to standard format (clean digits/E.164 approximation).
    """

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Phone number must be a string value")
        
        # Clean formatting characters
        cleaned = re.sub(r"[^\d+]", "", value)
        
        # Phase 1 simple validation check
        if len(cleaned) < 7:
            raise NormalizationException(f"Invalid phone number length: {value}")
            
        return cleaned
