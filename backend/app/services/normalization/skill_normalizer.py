from typing import Any
from app.services.normalization.normalizer import Normalizer
from app.exceptions.custom_exceptions import NormalizationException

class SkillNormalizer(Normalizer):
    """
    Standardizes skill naming conventions.
    In Phase 1, strips spaces and standardizes capitalization mapping rules.
    """
    
    # Simple static mapping of common skills for Phase 1 demonstration
    SKILL_MAPPINGS = {
        "python3": "Python",
        "py": "Python",
        "js": "JavaScript",
        "javascript": "JavaScript",
        "react.js": "React",
        "reactjs": "React",
        "node": "Node.js",
        "nodejs": "Node.js",
        "html5": "HTML",
        "css3": "CSS"
    }

    def normalize(self, value: Any) -> str:
        if not isinstance(value, str):
            raise NormalizationException("Skill value must be a string")
            
        cleaned = value.strip().lower()
        if not cleaned:
            raise NormalizationException("Skill value cannot be empty")
            
        # Map known variations
        return self.SKILL_MAPPINGS.get(cleaned, value.strip())
