import uuid
import os
from typing import List, Dict, Optional
from fastapi import APIRouter, Depends, UploadFile, File, Form, HTTPException
from app.models.canonical_candidate import CanonicalCandidate
from app.models.candidate_output import CandidateOutput
from app.models.pipeline_status import PipelineStatus
from app.models.candidate_fragment import CandidateFragment
from app.api.dependencies import (
    get_validation_service,
    get_merge_engine,
    get_confidence_engine,
    get_provenance_engine,
    get_enrichment_engine,
    get_projection_engine
)
from app.services.validation.validation_service import ValidationService
from app.services.merge.merge_engine import MergeEngine, DefaultMergeEngine
from app.services.confidence.confidence_engine import ConfidenceEngine
from app.services.provenance.provenance_engine import ProvenanceEngine
from app.services.enrichment.semantic_enrichment import SemanticEnrichmentEngine
from app.services.projection.projection_engine import ProjectionEngine
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

# Constants for security parameters
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB limit

@router.post("/pipeline/run", response_model=PipelineStatus)
async def run_pipeline(
    files: List[UploadFile] = File(..., description="Upload heterogeneous candidate files to run canonicalization"),
    enable_enrichment: bool = Form(False, description="Enable AI Semantic Enrichment using Gemini 2.5 Flash"),
    validation_service: ValidationService = Depends(get_validation_service),
    merge_engine: MergeEngine = Depends(get_merge_engine),
    enrichment_engine: SemanticEnrichmentEngine = Depends(get_enrichment_engine)
):
    """
    Executes the candidate canonicalization pipeline.
    Ingests files, parses through matching adapters, standardizes, resolves fields, 
    and merges into a single Canonical Candidate Profile.
    """
    job_id = str(uuid.uuid4())
    logger.info(f"Pipeline job {job_id} started. Process count: {len(files)}", extra={"extra_context": {"job_id": job_id, "action": "pipeline_started"}})
    
    pipeline_status = PipelineStatus(job_id=job_id, status="RUNNING")
    fragments: List[CandidateFragment] = []

    for file in files:
        # Security review: sanitize file name to avoid path traversal (isolate base name)
        filename = os.path.basename(file.filename or "unknown")
        pipeline_status.processed_sources.append(filename)
        
        # Security review: assert upload size limit bounds
        if file.size and file.size > MAX_FILE_SIZE:
            logger.warning(
                f"Ingestion reject: file {filename} exceeds limit of 10MB", 
                extra={"extra_context": {"job_id": job_id, "file": filename, "size": file.size}}
            )
            pipeline_status.errors.append({
                "source": filename,
                "error_type": "SecurityValidationError",
                "message": f"Upload rejected. File size ({file.size} bytes) exceeds the maximum limit of {MAX_FILE_SIZE} bytes (10MB).",
                "critical": True
            })
            continue

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
            
            # Log adapter mapping
            logger.info(
                f"Source file {filename} mapped to adapter: {matched_adapter.__class__.__name__}", 
                extra={"extra_context": {"job_id": job_id, "file": filename, "adapter": matched_adapter.__class__.__name__, "action": "source_detected"}}
            )

            # Parse, Validate, Normalize
            raw_parsed = matched_adapter.parse(detect_payload)
            matched_adapter.validate(raw_parsed)
            fragment = matched_adapter.normalize(raw_parsed, source_id=filename)
            
            # Log successful adapter parsing
            logger.info(
                f"Adapter extraction completed: {filename} into fragment {fragment.fragment_id}", 
                extra={"extra_context": {"job_id": job_id, "file": filename, "fragment_id": fragment.fragment_id, "action": "extraction_completed"}}
            )

            # Record validation warnings
            field_errors = validation_service.validate_fragment(fragment)
            if field_errors:
                pipeline_status.errors.extend(field_errors)
                logger.info(
                    f"Validation warnings logged for {filename}: {len(field_errors)} warnings", 
                    extra={"extra_context": {"job_id": job_id, "file": filename, "warnings": field_errors, "action": "validation_completed"}}
                )
                
            fragments.append(fragment)
            
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
        
        # Optional AI semantic enrichment phase
        if enable_enrichment:
            canonical_profile = await enrichment_engine.enrich(canonical_profile)
            
        pipeline_status.candidate_id = canonical_profile.candidate_id
        
        logger.info(
            f"Merge resolution completed. Canonical Profile ID: {canonical_profile.candidate_id}", 
            extra={"extra_context": {"job_id": job_id, "candidate_id": canonical_profile.candidate_id, "action": "merge_completed"}}
        )

        # Store resolved candidate
        CANDIDATE_STORE[canonical_profile.candidate_id] = canonical_profile
        
        pipeline_status.status = "COMPLETED"
        logger.info(f"Pipeline job {job_id} completed successfully.", extra={"extra_context": {"job_id": job_id, "action": "pipeline_finished"}})
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

@router.get("/pipeline/candidate/{candidate_id}", response_model=CandidateOutput)
async def get_candidate(
    candidate_id: str,
    projection_engine: ProjectionEngine = Depends(get_projection_engine)
):
    """
    Queries and returns a resolved Canonical Candidate Profile by ID mapped to CandidateOutput.
    """
    if candidate_id not in CANDIDATE_STORE:
        raise HTTPException(status_code=404, detail="Canonical Candidate Profile not found")
    candidate = CANDIDATE_STORE[candidate_id]
    return projection_engine.project(candidate)
