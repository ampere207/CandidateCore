from fastapi import APIRouter, Depends, HTTPException
from app.models.canonical_candidate import CanonicalCandidate
from app.api.dependencies import get_enrichment_engine
from app.services.enrichment.semantic_enrichment import SemanticEnrichmentEngine
from app.logging.logger import logger

router = APIRouter(tags=["Enrichment"])

@router.post("/semantic-enrichment", response_model=CanonicalCandidate)
async def enrich_candidate(
    candidate: CanonicalCandidate,
    enrichment_engine: SemanticEnrichmentEngine = Depends(get_enrichment_engine)
):
    """
    Enriches the Canonical Candidate Profile with semantic metadata such as inferred seniority tags or skills categorization.
    """
    logger.info(f"Executing semantic enrichment for candidate {candidate.candidate_id}")
    try:
        enriched_candidate = enrichment_engine.enrich(candidate)
        return enriched_candidate
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic enrichment failed: {str(e)}")
