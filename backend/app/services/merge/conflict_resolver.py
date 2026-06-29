from abc import ABC, abstractmethod
from typing import Any, List
from app.models.field_metadata import FieldMetadata

class ConflictResolver(ABC):
    """
    Interface for resolving value conflicts between candidate fragments.
    """

    @abstractmethod
    def resolve(self, values_with_metadata: List[tuple[Any, FieldMetadata]]) -> tuple[Any, FieldMetadata]:
        """
        Determines the winning value and its metadata from a set of candidate options.
        
        Args:
            values_with_metadata: A list of tuples containing (value, FieldMetadata).
            
        Returns:
            tuple[Any, FieldMetadata]: The selected winning value and its metadata.
        """
        pass

class SourcePriorityConflictResolver(ConflictResolver):
    """
    Resolves conflicts based on source type credibility priority rankings.
    """
    
    # Priority rank: higher index = higher trust
    SOURCE_PRIORITY = {
        "ats_json": 4,
        "resume_pdf": 3,
        "recruiter_csv": 2,
        "recruiter_notes": 1
    }

    def resolve(self, values_with_metadata: List[tuple[Any, FieldMetadata]]) -> tuple[Any, FieldMetadata]:
        if not values_with_metadata:
            raise ValueError("Values list for conflict resolution is empty")
            
        # Select winning value based on source type priority, breaking ties using confidence score, then timestamp
        def sort_key(item):
            val, meta = item
            priority = self.SOURCE_PRIORITY.get(meta.provenance.source_type, 0)
            confidence = meta.confidence.score
            timestamp = meta.provenance.extraction_timestamp.timestamp()
            return (priority, confidence, timestamp)

        winning_item = max(values_with_metadata, key=sort_key)
        return winning_item
