from datetime import datetime
from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class DateNormalizer(Normalizer):
    """
    Normalizes raw date strings into ISO format YYYY-MM-DD.
    """

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Date must be a string value")
            
        cleaned = value.strip()
        # Try a few common formats for mock robustness
        for fmt in ("%Y-%m-%d", "%m/%d/%Y", "%Y/%m/%d", "%B %d, %Y", "%b %Y"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
                
        # If we can't parse it, but it looks like a valid year or word, pass it or raise exception
        if cleaned.isdigit() and len(cleaned) == 4:
            return f"{cleaned}-01-01"
            
        raise NormalizationException(f"Failed to parse date format: {value}")
