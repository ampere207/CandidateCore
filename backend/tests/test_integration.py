import pytest
from unittest.mock import MagicMock, patch
from app.adapters.resume_adapter import ResumeAdapter
from app.adapters.csv_adapter import CSVAdapter
from app.adapters.recruiter_notes_adapter import RecruiterNotesAdapter
from app.services.merge.merge_engine import DefaultMergeEngine
from app.services.enrichment.semantic_enrichment import DefaultSemanticEnrichmentEngine
from app.models.candidate_fragment import CandidateFragment

def test_resume_adapter_parse_from_mock_pdf():
    adapter = ResumeAdapter()
    
    with patch("pdfplumber.open") as mock_open:
        mock_pdf = MagicMock()
        mock_page = MagicMock()
        mock_page.extract_text.return_value = "Alex Rivera\nEmail: alex.rivera@example.com\nPhone: +1-555-0199\nSkills: Python, Machine Learning\nExperience\n2020 - Present Google, Software Engineer\nEducation\nStanford University"
        mock_pdf.pages = [mock_page]
        mock_open.return_value.__enter__.return_value = mock_pdf

        dummy_bytes = b"%PDF-1.4\nstream..."
        assert adapter.detect(dummy_bytes) is True
        
        parsed = adapter.parse(dummy_bytes)
        assert "Alex Rivera" in parsed["text"]
        
        fragment = adapter.normalize(parsed, "candidate.pdf")
        assert fragment.first_name == "Alex"
        assert fragment.last_name == "Rivera"
        assert "Python" in fragment.skills

def test_end_to_end_merge():
    # 1. Fragment 1: CSV
    csv_raw = "first_name,last_name,email,phone,skills\nAlex,Rivera,alexr@example.com,+15550199,python3;javascript"
    csv_adapter = CSVAdapter()
    csv_parsed = csv_adapter.parse(csv_raw)
    csv_frag = csv_adapter.normalize(csv_parsed, "csv")
    
    # 2. Fragment 2: Notes
    notes_raw = "Candidate observations: Interview feedback for Alex Rivera.\nSkills: React, Python.\nLocation: San Francisco, CA"
    notes_adapter = RecruiterNotesAdapter()
    notes_parsed = notes_adapter.parse(notes_raw)
    notes_frag = notes_adapter.normalize(notes_parsed, "notes")
    
    # 3. Merge Engine Run
    merge_engine = DefaultMergeEngine()
    canonical = merge_engine.merge([csv_frag, notes_frag])
    
    assert canonical.first_name.value == "Alex"
    # skills is a union of normalized skills: Python (from python3), JavaScript, React
    assert "Python" in canonical.skills.value
    assert "React" in canonical.skills.value
    assert "JavaScript" in canonical.skills.value
    
    # Verify lineage explainability is populated
    assert canonical.first_name.selection_reason != ""
    assert len(canonical.first_name.competing_values) == 2

def test_semantic_enrichment_insights():
    # 1. Parse fragments and merge
    notes_raw = "Candidate observations: Interview feedback for Alex Rivera.\nSkills: React, Python.\nLocation: San Francisco, CA\nRole preferences: Senior Backend Engineer\nCandidate feedback: Outstanding system design skills."
    notes_adapter = RecruiterNotesAdapter()
    notes_parsed = notes_adapter.parse(notes_raw)
    notes_frag = notes_adapter.normalize(notes_parsed, "notes")
    
    merge_engine = DefaultMergeEngine()
    canonical = merge_engine.merge([notes_frag])
    
    # 2. Apply Enrichment
    enrichment_engine = DefaultSemanticEnrichmentEngine()
    enriched = enrichment_engine.enrich(canonical)
    
    assert enriched.metadata["semantic_enrichment_applied"] is True
    insights = enriched.metadata["semantic_enrichment"]
    assert "Senior Backend Engineer" in insights["role_preferences"]
    assert "Outstanding system design skills" in insights["recruiter_synopsis"]
    assert "Alex Rivera" in insights["professional_summary"]
