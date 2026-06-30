import re
from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class CompanyNormalizer(Normalizer):
    """
    Standardizes company names by stripping corporate suffix entities (LLC, Inc, Corp, Ltd, etc.).
    """

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Company name value must be a string")
            
        cleaned = value.strip()
        if not cleaned:
            raise NormalizationException("Company name cannot be blank")

        # Case-insensitive word boundary regex stripping common suffixes
        suffix_pattern = r"\b(l\.?l\.?c\.?|inc\.?|corp\.?|co\.?|ltd\.?|incorporated|corporation|limited|gmbh)\b"
        normalized = re.sub(suffix_pattern, "", cleaned, flags=re.IGNORECASE)

        # Cleanup whitespace and comma leftovers
        normalized = re.sub(r"\s+", " ", normalized)
        normalized = normalized.strip(",. ")

        return normalized if normalized else cleaned
