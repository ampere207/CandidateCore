import pytest
from app.services.normalization.email_normalizer import EmailNormalizer
from app.services.normalization.phone_normalizer import PhoneNormalizer
from app.services.normalization.date_normalizer import DateNormalizer
from app.services.normalization.skill_normalizer import SkillNormalizer
from app.services.projection.projection_engine import DefaultProjectionEngine
from app.services.enrichment.semantic_enrichment import DefaultSemanticEnrichmentEngine
from app.services.merge.conflict_resolver import SourcePriorityConflictResolver
from app.models.canonical_candidate import CanonicalCandidate, CanonicalField
from app.models.projection_config import ProjectionConfig
from app.models.field_metadata import FieldMetadata
from app.models.provenance import ProvenanceMetadata
from app.models.confidence import ConfidenceMetadata
from app.exceptions.custom_exceptions import NormalizationException, ProjectionException

def test_email_normalizer():
    norm = EmailNormalizer()
    assert norm.normalize("  JANE.smith@Example.COM  ") == "jane.smith@example.com"
    with pytest.raises(NormalizationException):
        norm.normalize("invalid-email")

def test_phone_normalizer():
    norm = PhoneNormalizer()
    assert norm.normalize(" +1 (555) 019 - 9911 ") == "+15550199911"
    with pytest.raises(NormalizationException):
        norm.normalize("12")

def test_date_normalizer():
    norm = DateNormalizer()
    assert norm.normalize("2024-05-15") == "2024-05-15"
    assert norm.normalize("05/15/2024") == "2024-05-15"
    assert norm.normalize("2024") == "2024-01-01"

def test_skill_normalizer():
    norm = SkillNormalizer()
    assert norm.normalize(" python3 ") == "Python"
    assert norm.normalize(" reactjs ") == "React"

def test_conflict_resolver_priority():
    resolver = SourcePriorityConflictResolver()
    
    prov1 = ProvenanceMetadata(source_id="csv", source_type="recruiter_csv")
    conf1 = ConfidenceMetadata(score=0.8, confidence_method="direct")
    meta1 = FieldMetadata(provenance=prov1, confidence=conf1)
    
    prov2 = ProvenanceMetadata(source_id="ats", source_type="ats_json")
    conf2 = ConfidenceMetadata(score=0.9, confidence_method="direct")
    meta2 = FieldMetadata(provenance=prov2, confidence=conf2)
    
    winning_val, winning_meta = resolver.resolve([
        ("Alex", meta1),
        ("Alexander", meta2)
    ])
    
    # ats_json has higher priority than recruiter_csv
    assert winning_val == "Alexander"
    assert winning_meta.provenance.source_type == "ats_json"

def test_projection_engine():
    engine = DefaultProjectionEngine()
    
    prov = ProvenanceMetadata(source_id="csv", source_type="recruiter_csv")
    conf = ConfidenceMetadata(score=1.0, confidence_method="test")
    meta = FieldMetadata(provenance=prov, confidence=conf)
    
    candidate = CanonicalCandidate(
        candidate_id="cand-99",
        first_name=CanonicalField[str](value="Alex", metadata=meta, history=[]),
        last_name=CanonicalField[str](value="Rivera", metadata=meta, history=[])
    )
    
    config = ProjectionConfig(
        selected_fields=["first_name"],
        field_mappings={"first_name": "firstName"},
        required_fields=["first_name"]
    )
    
    projected = engine.project(candidate, config)
    assert projected.full_name == "Alex Rivera"
    assert projected.candidate_id == "cand-99"

    # Test required missing validation failure
    bad_config = ProjectionConfig(
        selected_fields=["last_name"],
        required_fields=["first_name"]
    )
    with pytest.raises(ProjectionException):
        engine.project(candidate, bad_config)
