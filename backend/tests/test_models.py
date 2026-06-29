import pytest
from datetime import datetime, timezone
from app.models.provenance import ProvenanceMetadata
from app.models.confidence import ConfidenceMetadata
from app.models.field_metadata import FieldMetadata
from app.models.candidate_fragment import CandidateFragment
from app.models.canonical_candidate import CanonicalCandidate, CanonicalField

def test_provenance_metadata():
    prov = ProvenanceMetadata(
        source_id="src_001",
        source_type="ats_json",
        raw_value="raw_name_test"
    )
    assert prov.source_id == "src_001"
    assert prov.source_type == "ats_json"
    assert prov.raw_value == "raw_name_test"
    assert isinstance(prov.extraction_timestamp, datetime)

def test_confidence_metadata_bounds():
    # Happy Path
    conf = ConfidenceMetadata(score=0.9, confidence_method="heuristic")
    assert conf.score == 0.9

    # Boundary Failure: > 1.0
    with pytest.raises(ValueError, match="Confidence score must be in the range"):
        ConfidenceMetadata(score=1.1, confidence_method="heuristic")

    # Boundary Failure: < 0.0
    with pytest.raises(ValueError, match="Confidence score must be in the range"):
        ConfidenceMetadata(score=-0.05, confidence_method="heuristic")

def test_canonical_field_generic_typing():
    prov = ProvenanceMetadata(source_id="src_002", source_type="resume_pdf")
    conf = ConfidenceMetadata(score=0.95, confidence_method="direct_parse")
    meta = FieldMetadata(provenance=prov, confidence=conf)

    field = CanonicalField[str](
        value="Jane Doe",
        metadata=meta,
        history=[]
    )
    assert field.value == "Jane Doe"
    assert field.metadata.provenance.source_type == "resume_pdf"

def test_immutable_models():
    prov = ProvenanceMetadata(source_id="src_003", source_type="recruiter_csv")
    
    # Models should be frozen
    with pytest.raises(Exception):
        prov.source_id = "new_id" # type: ignore
