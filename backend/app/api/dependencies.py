from typing import Generator
from app.services.validation.validation_service import ValidationService, SimpleValidationService
from app.services.merge.merge_engine import MergeEngine, DefaultMergeEngine
from app.services.confidence.confidence_engine import ConfidenceEngine, DefaultConfidenceEngine
from app.services.provenance.provenance_engine import ProvenanceEngine, DefaultProvenanceEngine
from app.services.projection.projection_engine import ProjectionEngine, DefaultProjectionEngine
from app.services.enrichment.semantic_enrichment import SemanticEnrichmentEngine, DefaultSemanticEnrichmentEngine

def get_validation_service() -> ValidationService:
    return SimpleValidationService()

def get_merge_engine() -> MergeEngine:
    return DefaultMergeEngine()

def get_confidence_engine() -> ConfidenceEngine:
    return DefaultConfidenceEngine()

def get_provenance_engine() -> ProvenanceEngine:
    return DefaultProvenanceEngine()

def get_projection_engine() -> ProjectionEngine:
    return DefaultProjectionEngine()

def get_enrichment_engine() -> SemanticEnrichmentEngine:
    return DefaultSemanticEnrichmentEngine()
