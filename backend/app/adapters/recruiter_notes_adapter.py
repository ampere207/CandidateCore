import hashlib
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class RecruiterNotesAdapter(BaseAdapter):
    """
    Adapter for unstructured recruiter text files.
    Detects if the input is a plain text file containing recruitment keywords.
    """

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, str):
            lower_data = raw_data.lower()
            keywords = ["recruiter notes", "interview notes", "candidate feedback", "interview feedback"]
            return any(k in lower_data for k in keywords)
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        try:
            if not isinstance(raw_data, str):
                raise ValueError("Recruiter notes must be a string")
            
            sha_hash = hashlib.sha256(raw_data.encode("utf-8")).hexdigest()
            return {
                "text": raw_data,
                "text_hash": sha_hash
            }
        except Exception as e:
            raise AdapterException(f"Recruiter notes parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if len(raw_parsed.get("text", "").strip()) < 10:
            raise ValidationException("Recruiter notes are too short to process.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        sha_hash = raw_parsed.get("text_hash", "unknown")
        
        # Phase 1 Mock normalized representation:
        return CandidateFragment(
            fragment_id=f"frag-notes-{sha_hash[:8]}",
            source_id=source_id,
            source_type="recruiter_notes",
            raw_data_hash=sha_hash,
            first_name="NotesFirstName",
            last_name="NotesLastName",
            emails=["notes_candidate@example.com"],
            phones=[],
            location="Remote",
            skills=["React", "Node.js", "TailwindCSS"],
            experience=[
                {"company": "Meta", "title": "Senior Frontend Developer", "dates": "3 Years"}
            ],
            education=[],
            raw_payload={"mock_text": raw_parsed.get("text", "")[:100]}
        )
