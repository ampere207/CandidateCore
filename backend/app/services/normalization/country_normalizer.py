from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class CountryNormalizer(Normalizer):
    """
    Standardizes country names and abbreviations to full title strings.
    """
    
    COUNTRY_MAPPING = {
        "us": "United States",
        "usa": "United States",
        "united states of america": "United States",
        "u.s.a.": "United States",
        "uk": "United Kingdom",
        "gb": "United Kingdom",
        "united kingdom": "United Kingdom",
        "great britain": "United Kingdom",
        "in": "India",
        "india": "India",
        "ca": "Canada",
        "canada": "Canada",
        "de": "Germany",
        "deutschland": "Germany",
        "germany": "Germany",
        "fr": "France",
        "france": "France"
    }

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Country identifier must be a string")
            
        cleaned = value.strip().lower()
        if not cleaned:
            raise NormalizationException("Country name cannot be blank")

        return self.COUNTRY_MAPPING.get(cleaned, value.strip().title())
