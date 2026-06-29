from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, ConfigDict

class PipelineStatus(BaseModel):
    model_config = ConfigDict(frozen=False)

    job_id: str = Field(
        ..., 
        description="Unique execution job ID tracking this pipeline run"
    )
    status: str = Field(
        "PENDING", 
        description="Current state of the pipeline (PENDING, RUNNING, COMPLETED, FAILED)"
    )
    processed_sources: List[str] = Field(
        default_factory=list, 
        description="List of source file names or IDs that have been processed"
    )
    errors: List[Dict[str, Any]] = Field(
        default_factory=list, 
        description="Captures non-blocking, field-level parsing or validation errors during pipeline execution"
    )
    started_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Pipeline run start time"
    )
    completed_at: Optional[datetime] = Field(
        None, 
        description="Pipeline run completion time"
    )
    candidate_id: Optional[str] = Field(
        None, 
        description="The resolved Canonical Candidate ID, if matching or merging was successful"
    )
