from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class EmailNormalizer(Normalizer):
    """
    Standardizes email addresses to lowercase and strips whitespaces.
    """

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Email must be a string value")
            
        cleaned = value.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise NormalizationException(f"Invalid email format: {value}")
            
        return cleaned
