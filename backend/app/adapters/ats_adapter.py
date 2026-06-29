import hashlib
import json
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class ATSAdapter(BaseAdapter):
    """
    Adapter for structured ATS JSON payloads.
    Detects if the input is a JSON string or dict containing ATS identifiers.
    """

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, dict) and ("ats_id" in raw_data or "candidate_profile" in raw_data):
            return True
        if isinstance(raw_data, str):
            try:
                parsed = json.loads(raw_data)
                return isinstance(parsed, dict) and ("ats_id" in parsed or "candidate_profile" in parsed)
            except json.JSONDecodeError:
                return False
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        try:
            if isinstance(raw_data, dict):
                return raw_data
            if isinstance(raw_data, str):
                return json.loads(raw_data)
            raise ValueError("ATS raw data must be a dictionary or JSON string")
        except Exception as e:
            raise AdapterException(f"ATS parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if "ats_id" not in raw_parsed:
            raise ValidationException("ATS payloads must contain an 'ats_id'.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        profile = raw_parsed.get("candidate_profile", {})
        first_name = profile.get("first_name")
        last_name = profile.get("last_name")
        emails = profile.get("emails", [])
        phones = profile.get("phones", [])
        location = profile.get("location")
        skills = profile.get("skills", [])
        experience = profile.get("experience", [])
        education = profile.get("education", [])

        # Generate unique hash of raw input
        raw_str = json.dumps(raw_parsed, sort_keys=True)
        sha_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        return CandidateFragment(
            fragment_id=f"frag-ats-{raw_parsed.get('ats_id')}",
            source_id=source_id,
            source_type="ats_json",
            raw_data_hash=sha_hash,
            first_name=first_name,
            last_name=last_name,
            emails=emails,
            phones=phones,
            location=location,
            skills=skills,
            experience=experience,
            education=education,
            raw_payload=raw_parsed
        )
