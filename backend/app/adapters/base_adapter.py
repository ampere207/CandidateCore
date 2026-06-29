from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.candidate_fragment import CandidateFragment

class BaseAdapter(ABC):
    """
    Abstract Base Class for all Candidate ingestion source adapters.
    Adapters are responsible for source recognition, raw parsing, initial schema validation, 
    and field normalization into CandidateFragments. 
    
    Adapters MUST NOT contain any cross-source merging, global confidence computation, or projection logic.
    """

    @abstractmethod
    def detect(self, raw_data: Any) -> bool:
        """
        Inspects the raw input to determine if this adapter can process it.
        
        Args:
            raw_data: The incoming raw payload (can be bytes, dict, or string).
            
        Returns:
            bool: True if the payload matches the adapter's capabilities, False otherwise.
        """
        pass

    @abstractmethod
    def parse(self, raw_data: Any) -> Dict[str, Any]:
        """
        Parses raw unstructured or structured input into an intermediate dictionary.
        
        Args:
            raw_data: Raw input data payload.
            
        Returns:
            Dict[str, Any]: A raw dictionary mapping candidate attributes.
            
        Raises:
            AdapterException: If parsing fails catastrophically.
        """
        pass

    @abstractmethod
    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        """
        Validates the intermediate structure according to source schema requirements.
        
        Args:
            raw_parsed: Dictionary output from parse().
            
        Returns:
            bool: True if valid, raises ValidationException otherwise.
        """
        pass

    @abstractmethod
    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        """
        Normalizes the intermediate dict fields and maps them into a typed CandidateFragment.
        This includes applying basic normalizations like format standardizations.
        
        Args:
            raw_parsed: Dictionary output from parse().
            source_id: Unique string reference for this ingestion run.
            
        Returns:
            CandidateFragment: The normalized and strongly typed data fragment.
        """
        pass
