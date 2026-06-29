from fastapi import APIRouter, Depends, HTTPException
from app.models.canonical_candidate import CanonicalCandidate
from app.models.projection_config import ProjectionConfig
from app.api.dependencies import get_projection_engine
from app.services.projection.projection_engine import ProjectionEngine
from app.exceptions.custom_exceptions import ProjectionException
from app.logging.logger import logger

router = APIRouter(tags=["Projection"])

@router.post("/projection")
async def project_candidate(
    candidate: CanonicalCandidate,
    config: ProjectionConfig,
    projection_engine: ProjectionEngine = Depends(get_projection_engine)
):
    """
    Transforms the structured CanonicalCandidate profile according to field selection, 
    exclusion, renaming, and required validations specified in the config.
    """
    logger.info(f"Executing projection for candidate {candidate.candidate_id}")
    try:
        projected_result = projection_engine.project(candidate, config)
        return {
            "success": True,
            "projected_data": projected_result
        }
    except ProjectionException as e:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Projection run failed: {str(e)}")
