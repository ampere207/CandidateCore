import uuid
from typing import List, Optional, Any, Dict, Tuple
from datetime import datetime, timezone
from app.models.candidate_fragment import CandidateFragment
from app.models.canonical_candidate import CanonicalCandidate, CanonicalField, CompetingValue
from app.models.field_metadata import FieldMetadata
from app.models.provenance import ProvenanceMetadata
from app.models.confidence import ConfidenceMetadata
from app.services.merge.conflict_resolver import ConflictResolver, SourcePriorityConflictResolver
from app.services.confidence.confidence_engine import ConfidenceEngine, DefaultConfidenceEngine
from app.services.provenance.provenance_engine import ProvenanceEngine, DefaultProvenanceEngine
from app.services.validation.validation_service import ValidationService, PipelineValidationService
from app.services.normalization.email_normalizer import EmailNormalizer
from app.services.normalization.phone_normalizer import PhoneNormalizer
from app.services.normalization.date_normalizer import DateNormalizer
from app.services.normalization.skill_normalizer import SkillNormalizer
from app.services.normalization.company_normalizer import CompanyNormalizer
from app.services.normalization.country_normalizer import CountryNormalizer
from app.exceptions.custom_exceptions import MergeException

from abc import ABC, abstractmethod

class MergeEngine(ABC):
    """
    Interface for merging multiple CandidateFragments into a single CanonicalCandidate.
    """
    @abstractmethod
    def merge(self, fragments: List[CandidateFragment], candidate_id: Optional[str] = None) -> CanonicalCandidate:
        pass

