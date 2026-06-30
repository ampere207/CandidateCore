import io
import hashlib
import re
from typing import Any, Dict, List
import pdfplumber
from app.adapters.base_adapter import BaseAdapter
from app.models.candidate_fragment import CandidateFragment
from app.exceptions.custom_exceptions import AdapterException, ValidationException

class ResumeAdapter(BaseAdapter):
    """
    Adapter for candidate Resume PDF documents.
    Detects if the payload begins with standard PDF magic bytes.
    """
    
    # Common tech/engineering skills vocabulary for fallback lookup
    SKILL_VOCABULARY = {
        "python", "javascript", "typescript", "golang", "java", "c++", "c#", "ruby", "rust",
        "react", "node.js", "nodejs", "vue", "angular", "next.js", "fastapi", "flask", "django",
        "docker", "kubernetes", "aws", "gcp", "azure", "sql", "postgresql", "mysql", "mongodb",
        "redis", "machine learning", "ml", "artificial intelligence", "nlp", "system design",
        "microservices", "git", "ci/cd", "terraform", "html", "css", "tailwind"
    }

    def detect(self, raw_data: Any) -> bool:
        if isinstance(raw_data, bytes) and raw_data.startswith(b"%PDF"):
            return True
        return False

    def parse(self, raw_data: Any) -> Dict[str, Any]:
        if not isinstance(raw_data, bytes):
            raise AdapterException("Resume PDF raw data must be a byte array")
            
        try:
            extracted_text = ""
            # Open PDF using pdfplumber in-memory
            with pdfplumber.open(io.BytesIO(raw_data)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        extracted_text += page_text + "\n"
                        
            if not extracted_text.strip():
                raise AdapterException("Could not extract any readable text layout from PDF")
                
            sha_hash = hashlib.sha256(raw_data).hexdigest()
            return {
                "text": extracted_text,
                "file_hash": sha_hash
            }
        except Exception as e:
            raise AdapterException(f"Resume PDF layout parsing error: {str(e)}")

    def validate(self, raw_parsed: Dict[str, Any]) -> bool:
        if not raw_parsed.get("text", "").strip():
            raise ValidationException("Parsed resume PDF text is empty.")
        return True

    def normalize(self, raw_parsed: Dict[str, Any], source_id: str) -> CandidateFragment:
        text = raw_parsed["text"]
        lines = [line.strip() for line in text.split("\n") if line.strip()]
        
        # 1. Deterministic Name Extraction:
        # Search first few lines for first/last name.
        # Avoid lines containing keywords like "resume", "curriculum", "@", or phone numbers.
        first_name = "Candidate"
        last_name = "Profile"
        
        for line in lines[:4]:
            if "@" in line or any(k in line.lower() for k in ["resume", "cv", "curriculum", "phone", "email"]):
                continue
            # Look for 2 or 3 capitalized alphabetical words
            words = line.split()
            if 2 <= len(words) <= 3 and all(w[0].isupper() and w.isalpha() for w in words):
                first_name = words[0]
                last_name = " ".join(words[1:])
                break
        
        # 2. Extract emails & phones via regex
        emails = list(set(re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", text)))
        phones = list(set(re.findall(r"\+?\d[\d -]{7,}\d", text)))
        
        # 3. Location extraction via standard city/state pattern (e.g. San Francisco, CA or Bangalore, India)
        location = None
        for line in lines[:15]:
            loc_match = re.search(r"([A-Z][a-zA-Z\s]{2,}),\s*([A-Z]{2,}|[A-Z][a-zA-Z\s]{2,})", line)
            # Avoid false positives like "Bachelor of Science, University"
            if loc_match and not any(k in line.lower() for k in ["university", "college", "school", "bachelor", "master", "degree"]):
                city = loc_match.group(1).strip()
                region = loc_match.group(2).strip()
                if len(city) < 30 and len(region) < 30:
                    location = f"{city}, {region}"
                    break

        # 4. Skills extraction: Section parse + vocabulary matching
        skills = set()
        
        # Section parse
        skills_sec_match = re.search(
            r"(?:skills|technical skills|technologies|proficiencies)\s*:?\s*([^:\n]+(?:\n\s*[^:\n]+)*)", 
            text, 
            re.IGNORECASE
        )
        if skills_sec_match:
            sec_text = skills_sec_match.group(1)
            # split by comma, semicolon, bullet points, or newlines
            raw_skills = re.split(r"[,;•\n\t]+", sec_text)
            for s in raw_skills:
                cleaned = s.strip()
                if cleaned and len(cleaned) < 25 and not any(x in cleaned.lower() for x in ["experience", "work"]):
                    skills.add(cleaned)

        # Fallback vocabulary check to capture missed tags
        lower_text = text.lower()
        for skill in self.SKILL_VOCABULARY:
            # Word boundary regex check
            pattern = rf"\b{re.escape(skill)}\b"
            if re.search(pattern, lower_text):
                # Standardize casing using a capital letter mapping representation
                title_skill = skill.capitalize()
                # Special cases:
                if skill == "nodejs" or skill == "node.js": title_skill = "Node.js"
                elif skill == "next.js": title_skill = "Next.js"
                elif skill == "fastapi": title_skill = "FastAPI"
                elif skill == "c++": title_skill = "C++"
                elif skill == "c#": title_skill = "C#"
                elif skill == "gcp": title_skill = "GCP"
                elif skill == "aws": title_skill = "AWS"
                elif skill == "sql": title_skill = "SQL"
                elif skill == "ci/cd": title_skill = "CI/CD"
                elif skill == "html": title_skill = "HTML"
                elif skill == "css": title_skill = "CSS"
                
                skills.add(title_skill)

        # 5. Experience section extraction
        experience = []
        exp_match = re.search(
            r"(?:experience|work experience|employment history|work history)\s*\n(.*?)(?=\n(?:education|skills|certifications|projects|languages)|$)", 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if exp_match:
            exp_text = exp_match.group(1)
            # Try to split by years/dates
            jobs = re.split(r"(\b\d{4}\s*-\s*(?:\d{4}|present|current)\b)", exp_text, flags=re.IGNORECASE)
            # Group jobs and dates
            if len(jobs) >= 2:
                for i in range(1, len(jobs), 2):
                    date_range = jobs[i].strip()
                    job_body = jobs[i+1].strip() if i+1 < len(jobs) else ""
                    # Grab first line of job body as title / company
                    job_lines = [l.strip() for l in job_body.split("\n") if l.strip()]
                    title_company = job_lines[0] if job_lines else "Software Engineer"
                    experience.append({
                        "company": title_company.split(",")[0].strip(),
                        "title": title_company.split(",")[-1].strip() if "," in title_company else "Engineer",
                        "dates": date_range
                    })
            else:
                # If no date ranges matched, parse line by line
                exp_lines = [l.strip() for l in exp_text.split("\n") if l.strip()]
                if exp_lines:
                    experience.append({
                        "company": exp_lines[0],
                        "title": exp_lines[1] if len(exp_lines) > 1 else "Software Engineer",
                        "dates": ""
                    })

        # 6. Education section extraction
        education = []
        edu_match = re.search(
            r"(?:education|academic background|academic details|credentials)\s*\n(.*?)(?=\n(?:experience|skills|projects|certifications|languages)|$)", 
            text, 
            re.IGNORECASE | re.DOTALL
        )
        if edu_match:
            edu_text = edu_match.group(1)
            edu_lines = [l.strip() for l in edu_text.split("\n") if l.strip()]
            for line in edu_lines:
                if any(x in line.lower() for x in ["university", "college", "school", "institute"]):
                    education.append({
                        "school": line,
                        "degree": "B.S." if "bachelor" in text.lower() or "b.s." in text.lower() else "Degree"
                    })
                    break

        return CandidateFragment(
            fragment_id=f"frag-pdf-{raw_parsed['file_hash'][:8]}",
            source_id=source_id,
            source_type="resume_pdf",
            raw_data_hash=raw_parsed["file_hash"],
            first_name=first_name,
            last_name=last_name,
            emails=emails,
            phones=phones,
            location=location,
            skills=sorted(list(skills)),
            experience=experience,
            education=education,
            raw_payload={"raw_text": text}
        )
