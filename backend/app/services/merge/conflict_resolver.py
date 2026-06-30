from abc import ABC, abstractmethod
from typing import Any, List, Tuple
from app.models.field_metadata import FieldMetadata

class ConflictResolver(ABC):
    """
    Interface for conflict resolution strategy.
    """
    @abstractmethod
    def resolve(self, values_with_metadata: List[Tuple[Any, FieldMetadata]]) -> Tuple[Any, FieldMetadata]:
        pass

class SourcePriorityConflictResolver(ConflictResolver):
    """
    Resolves field-level value conflicts deterministically.
    Prefers values with the highest confidence scores.
    Breaks ties using source priority rankings and latest extraction timestamps.
    """
    
    # Priority rankings (higher number = higher trust)
    SOURCE_PRIORITIES = {
        "ats_json": 4,
        "resume_pdf": 3,
        "recruiter_csv": 2,
        "recruiter_notes": 1
    }

    def resolve(self, values_with_metadata: List[Tuple[Any, FieldMetadata]]) -> Tuple[Any, FieldMetadata]:
        if not values_with_metadata:
            raise ValueError("Cannot resolve conflict on empty value metadata list")

        # Sorting key function:
        # 1. Confidence score (descending)
        # 2. Source reliability priority (descending)
        # 3. Extraction timestamp (descending)
        def sort_key(item: Tuple[Any, FieldMetadata]):
            val, meta = item
            confidence_score = meta.confidence.score
            source_type = meta.provenance.source_type
            source_priority = self.SOURCE_PRIORITIES.get(source_type, 0)
            timestamp = meta.provenance.extraction_timestamp.timestamp()
            
            return (confidence_score, source_priority, timestamp)

        # Select the item with the maximum key
        winning_item = max(values_with_metadata, key=sort_key)
        return winning_item
