from fastapi import APIRouter, Depends, HTTPException
from app.models.candidate_output import CandidateOutput
from app.models.projection_config import ProjectionConfig
from app.api.dependencies import get_projection_engine
from app.services.projection.projection_engine import ProjectionEngine
from app.api.routes.pipeline import CANDIDATE_STORE
from app.exceptions.custom_exceptions import ProjectionException
from app.logging.logger import logger

router = APIRouter(tags=["Projection"])

@router.post("/projection/{candidate_id}", response_model=CandidateOutput)
async def project_candidate(
    candidate_id: str,
    config: ProjectionConfig,
    projection_engine: ProjectionEngine = Depends(get_projection_engine)
):
    """
    Transforms the structured CanonicalCandidate profile according to field selection, 
    exclusion, renaming, and required validations specified in the config.
    Returns projected CandidateOutput.
    """
    logger.info(f"Executing projection for candidate {candidate_id}")
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    candidate = CANDIDATE_STORE[candidate_id]
    try:
        projected_result = projection_engine.project(candidate, config)
        return projected_result
    except ProjectionException as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Projection run failed: {str(e)}")
