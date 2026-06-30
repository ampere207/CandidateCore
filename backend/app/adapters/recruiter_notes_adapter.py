import hashlib
import re
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class RecruiterNotesAdapter(BaseAdapter):
    """
    Adapter for unstructured recruiter text files or notes.
    Detects based on common note headings or labels.
    """

    def detect(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, str):
            return False
        
        lower_data = raw_data.lower()
        keywords = ["recruiter notes", "interview notes", "candidate feedback", "interview feedback", "candidate observations"]
        return any(k in lower_data for k in keywords)

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        if not isinstance(raw_data, str):
            raise AdapterException("Recruiter notes must be a string")
        
        try:
            # Deterministic line-by-line extractor
            lines = [line.strip() for line in raw_data.split("\n")]
            parsed_data = {
                "raw_text": raw_data,
                "first_name": "",
                "last_name": "",
                "emails": [],
                "phones": [],
                "location": "",
                "skills": [],
                "availability": "",
                "role_preferences": "",
                "observations": ""
            }

            # 1. Extract email and phone using regex
            emails = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", raw_data)
            parsed_data["emails"] = list(set(emails))

            phones = re.findall(r"\+?\d[\d -]{7,}\d", raw_data)
            parsed_data["phones"] = list(set(phones))

            # 2. Extract key fields using text markers
            for line in lines:
                lower_line = line.lower()
                
                # Name check
                if "candidate:" in lower_line or "name:" in lower_line:
                    name_part = line.split(":", 1)[1].strip()
                    parts = name_part.split()
                    if len(parts) >= 2:
                        parsed_data["first_name"] = parts[0]
                        parsed_data["last_name"] = " ".join(parts[1:])
                    elif len(parts) == 1:
                        parsed_data["first_name"] = parts[0]
                
                # Alternate header detection for name
                elif "interview notes for" in lower_line or "interview feedback for" in lower_line:
                    pattern = r"(?:notes|feedback) for\s+([A-Za-z]+)\s+([A-Za-z]+)"
                    match = re.search(pattern, lower_line, re.IGNORECASE)
                    if match:
                        parsed_data["first_name"] = match.group(1).capitalize()
                        parsed_data["last_name"] = match.group(2).capitalize()

                # Location check
                elif "location:" in lower_line or "current location:" in lower_line:
                    parsed_data["location"] = line.split(":", 1)[1].strip()

                # Skills check
                elif "skills:" in lower_line or "key skills:" in lower_line:
                    skills_part = line.split(":", 1)[1].strip()
                    delim = ";" if ";" in skills_part else ","
                    parsed_data["skills"] = [s.strip() for s in skills_part.split(delim) if s.strip()]

                # Availability
                elif "availability:" in lower_line:
                    parsed_data["availability"] = line.split(":", 1)[1].strip()

                # Role preferences
                elif "role preferences:" in lower_line or "preferences:" in lower_line:
                    parsed_data["role_preferences"] = line.split(":", 1)[1].strip()

                # Observations
                elif "observations:" in lower_line or "candidate observations:" in lower_line:
                    parsed_data["observations"] = line.split(":", 1)[1].strip()

            return parsed_data
        except Exception as e:
            raise AdapterException(f"Recruiter notes parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if len(raw_parsed.get("raw_text", "").strip()) < 15:
            raise ValidationException("Recruiter notes payload is too short to be processed.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        sha_hash = hashlib.sha256(raw_parsed["raw_text"].encode("utf-8")).hexdigest()
        
        # Populate CandidateFragment details
        return CandidateFragment(
            fragment_id=f"frag-notes-{sha_hash[:8]}",
            source_id=source_id,
            source_type="recruiter_notes",
            raw_data_hash=sha_hash,
            first_name=raw_parsed.get("first_name") or None,
            last_name=raw_parsed.get("last_name") or None,
            emails=raw_parsed.get("emails", []),
            phones=raw_parsed.get("phones", []),
            location=raw_parsed.get("location") or None,
            skills=raw_parsed.get("skills", []),
            raw_payload=raw_parsed
        )
