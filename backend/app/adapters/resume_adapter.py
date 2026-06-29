import hashlib
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class ResumeAdapter(BaseAdapter):
    """
    Adapter for resume PDFs.
    Detects if the input starts with PDF magic bytes (%PDF).
    """

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, bytes) and raw_data.startswith(b"%PDF"):
            return True
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        try:
            if not isinstance(raw_data, bytes):
                raise ValueError("PDF raw data must be bytes")
            
            # Phase 1 Mock implementation:
            # We mock the extraction of text from PDF bytes.
            # In a real implementation we would use pdfplumber / pdfminer.
            sha_hash = hashlib.sha256(raw_data).hexdigest()
            
            # Return dummy parsed result representing the extracted content
            return {
                "text": "Mock Extracted PDF Resume Text for hash " + sha_hash,
                "file_hash": sha_hash
            }
        except Exception as e:
            raise AdapterException(f"PDF parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if not raw_parsed.get("text"):
            raise ValidationException("Extracted PDF text is empty.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        # Mocking mapping from PDF unstructured text extraction
        sha_hash = raw_parsed.get("file_hash", "unknown")
        
        return CandidateFragment(
            fragment_id=f"frag-pdf-{sha_hash[:8]}",
            source_id=source_id,
            source_type="resume_pdf",
            raw_data_hash=sha_hash,
            first_name="ExtractedFirstName",
            last_name="ExtractedLastName",
            emails=["extracted@example.com"],
            phones=["+1-555-0199"],
            location="San Francisco, CA",
            skills=["Python", "Machine Learning", "System Design"],
            experience=[
                {"company": "Google", "title": "Software Engineer", "dates": "2020-Present"}
            ],
            education=[
                {"school": "Stanford University", "degree": "M.S.", "major": "Computer Science"}
            ],
            raw_payload={"mock_text_len": len(raw_parsed.get("text", ""))}
        )
