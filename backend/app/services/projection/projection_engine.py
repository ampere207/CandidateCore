from abc import ABC, abstractmethod
from typing import Any, Dict
from app.models.canonical_candidate import CanonicalCandidate
from app.models.projection_config import ProjectionConfig
from app.exceptions.custom_exceptions import ProjectionException

class ProjectionEngine(ABC):
    """
    Interface for translating and flattening CanonicalCandidates into custom schema structures.
    """

    @abstractmethod
    def project(self, candidate: CanonicalCandidate, config: ProjectionConfig) -> Dict[str, Any]:
        """
        Transforms CanonicalCandidate to a target JSON format according to ProjectionConfig rules.
        """
        pass

class DefaultProjectionEngine(ProjectionEngine):
    """
    Core implementation of the ProjectionEngine mapping and transforming fields.
    """

    def project(self, candidate: CanonicalCandidate, config: ProjectionConfig) -> Dict[str, Any]:
        try:
            output = {}
            candidate_dict = candidate.model_dump()
            
            # Map canonical attributes
            fields_to_process = [
                "first_name", "last_name", "emails", "phones", "location", "skills", "experience", "education"
            ]

            for field in fields_to_process:
                # 1. Skip if explicitly excluded
                if field in config.exclude_fields:
                    continue
                
                # 2. Skip if we have selected list and field isn't in it
                if config.selected_fields and field not in config.selected_fields:
                    continue

                # Get value (extracting resolved value from CanonicalField wrapper)
                field_wrapper = getattr(candidate, field, None)
                val = field_wrapper.value if field_wrapper is not None else None
                
                # 4. Map output key name
                target_key = config.field_mappings.get(field, field)
                output[target_key] = val

            # 5. Validate that all required fields are present and non-empty in final output
            for req in config.required_fields:
                target_key = config.field_mappings.get(req, req)
                if target_key not in output or output[target_key] is None or (isinstance(output[target_key], list) and not output[target_key]):
                    raise ProjectionException(f"Required field '{req}' is missing or empty in the projected output.")

            # Always preserve candidate_id in projection output for mapping reference
            output["candidate_id"] = candidate.candidate_id
            return output
            
        except ProjectionException:
            raise
        except Exception as e:
            raise ProjectionException(f"Error executing projection: {str(e)}")
