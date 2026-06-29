from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class CandidateFragment(BaseModel):
    model_config = ConfigDict(frozen=True)

    fragment_id: str = Field(
        ..., 
        description="Unique identifier for this specific ingested fragment (e.g., UUID)"
    )
    source_id: str = Field(
        ..., 
        description="Identifier referencing the source record or file (e.g., file path or database ID)"
    )
    source_type: str = Field(
        ..., 
        description="Format/type of the source (e.g., recruiter_csv, ats_json, resume_pdf, recruiter_notes)"
    )
    extracted_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Timestamp indicating when the fragment extraction was executed"
    )
    raw_data_hash: str = Field(
        ..., 
        description="SHA-256 hash of the raw input content to prevent duplicate processing"
    )
    
    # Candidate fields extracted from the source (nullable/optional to support partial data fragments)
    first_name: Optional[str] = Field(None, description="Extracted first name")
    last_name: Optional[str] = Field(None, description="Extracted last name")
    emails: List[str] = Field(default_factory=list, description="Extracted email addresses")
    phones: List[str] = Field(default_factory=list, description="Extracted phone numbers")
    location: Optional[str] = Field(None, description="Extracted location/address string")
    skills: List[str] = Field(default_factory=list, description="Extracted skills")
    experience: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Raw list of experience items (e.g. company, title, dates)"
    )
    education: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Raw list of education items (e.g. school, degree, major, dates)"
    )
    
    # Store complete raw payload for auditability
    raw_payload: Dict[str, Any] = Field(
        default_factory=dict, 
        description="The unmodified raw JSON/dict payload from which this fragment was parsed"
    )
