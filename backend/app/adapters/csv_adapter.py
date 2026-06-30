import csv
import hashlib
import io
from typing import Any, Dict
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class CSVAdapter(BaseAdapter):
    """
    Adapter for Recruiter CSV payloads.
    Detects if the input starts with typical CSV recruiter headers.
    """

    def detect(self, raw_data: Any) -> bool:
        if not isinstance(raw_data, str):
            return False
        
        # Look for headers in the first line
        first_line = raw_data.strip().split('\n')[0].lower()
        headers = ["name", "email", "phone", "skills", "company", "title"]
        # If we see at least two of these headers and commas on the FIRST line, it's a CSV
        matched_headers = sum(1 for h in headers if h in first_line)
        return matched_headers >= 2 and "," in first_line

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        if not isinstance(raw_data, str):
            raise AdapterException("CSV raw data must be a string")
        
        try:
            f = io.StringIO(raw_data.strip())
            # Handle delimiter configuration
            reader = csv.DictReader(f)
            rows = list(reader)
            
            if not rows:
                raise AdapterException("CSV content is empty")
            
            # Since a CSV payload represents one candidate profile per row (or multiple rows),
            # for identity resolution we parse the first valid candidate record row.
            # Clean headers: remove spaces and lowercase
            raw_parsed = {}
            row = rows[0]
            for key, val in row.items():
                if key:
                    clean_key = key.strip().lower()
                    raw_parsed[clean_key] = val.strip() if val else ""
            
            return raw_parsed
        except Exception as e:
            raise AdapterException(f"CSV format parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        # Check required fields
        if not raw_parsed.get("email") and not raw_parsed.get("phone"):
            raise ValidationException("CSV record must contain either 'email' or 'phone' for identification.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        # Field mapping and extraction
        first_name = raw_parsed.get("first_name") or raw_parsed.get("firstname") or None
        last_name = raw_parsed.get("last_name") or raw_parsed.get("lastname") or None
        
        email = raw_parsed.get("email")
        emails = [email] if email else []
        
        phone = raw_parsed.get("phone")
        phones = [phone] if phone else []
        
        location = raw_parsed.get("location") or raw_parsed.get("address") or None
        
        # Skills delimiter is typically semicolon or comma
        skills_raw = raw_parsed.get("skills", "")
        skills = []
        if skills_raw:
            delim = ";" if ";" in skills_raw else ","
            skills = [s.strip() for s in skills_raw.split(delim) if s.strip()]

        # Experience parse: CSV might have flat strings.
        experience = []
        company = raw_parsed.get("company")
        title = raw_parsed.get("title")
        years = raw_parsed.get("experience_years") or raw_parsed.get("experience")
        if company or title:
            experience.append({
                "company": company or "Unknown",
                "title": title or "Software Engineer",
                "dates": f"{years} years" if years else ""
            })

        # Education parse
        education = []
        school = raw_parsed.get("school") or raw_parsed.get("university")
        degree = raw_parsed.get("degree")
        if school:
            education.append({
                "school": school,
                "degree": degree or "B.S."
            })

        raw_str = str(sorted(raw_parsed.items()))
        sha_hash = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()

        return CandidateFragment(
            fragment_id=f"frag-csv-{sha_hash[:8]}",
            source_id=source_id,
            source_type="recruiter_csv",
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
