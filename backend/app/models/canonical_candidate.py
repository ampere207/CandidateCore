from datetime import datetime, timezone
from typing import Generic, TypeVar, Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict
from app.models.field_metadata import FieldMetadata

T = TypeVar('T')

class CanonicalField(BaseModel, Generic[T]):
    model_config = ConfigDict(frozen=True)

    value: T = Field(
        ..., 
        description="The resolved canonical value for this field"
    )
    metadata: FieldMetadata = Field(
        ..., 
        description="Metadata (provenance + confidence) of the winning source value"
    )
    history: List[FieldMetadata] = Field(
        default_factory=list, 
        description="List of all other candidate values from other sources used in conflict resolution/merging"
    )

class CanonicalCandidate(BaseModel):
    model_config = ConfigDict(frozen=True)

    candidate_id: str = Field(
        ..., 
        description="Unique identifier for the unified candidate profile (e.g. UUID)"
    )
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp indicating when the canonical profile was created"
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp indicating when the canonical profile was last updated"
    )
    
    first_name: Optional[CanonicalField[str]] = Field(None, description="Resolved first name")
    last_name: Optional[CanonicalField[str]] = Field(None, description="Resolved last name")
    emails: Optional[CanonicalField[List[str]]] = Field(None, description="Resolved list of emails")
    phones: Optional[CanonicalField[List[str]]] = Field(None, description="Resolved list of phone numbers")
    location: Optional[CanonicalField[str]] = Field(None, description="Resolved location")
    skills: Optional[CanonicalField[List[str]]] = Field(None, description="Resolved list of normalized skills")
    experience: Optional[CanonicalField[List[Dict[str, Any]]]] = Field(
        None, 
        description="Resolved timeline of experience details"
    )
    education: Optional[CanonicalField[List[Dict[str, Any]]]] = Field(
        None, 
        description="Resolved education history"
    )

    metadata: Dict[str, Any] = Field(
        default_factory=dict, 
        description="General pipeline engine run details or processing markers"
    )
