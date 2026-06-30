from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field

class LocationOutput(BaseModel):
    city: Optional[str] = None
    region: Optional[str] = None
    country: Optional[str] = None

class LinksOutput(BaseModel):
    linkedin: Optional[str] = None
    github: Optional[str] = None
    portfolio: Optional[str] = None
    other: List[str] = []

class SkillItemOutput(BaseModel):
    name: str
    confidence: float
    sources: List[str]

class ExperienceItemOutput(BaseModel):
    company: str
    title: str
    start: str
    end: Optional[str] = None
    summary: Optional[str] = None

class EducationItemOutput(BaseModel):
    institution: str
    degree: str
    field: Optional[str] = None
    end_year: Optional[int] = None

class ProvenanceItemOutput(BaseModel):
    field: str
    selected_source: str
    confidence: float
    reason: str

class MetadataOutput(BaseModel):
    generated_at: datetime
    pipeline_version: str
    sources_processed: int
    ai_enrichment_enabled: bool

class AISemanticSummaryOutput(BaseModel):
    professional_summary: Optional[str] = None
    core_strengths: List[str] = []
    recommended_roles: List[str] = []
    technical_highlights: List[str] = []
    leadership_signals: List[str] = []
    communication_signals: List[str] = []
    interview_focus: List[str] = []
    recruiter_insights: List[str] = []
    potential_concerns: List[str] = []

class CandidateOutput(BaseModel):
    candidate_id: str
    full_name: str
    emails: List[str] = []
    phones: List[str] = []
    location: LocationOutput
    links: LinksOutput
    headline: Optional[str] = None
    years_experience: Optional[float] = None
    skills: List[SkillItemOutput] = []
    experience: List[ExperienceItemOutput] = []
    education: List[EducationItemOutput] = []
    provenance: List[ProvenanceItemOutput] = []
    overall_confidence: float
    metadata: MetadataOutput
    ai_semantic_summary: Optional[AISemanticSummaryOutput] = None