class DefaultMergeEngine(MergeEngine):
    """
    Main Merge Engine for CandidateCore pipeline.
    Executes field-level merges, applies validators & normalizers,
    tracks consensus, runs tie-breaker conflict rules, and builds explainability logs.
    """

    def __init__(self, resolver: Optional[ConflictResolver] = None):
        self.resolver = resolver or SourcePriorityConflictResolver()
        self.confidence_engine = DefaultConfidenceEngine()
        self.provenance_engine = DefaultProvenanceEngine()
        self.validation_service = PipelineValidationService()
        
        # Initializing normalizers
        self.email_normalizer = EmailNormalizer()
        self.phone_normalizer = PhoneNormalizer()
        self.date_normalizer = DateNormalizer()
        self.skill_normalizer = SkillNormalizer()
        self.company_normalizer = CompanyNormalizer()
        self.country_normalizer = CountryNormalizer()

    def merge(self, fragments: List[CandidateFragment], candidate_id: Optional[str] = None) -> CanonicalCandidate:
        if not fragments:
            raise MergeException("Cannot run canonicalization on empty candidate fragments array")

        resolved_id = candidate_id or str(uuid.uuid4())
        
        # 1. Merge Scalar Fields (First Name, Last Name, Location)
        first_name_field = self._merge_scalar_field("first_name", [f.first_name for f in fragments if f.first_name], fragments)
        last_name_field = self._merge_scalar_field("last_name", [f.last_name for f in fragments if f.last_name], fragments)
        location_field = self._merge_scalar_field("location", [f.location for f in fragments if f.location], fragments)

        # 2. Merge Collection Fields (Emails, Phones, Skills)
        emails_field = self._merge_collection_field("emails", [email for f in fragments for email in f.emails], fragments, self.email_normalizer)
        phones_field = self._merge_collection_field("phones", [phone for f in fragments for phone in f.phones], fragments, self.phone_normalizer)
        skills_field = self._merge_collection_field("skills", [skill for f in fragments for skill in f.skills], fragments, self.skill_normalizer)

        # 3. Merge Complex Timelines (Experience, Education)
        experience_field = self._merge_experience(fragments)
        education_field = self._merge_education(fragments)

        # 4. Profile Meta Calculations
        overall_completeness = self.confidence_engine.calculate_profile_completeness(
            first_name=first_name_field.value if first_name_field else "",
            last_name=last_name_field.value if last_name_field else "",
            emails=emails_field.value if emails_field else [],
            phones=phones_field.value if phones_field else []
        )

        linkedin = None
        github = None
        portfolio = None
        other_links = []
        headline = None
        
        import re
        for frag in fragments:
            raw = frag.raw_payload or {}
            if not linkedin:
                linkedin = raw.get("linkedin_url") or raw.get("linkedin") or raw.get("candidate_profile", {}).get("linkedin")
            if not github:
                github = raw.get("github_url") or raw.get("github") or raw.get("candidate_profile", {}).get("github")
            if not portfolio:
                portfolio = raw.get("portfolio_url") or raw.get("portfolio") or raw.get("website") or raw.get("candidate_profile", {}).get("portfolio")
            
            if not headline:
                headline = raw.get("headline") or raw.get("candidate_profile", {}).get("headline") or raw.get("role_preferences")
                
            if isinstance(raw.get("raw_text"), str):
                text = raw["raw_text"]
                urls = re.findall(r'https?://[^\s<>"]+|www\.[^\s<>"]+', text)
                for url in urls:
                    url_lower = url.lower()
                    if "linkedin.com" in url_lower:
                        if not linkedin: linkedin = url
                    elif "github.com" in url_lower:
                        if not github: github = url
                    else:
                        if url not in other_links:
                            other_links.append(url)

        metadata = {
            "completeness_score": overall_completeness,
            "resolved_sources_count": len(fragments),
            "merged_at": datetime.now(timezone.utc).isoformat(),
            "links": {
                "linkedin": linkedin,
                "github": github,
                "portfolio": portfolio,
                "other": other_links
            },
            "headline": headline
        }

        return CanonicalCandidate(
            candidate_id=resolved_id,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            first_name=first_name_field,
            last_name=last_name_field,
            emails=emails_field,
            phones=phones_field,
            location=location_field,
            skills=skills_field,
            experience=experience_field,
            education=education_field,
            metadata=metadata
        )

    def _merge_scalar_field(self, field_name: str, values: List[str], fragments: List[CandidateFragment]) -> Optional[CanonicalField[str]]:
        if not values:
            return None

        # Build list of competing options
        competing_candidates: List[Tuple[str, FieldMetadata, CompetingValue]] = []
        
        for val in values:
            # Find the originating fragment
            orig_frag = next(f for f in fragments if getattr(f, field_name) == val)
            
            # 1. Normalization Step
            norm_val = val
            norm_success = True
            try:
                if field_name == "location" and "," in val:
                    parts = val.split(",", 1)
                    city = parts[0].strip().title()
                    country = self.country_normalizer.normalize(parts[1])
                    norm_val = f"{city}, {country}"
                else:
                    norm_val = val.strip().title()
            except Exception:
                norm_success = False
                
            # 2. Validation Step (check warnings)
            has_warnings = False
            # Generate temporary fragment to trigger validations
            temp_fields = {
                "fragment_id": orig_frag.fragment_id,
                "source_id": orig_frag.source_id,
                "source_type": orig_frag.source_type,
                "raw_data_hash": orig_frag.raw_data_hash,
                "raw_payload": {}
            }
            temp_fields[field_name] = norm_val
            temp_frag = CandidateFragment(**temp_fields)
            warnings = self.validation_service.validate_fragment(temp_frag)
            if any(w["field"] == field_name for w in warnings):
                has_warnings = True

            # 3. Consensus Agreement Count (how many fragments support this exact normalized value)
            consensus_count = sum(1 for v in values if v.strip().lower() == val.strip().lower()) - 1

            # 4. Confidence Evaluation
            conf_meta = self.confidence_engine.calculate_field_confidence(
                field_name=field_name,
                value=norm_val,
                source_type=orig_frag.source_type,
                has_validation_errors=has_warnings,
                normalization_success=norm_success,
                agreement_count=consensus_count
            )

            prov_meta = self.provenance_engine.create_provenance(
                field_name=field_name,
                raw_value=orig_frag.raw_payload if orig_frag.source_type == "recruiter_notes" else val,
                fragment=orig_frag
            )
            
            field_meta = FieldMetadata(provenance=prov_meta, confidence=conf_meta)
            
            comp_val = CompetingValue(
                value=norm_val,
                source_id=orig_frag.source_id,
                source_type=orig_frag.source_type,
                confidence_score=conf_meta.score,
                normalization_success=norm_success,
                validation_success=not has_warnings
            )
            
            competing_candidates.append((norm_val, field_meta, comp_val))

        # 5. Resolve Conflicts
        resolver_inputs = [(item[0], item[1]) for item in competing_candidates]
        winner_val, winner_meta = self.resolver.resolve(resolver_inputs)

        # Build list of competing value entities and separate winner
        all_competing = [item[2] for item in competing_candidates]
        
        # Build history list of competing metadata
        history_list = [item[1] for item in competing_candidates if item[0] != winner_val]

        selection_reason = (
            f"Selected value '{winner_val}' from source '{winner_meta.provenance.source_id}' "
            f"with confidence score {winner_meta.confidence.score}. "
            f"Resolution based on source type credibility weightings and consensus agreement counts."
        )

        return CanonicalField[str](
            value=winner_val,
            metadata=winner_meta,
            history=history_list,
            competing_values=all_competing,
            selection_reason=selection_reason
        )

    def _merge_collection_field(self, field_name: str, values: List[str], fragments: List[CandidateFragment], normalizer: Any) -> Optional[CanonicalField[List[str]]]:
        if not values:
            return None

        normalized_unique = {}
        competing_list: List[CompetingValue] = []
        history_list: List[FieldMetadata] = []
        
        # Gather all unique values and compile their metadata
        for val in values:
            # Find originating fragment
            orig_frag = next(f for f in fragments if val in getattr(f, field_name))
            
            norm_val = val
            norm_success = True
            try:
                norm_val = normalizer.normalize(val)
            except Exception:
                norm_success = False

            # Validation
            has_warnings = False
            temp_fields = {
                "fragment_id": orig_frag.fragment_id,
                "source_id": orig_frag.source_id,
                "source_type": orig_frag.source_type,
                "raw_data_hash": orig_frag.raw_data_hash,
                "raw_payload": {}
            }
            temp_fields[field_name] = [norm_val]
            temp_frag = CandidateFragment(**temp_fields)
            warnings = self.validation_service.validate_fragment(temp_frag)
            if any(w["field"] == field_name for w in warnings):
                has_warnings = True

            # Consensus
            consensus_count = sum(1 for v in values if v.strip().lower() == val.strip().lower()) - 1

            # Confidence
            conf_meta = self.confidence_engine.calculate_field_confidence(
                field_name=field_name,
                value=norm_val,
                source_type=orig_frag.source_type,
                has_validation_errors=has_warnings,
                normalization_success=norm_success,
                agreement_count=consensus_count
            )

            prov_meta = self.provenance_engine.create_provenance(
                field_name=field_name,
                raw_value=orig_frag.raw_payload if orig_frag.source_type == "recruiter_notes" else val,
                fragment=orig_frag
            )
            
            field_meta = FieldMetadata(provenance=prov_meta, confidence=conf_meta)
            
            comp_val = CompetingValue(
                value=norm_val,
                source_id=orig_frag.source_id,
                source_type=orig_frag.source_type,
                confidence_score=conf_meta.score,
                normalization_success=norm_success,
                validation_success=not has_warnings
            )
            competing_list.append(comp_val)

            # Store best metadata for each unique normalized value
            if norm_val not in normalized_unique or conf_meta.score > normalized_unique[norm_val][1].confidence.score:
                normalized_unique[norm_val] = (field_meta, orig_frag)
            else:
                history_list.append(field_meta)

        # Aggregated values list
        resolved_list = sorted(list(normalized_unique.keys()))

        # Determine winning metadata representing the set (highest confidence item)
        winning_val = max(normalized_unique.keys(), key=lambda k: normalized_unique[k][0].confidence.score)
        winning_meta = normalized_unique[winning_val][0]

        selection_reason = (
            f"Union of all unique normalized values extracted across sources. "
            f"The primary source is '{winning_meta.provenance.source_id}' with the highest individual element confidence score of {winning_meta.confidence.score}."
        )

        return CanonicalField[List[str]](
            value=resolved_list,
            metadata=winning_meta,
            history=history_list,
            competing_values=competing_list,
            selection_reason=selection_reason
        )

    def _merge_experience(self, fragments: List[CandidateFragment]) -> Optional[CanonicalField[List[Dict[str, Any]]]]:
        # Flatten all experience entries
        all_jobs = []
        competing_list = []
        for f in fragments:
            for job in f.experience:
                all_jobs.append((job, f))

        if not all_jobs:
            return None

        # Deduplicate based on company and title
        merged_jobs: Dict[str, Tuple[Dict[str, Any], FieldMetadata]] = {}
        history_list = []

        for job, frag in all_jobs:
            comp_name = job.get("company", "Unknown")
            title = job.get("title", "Engineer")
            dates = job.get("dates", "")
            
            # Normalize company name
            norm_company = comp_name
            norm_success = True
            try:
                norm_company = self.company_normalizer.normalize(comp_name)
            except Exception:
                norm_success = False

            key = f"{norm_company.lower()}|{title.lower()}"
            
            # Build Metadata
            prov = ProvenanceMetadata(source_id=frag.source_id, source_type=frag.source_type, raw_value=job)
            conf = ConfidenceMetadata(
                score=0.9 if frag.source_type == "ats_json" else 0.75, 
                confidence_method="experience_merger"
            )
            meta = FieldMetadata(provenance=prov, confidence=conf)

            competing_list.append(CompetingValue(
                value=f"{norm_company} - {title}",
                source_id=frag.source_id,
                source_type=frag.source_type,
                confidence_score=conf.score,
                normalization_success=norm_success,
                validation_success=True
            ))

            normalized_job = {
                "company": norm_company,
                "title": title,
                "dates": dates
            }

            if key not in merged_jobs:
                merged_jobs[key] = (normalized_job, meta)
            else:
                # Merge dates or keep highest priority source details
                existing_job, existing_meta = merged_jobs[key]
                history_list.append(meta)
                if not existing_job["dates"] and dates:
                    existing_job["dates"] = dates

        resolved_list = [item[0] for item in merged_jobs.values()]
        
        # Best metadata selection
        winning_key = max(merged_jobs.keys(), key=lambda k: merged_jobs[k][1].confidence.score)
        winning_meta = merged_jobs[winning_key][1]

        return CanonicalField[List[Dict[str, Any]]](
            value=resolved_list,
            metadata=winning_meta,
            history=history_list,
            competing_values=competing_list,
            selection_reason="Deduplicated and merged work history timelines using name standardizations."
        )

    def _merge_education(self, fragments: List[CandidateFragment]) -> Optional[CanonicalField[List[Dict[str, Any]]]]:
        all_edu = []
        competing_list = []
        for f in fragments:
            for edu in f.education:
                all_edu.append((edu, f))

        if not all_edu:
            return None

        merged_edu: Dict[str, Tuple[Dict[str, Any], FieldMetadata]] = {}
        history_list = []

        for edu, frag in all_edu:
            school = edu.get("school", "Unknown")
            degree = edu.get("degree", "Degree")
            major = edu.get("major", "")

            # Normalize school suffix
            norm_school = school
            norm_success = True
            try:
                norm_school = self.company_normalizer.normalize(school)
            except Exception:
                norm_success = False

            key = f"{norm_school.lower()}|{degree.lower()}"

            prov = ProvenanceMetadata(source_id=frag.source_id, source_type=frag.source_type, raw_value=edu)
            conf = ConfidenceMetadata(
                score=0.95 if frag.source_type == "ats_json" else 0.8, 
                confidence_method="education_merger"
            )
            meta = FieldMetadata(provenance=prov, confidence=conf)

            competing_list.append(CompetingValue(
                value=f"{norm_school} - {degree}",
                source_id=frag.source_id,
                source_type=frag.source_type,
                confidence_score=conf.score,
                normalization_success=norm_success,
                validation_success=True
            ))

            normalized_edu = {
                "school": norm_school,
                "degree": degree,
                "major": major
            }

            if key not in merged_edu:
                merged_edu[key] = (normalized_edu, meta)
            else:
                existing_edu, existing_meta = merged_edu[key]
                history_list.append(meta)
                if not existing_edu["major"] and major:
                    existing_edu["major"] = major

        resolved_list = [item[0] for item in merged_edu.values()]
        winning_key = max(merged_edu.keys(), key=lambda k: merged_edu[k][1].confidence.score)
        winning_meta = merged_edu[winning_key][1]

        return CanonicalField[List[Dict[str, Any]]](
            value=resolved_list,
            metadata=winning_meta,
            history=history_list,
            competing_values=competing_list,
            selection_reason="Deduplicated and merged academic credentials using school standardizations."
        )
