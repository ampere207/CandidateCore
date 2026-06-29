from fastapi import APIRouter
from datetime import datetime, timezone

router = APIRouter(tags=["System health"])

@router.get("/health")
async def health_check():
    """
    Returns API runtime check status.
    """
    return {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "service": "CandidateCore Ingestion Pipeline Engine"
    }
