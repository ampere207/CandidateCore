from pydantic import BaseModel, Field, ConfigDict
from app.models.provenance import ProvenanceMetadata
from app.models.confidence import ConfidenceMetadata

class FieldMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)

    provenance: ProvenanceMetadata = Field(
        ..., 
        description="Lineage and origin history of the field value"
    )
    confidence: ConfidenceMetadata = Field(
        ..., 
        description="Confidence metrics associated with the field value"
    )
