import hashlib
import json
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class ATSAdapter(BaseAdapter):
    """
    Adapter for structured Applicant Tracking System (ATS) JSON payloads.
    Detects if the payload contains standard ATS tracking attributes.
    """

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, dict):
            return "ats_id" in raw_data or "candidate_profile" in raw_data
        
        if isinstance(raw_data, str):
            try:
                # Strip spaces
                trimmed = raw_data.strip()
                if not (trimmed.startswith("{") and trimmed.endswith("}")):
                    return False
                parsed = json.loads(trimmed)
                return isinstance(parsed, dict) and ("ats_id" in parsed or "candidate_profile" in parsed)
            except json.JSONDecodeError:
                return False
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        if isinstance(raw_data, dict):
            return raw_data
        
        if isinstance(raw_data, str):
            try:
                return json.loads(raw_data)
            except json.JSONDecodeError as e:
                raise AdapterException(f"ATS JSON decoding error: {str(e)}")
                
        raise AdapterException("ATS raw data must be a dictionary or a JSON string")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if "ats_id" not in raw_parsed:
            raise ValidationException("ATS profile configuration requires an 'ats_id' tracking field.")
            
        profile = raw_parsed.get("candidate_profile")
        if not profile or not isinstance(profile, dict):
            raise ValidationException("ATS JSON requires a nested 'candidate_profile' object.")
            
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        profile = raw_parsed.get("candidate_profile", {})
        
        first_name = profile.get("first_name") or profile.get("firstname") or None
        last_name = profile.get("last_name") or profile.get("lastname") or None
        
        emails = profile.get("emails") or []
        if isinstance(emails, str):
            emails = [emails]
            
        phones = profile.get("phones") or []
        if isinstance(phones, str):
            phones = [phones]
            
        location = profile.get("location")
        skills = profile.get("skills") or []
        experience = profile.get("experience") or []
        education = profile.get("education") or []

        # Hash payload
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
