from fastapi import APIRouter, Depends, HTTPException
from app.models.candidate_output import CandidateOutput
from app.api.dependencies import get_enrichment_engine, get_projection_engine
from app.services.enrichment.semantic_enrichment import SemanticEnrichmentEngine
from app.services.projection.projection_engine import ProjectionEngine
from app.api.routes.pipeline import CANDIDATE_STORE
from app.logging.logger import logger

router = APIRouter(tags=["Enrichment"])

@router.post("/semantic-enrichment/{candidate_id}", response_model=CandidateOutput)
async def enrich_candidate(
    candidate_id: str,
    enrichment_engine: SemanticEnrichmentEngine = Depends(get_enrichment_engine),
    projection_engine: ProjectionEngine = Depends(get_projection_engine)
):
    """
    Enriches the Canonical Candidate Profile with semantic metadata such as inferred seniority tags.
    Saves it to backend store and returns projected CandidateOutput.
    """
    logger.info(f"Executing semantic enrichment for candidate {candidate_id}")
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(status_code=404, detail="Candidate not found")
        
    candidate = CANDIDATE_STORE[candidate_id]
    try:
        enriched_candidate = enrichment_engine.enrich(candidate)
        CANDIDATE_STORE[candidate_id] = enriched_candidate
        return projection_engine.project(enriched_candidate)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic enrichment failed: {str(e)}")
