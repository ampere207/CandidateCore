import uuid
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from app.models.canonical_candidate import CanonicalCandidate
from app.models.pipeline_status import PipelineStatus
from app.models.candidate_fragment import CandidateFragment
from app.api.dependencies import (
    get_validation_service,
    get_merge_engine,
    get_confidence_engine,
    get_provenance_engine
)
from app.services.validation.validation_service import ValidationService
from app.services.merge.merge_engine import MergeEngine, DefaultMergeEngine
from app.services.confidence.confidence_engine import ConfidenceEngine
from app.services.provenance.provenance_engine import ProvenanceEngine
from app.adapters.csv_adapter import CSVAdapter
from app.adapters.ats_adapter import ATSAdapter
from app.adapters.resume_adapter import ResumeAdapter
from app.adapters.recruiter_notes_adapter import RecruiterNotesAdapter
from app.exceptions.custom_exceptions import PipelineException
from app.logging.logger import logger

router = APIRouter(tags=["Pipeline execution"])

# Instantiating adapters for detection mapping
ADAPTERS = [
    CSVAdapter(),
    ATSAdapter(),
    ResumeAdapter(),
    RecruiterNotesAdapter()
]

# Global in-memory storage to maintain resolved profiles for Phase 2 API retrieval
CANDIDATE_STORE: Dict[str, CanonicalCandidate] = {}

@router.post("/pipeline/run", response_model=PipelineStatus)
async def run_pipeline(
    files: List[UploadFile] = File(..., description="Upload heterogeneous candidate files to run canonicalization"),
    validation_service: ValidationService = Depends(get_validation_service),
    merge_engine: MergeEngine = Depends(get_merge_engine)
):
    """
    Executes the candidate canonicalization pipeline.
    Ingests files, parses through matching adapters, standardizes, resolves fields, 
    and merges into a single Canonical Candidate Profile.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Initiating pipeline run job {job_id}", extra={"extra_context": {"job_id": job_id}})
    
    pipeline_status = PipelineStatus(job_id=job_id, status="RUNNING")
    fragments: List[CandidateFragment] = []

    for file in files:
        filename = file.filename or "unknown"
        pipeline_status.processed_sources.append(filename)
        
        try:
            content_bytes = await file.read()
            
            # Detect adapter
            matched_adapter = None
            content_str = None
            try:
                content_str = content_bytes.decode("utf-8")
            except UnicodeDecodeError:
                pass
                
            detect_payload = content_str if content_str is not None else content_bytes
            
            for adapter in ADAPTERS:
                if adapter.detect(detect_payload):
                    matched_adapter = adapter
                    break
                    
            if not matched_adapter:
                if filename.endswith(".csv"):
                    matched_adapter = ADAPTERS[0]
                elif filename.endswith(".json"):
                    matched_adapter = ADAPTERS[1]
                elif filename.endswith(".pdf"):
                    matched_adapter = ADAPTERS[2]
                else:
                    matched_adapter = ADAPTERS[3]
            
            # Parse, Validate, Normalize
            raw_parsed = matched_adapter.parse(detect_payload)
            matched_adapter.validate(raw_parsed)
            fragment = matched_adapter.normalize(raw_parsed, source_id=filename)
            
            # Record validation warnings
            field_errors = validation_service.validate_fragment(fragment)
            if field_errors:
                pipeline_status.errors.extend(field_errors)
                
            fragments.append(fragment)
            logger.info(f"Successfully processed file: {filename} into fragment {fragment.fragment_id}")
            
        except Exception as e:
            err_msg = f"Failed to ingest source file {filename}: {str(e)}"
            logger.error(err_msg, exc_info=True)
            pipeline_status.errors.append({
                "source": filename,
                "error_type": e.__class__.__name__,
                "message": str(e),
                "critical": True
            })

    if not fragments:
        pipeline_status.status = "FAILED"
        logger.error(f"Pipeline job {job_id} failed: No valid candidate data fragments extracted.")
        return pipeline_status

    try:
        # Merge fragments
        canonical_profile = merge_engine.merge(fragments)
        pipeline_status.candidate_id = canonical_profile.candidate_id
        
        # Store resolved candidate
        CANDIDATE_STORE[canonical_profile.candidate_id] = canonical_profile
        
        pipeline_status.status = "COMPLETED"
        logger.info(f"Pipeline job {job_id} completed. Candidate ID: {canonical_profile.candidate_id}")
    except Exception as e:
        pipeline_status.status = "FAILED"
        pipeline_status.errors.append({
            "source": "merge_stage",
            "error_type": e.__class__.__name__,
            "message": f"Merge process failure: {str(e)}",
            "critical": True
        })
        logger.error(f"Pipeline job {job_id} failed at merge stage: {str(e)}")

    return pipeline_status

@router.get("/pipeline/candidate/{candidate_id}", response_model=CanonicalCandidate)
async def get_candidate(candidate_id: str):
    """
    Queries and returns a resolved Canonical Candidate Profile by ID.
    """
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(status_code=404, detail="Canonical Candidate Profile not found")
    return CANDIDATE_STORE[candidate_id]
