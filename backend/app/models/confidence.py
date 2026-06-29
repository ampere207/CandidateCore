from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, field_validator, ConfigDict

class ConfidenceMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    score: float = Field(
        ..., 
        description="Confidence score assigned to the field, bounded between 0.0 and 1.0"
    )
    confidence_method: str = Field(
        ..., 
        description="Method or engine used to compute the confidence score"
    )
    assessment_details: Dict[str, Any] = Field(
        default_factory=dict, 
        description="Key-value pairs containing detailed rules or factors driving the confidence score"
    )

    @field_validator("score")
    @classmethod
    def validate_score(cls, v: float) -> float:
        if not (0.0 <= v <= 1.0):
            raise ValueError("Confidence score must be in the range [0.0, 1.0]")
        return v
