from abc import ABC, abstractmethod
from typing import Any

class Normalizer(ABC):
    """
    Abstract interface for field normalizers.
    Standardizes fields like phone numbers, emails, skills, and dates into consistent structures.
    """

    @abstractmethod
    def normalize(self, value: Any) -> Any:
        """
        Standardizes a raw field value.
        
        Args:
            value: The field value to normalize.
            
        Returns:
            The normalized value in target standard format.
            
        Raises:
            NormalizationException: If normalization fails critically.
        """
        pass
