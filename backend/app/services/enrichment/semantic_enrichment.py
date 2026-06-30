import os
import re
import time
from datetime import datetime, timezone
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from google import genai
from google.genai import types
from app.models.canonical_candidate import CanonicalCandidate
from app.logging.logger import logger
from app.exceptions.custom_exceptions import EnrichmentException
from app.config.settings import settings

class GeminiSemanticEnrichment(BaseModel):
    """
    Structured Pydantic schema for Gemini 2.5 Flash semantic enrichment outputs.
    Ensures validated, machine-readable JSON structure.
    """
    professional_summary: str = Field(description="A concise summary of the candidate's career highlights.")
    core_strengths: List[str] = Field(description="List of key technical or core strengths.")
    recommended_roles: List[str] = Field(description="List of recommended position titles or functions.")
    technical_highlights: List[str] = Field(description="List of specific technical milestones or achievements.")
    leadership_signals: List[str] = Field(description="List of traits showing team leadership, project ownership, or initiative.")
    communication_signals: List[str] = Field(description="List of observations regarding communication skills, collaboration styles, or articulacy.")
    interview_focus_areas: List[str] = Field(description="Key technical or interpersonal topics that require deep-diving during live interviews.")
    potential_concerns: List[str] = Field(description="Red flags or gaps in candidate timelines, technology churn, or role tenures.")
    recruiter_insights: str = Field(description="Strategic feedback or synthesis suggestions to help match the candidate with target teams.")

class SemanticEnrichmentEngine(ABC):
    """
    Interface for semantic profiling, e.g. taxonomy mappings or job-title classification.
    """

    @abstractmethod
    async def enrich(self, candidate: CanonicalCandidate) -> CanonicalCandidate:
        pass

class DefaultSemanticEnrichmentEngine(SemanticEnrichmentEngine):
    """
    Standard Semantic Enrichment Engine.
    Processes recruiter notes and calls Gemini 2.5 Flash to extract validated structured insights.
    Fails safe to default fallback values if the model is unreachable or unavailable.
    """

    async def enrich(self, candidate: CanonicalCandidate) -> CanonicalCandidate:
        # Find raw recruiter notes text from field histories or fragment payload traces
        notes_text = ""
        
        all_histories = []
        for field in ["first_name", "last_name", "emails", "phones", "location", "skills"]:
            f_val = getattr(candidate, field, None)
            if f_val:
                all_histories.append(f_val.metadata)
                all_histories.extend(f_val.history)

        for meta in all_histories:
            if meta.provenance.source_type == "recruiter_notes" and meta.provenance.raw_value:
                raw_val = meta.provenance.raw_value
                if isinstance(raw_val, dict) and "raw_text" in raw_val:
                    notes_text = raw_val["raw_text"]
                    break
                elif isinstance(raw_val, str):
                    notes_text = raw_val
                    break

        if not notes_text:
            notes_text = "Recruiter notes: No interview writeups provided."

        api_key = settings.gemini_api_key
        
        # Default fallback structure for fail-safe capability
        fallback_insights = {
            "professional_summary": "AI enrichment unavailable.",
            "core_strengths": ["AI enrichment unavailable."],
            "recommended_roles": ["AI enrichment unavailable."],
            "technical_highlights": ["AI enrichment unavailable."],
            "leadership_signals": ["AI enrichment unavailable."],
            "communication_signals": ["AI enrichment unavailable."],
            "interview_focus_areas": ["AI enrichment unavailable."],
            "potential_concerns": ["AI enrichment unavailable."],
            "recruiter_insights": "AI enrichment unavailable.",
            "enriched_at": datetime.now(timezone.utc).isoformat(),
            "success": False
        }

        if not api_key:
            logger.warning(
                "Gemini Enrichment skipped: GEMINI_API_KEY environment variable is not defined.",
                extra={"extra_context": {"action": "enrichment_skipped_no_key"}}
            )
            candidate_dict = candidate.model_dump()
            candidate_dict["metadata"] = dict(candidate_dict.get("metadata", {}))
            candidate_dict["metadata"]["semantic_enrichment"] = fallback_insights
            candidate_dict["metadata"]["semantic_enrichment_applied"] = True
            return CanonicalCandidate(**candidate_dict)

        start_time = time.time()
        logger.info(
            "Enrichment Started", 
            extra={"extra_context": {
                "action": "enrichment_started", 
                "candidate_id": candidate.candidate_id,
                "model": "gemini-2.5-flash"
            }}
        )

        try:
            # Initialize official GenAI client using api_key
            client = genai.Client(api_key=api_key)
            
            prompt = f"""
            You are an expert technical recruiting advisor at Eightfold AI.
            Your task is to analyze a candidate's Canonical Master Profile and the original Recruiter Notes,
            and generate high-level semantic insights.
            
            Canonical Candidate Master Profile:
            {candidate.model_dump_json(indent=2)}
            
            Original Recruiter Notes:
            {notes_text}
            """
            
            response = await client.aio.models.generate_content(
                model='gemini-2.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=GeminiSemanticEnrichment,
                ),
            )
            
            # Validate structured response text with Pydantic
            insights_model = GeminiSemanticEnrichment.model_validate_json(response.text)
            insights = insights_model.model_dump()
            insights["enriched_at"] = datetime.now(timezone.utc).isoformat()
            insights["success"] = True
            
            latency = time.time() - start_time
            tokens_used = None
            if response.usage_metadata:
                tokens_used = response.usage_metadata.total_token_count
                
            logger.info(
                "Enrichment Completed",
                extra={"extra_context": {
                    "action": "enrichment_completed",
                    "candidate_id": candidate.candidate_id,
                    "latency_seconds": round(latency, 3),
                    "tokens_used": tokens_used
                }}
            )
            
            candidate_dict = candidate.model_dump()
            candidate_dict["metadata"] = dict(candidate_dict.get("metadata", {}))
            candidate_dict["metadata"]["semantic_enrichment"] = insights
            candidate_dict["metadata"]["semantic_enrichment_applied"] = True
            return CanonicalCandidate(**candidate_dict)

        except Exception as e:
            latency = time.time() - start_time
            logger.error(
                f"Failures: Semantic enrichment error: {str(e)}",
                extra={"extra_context": {
                    "action": "enrichment_failed",
                    "candidate_id": candidate.candidate_id,
                    "latency_seconds": round(latency, 3),
                    "error": str(e)
                }}
            )
            
            candidate_dict = candidate.model_dump()
            candidate_dict["metadata"] = dict(candidate_dict.get("metadata", {}))
            candidate_dict["metadata"]["semantic_enrichment"] = fallback_insights
            candidate_dict["metadata"]["semantic_enrichment_applied"] = True
            return CanonicalCandidate(**candidate_dict)
