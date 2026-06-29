from datetime import datetime, timezone
from typing import Optional, Any
from pydantic import BaseModel, Field, ConfigDict

class ProvenanceMetadata(BaseModel):
    model_config = ConfigDict(frozen=True)
    
    source_id: str = Field(
        ..., 
        description="Unique identifier of the source document or payload fragment"
    )
    source_type: str = Field(
        ..., 
        description="Type of the ingestion source (e.g., recruiter_csv, ats_json, resume_pdf, recruiter_notes)"
    )
    extraction_timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp indicating when the raw value was extracted"
    )
    raw_value: Optional[Any] = Field(
        None, 
        description="The raw un-normalized value retrieved from the source"
    )
    extractor_version: str = Field(
        "1.0.0", 
        description="Version string of the adapter extractor parsing the source"
    )
