import pytest
from app.adapters.csv_adapter import CSVAdapter
from app.adapters.ats_adapter import ATSAdapter
from app.adapters.resume_adapter import ResumeAdapter
from app.adapters.recruiter_notes_adapter import RecruiterNotesAdapter
from app.exceptions.custom_exceptions import ValidationException

def test_csv_adapter_flow():
    adapter = CSVAdapter()
    raw_csv = "first_name,last_name,email,phone,skills\nAlex,Rivera,alex@example.com,+15550199,python;react"
    
    assert adapter.detect(raw_csv) is True
    assert adapter.detect("{}") is False

    parsed = adapter.parse(raw_csv)
    assert parsed["first_name"] == "Alex"
    assert parsed["email"] == "alex@example.com"
    
    assert adapter.validate(parsed) is True
    
    fragment = adapter.normalize(parsed, source_id="test.csv")
    assert fragment.first_name == "Alex"
    assert fragment.emails == ["alex@example.com"]
    assert fragment.skills == ["python", "react"]

def test_ats_adapter_flow():
    adapter = ATSAdapter()
    raw_json = {
        "ats_id": "ats-123",
        "candidate_profile": {
            "first_name": "Jane",
            "last_name": "Smith",
            "emails": ["jane.smith@example.com"]
        }
    }
    
    assert adapter.detect(raw_json) is True
    
    parsed = adapter.parse(raw_json)
    assert parsed["ats_id"] == "ats-123"
    
    assert adapter.validate(parsed) is True
    
    fragment = adapter.normalize(parsed, source_id="ats_conn")
    assert fragment.first_name == "Jane"
    assert fragment.emails == ["jane.smith@example.com"]

def test_resume_adapter_detection():
    adapter = ResumeAdapter()
    pdf_magic = b"%PDF-1.4\nstream..."
    assert adapter.detect(pdf_magic) is True
    assert adapter.detect(b"not pdf") is False

def test_recruiter_notes_detection():
    adapter = RecruiterNotesAdapter()
    notes_text = "Recruiter Notes:\nDiscussed experience with candidate Alex."
    assert adapter.detect(notes_text) is True
    assert adapter.detect("not notes") is False
