from typing import List, Dict, Optional
from pydantic import BaseModel, Field, ConfigDict

class ProjectionConfig(BaseModel):
    model_config = ConfigDict(frozen=True)

    selected_fields: List[str] = Field(
        default_factory=list, 
        description="List of fields to include in the output projection. If empty, all fields are included."
    )
    field_mappings: Dict[str, str] = Field(
        default_factory=dict, 
        description="Key-value mapping to rename fields in the projected output (e.g., 'first_name' -> 'firstName')"
    )
    exclude_fields: List[str] = Field(
        default_factory=list, 
        description="List of fields to explicitly omit from the output projection"
    )
    required_fields: List[str] = Field(
        default_factory=list, 
        description="List of fields that must not be null/empty in the final projection. Raises validation error if missing."
    )
    output_format: str = Field(
        "json", 
        description="Target output format for the projection (e.g., 'json', 'nested_object', 'flat_dict')"
    )
