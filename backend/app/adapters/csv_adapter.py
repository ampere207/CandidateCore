import hashlib
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class CSVAdapter(BaseAdapter):
    """
    Adapter for Recruiter CSV payloads.
    Detects based on specific CSV column structures or headers in string/bytes format.
    """

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, str) and ("first_name" in raw_data or "email" in raw_data) and "," in raw_data:
            return True
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        try:
            # Phase 1 Mock implementation: just simulate parsing lines
            if not isinstance(raw_data, str):
                raise ValueError("CSV raw data must be a string")
            
            # Simple header/row splitter for mock
            lines = [line.strip() for line in raw_data.strip().split("\n") if line.strip()]
            if not lines:
                return {}
            
            headers = [h.strip() for h in lines[0].split(",")]
            if len(lines) < 2:
                return {}
            
            values = [v.strip() for v in lines[1].split(",")]
            parsed_dict = dict(zip(headers, values))
            return parsed_dict
        except Exception as e:
            raise AdapterException(f"CSV parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        # Require email or phone for validation
        if not raw_parsed.get("email") and not raw_parsed.get("phone"):
            raise ValidationException("CSV record must contain either 'email' or 'phone' to be unique.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        # Basic parsing & mapping to fragment schema
        first_name = raw_parsed.get("first_name")
        last_name = raw_parsed.get("last_name")
        email = raw_parsed.get("email")
        phone = raw_parsed.get("phone")
        skills_raw = raw_parsed.get("skills", "")
        skills = [s.strip() for s in skills_raw.split(";") if s.strip()] if skills_raw else []

        raw_str = str(raw_parsed)
        sha_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        return CandidateFragment(
            fragment_id=f"frag-csv-{sha_hash[:8]}",
            source_id=source_id,
            source_type="recruiter_csv",
            raw_data_hash=sha_hash,
            first_name=first_name,
            last_name=last_name,
            emails=[email] if email else [],
            phones=[phone] if phone else [],
            skills=skills,
            raw_payload=raw_parsed
        )
