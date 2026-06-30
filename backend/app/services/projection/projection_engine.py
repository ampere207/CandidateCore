import re
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional
from datetime import datetime, timezone
from app.models.canonical_candidate import CanonicalCandidate
from app.models.projection_config import ProjectionConfig
from app.models.candidate_output import (
    CandidateOutput,
    LocationOutput,
    LinksOutput,
    SkillItemOutput,
    ExperienceItemOutput,
    EducationItemOutput,
    ProvenanceItemOutput,
    MetadataOutput,
    AISemanticSummaryOutput
)
from app.exceptions.custom_exceptions import ProjectionException

class ProjectionEngine(ABC):
    """
    Interface for translating and flattening CanonicalCandidates into CandidateOutput.
    """

    @abstractmethod
    def project(self, candidate: CanonicalCandidate, config: Optional[ProjectionConfig] = None) -> CandidateOutput:
        """
        Transforms CanonicalCandidate to CandidateOutput according to ProjectionConfig rules.
        """
        pass

class DefaultProjectionEngine(ProjectionEngine):
    """
    Core implementation of the ProjectionEngine mapping and transforming fields.
    Translates internal CanonicalCandidates into external CandidateOutputs.
    """

    def project(self, candidate: CanonicalCandidate, config: Optional[ProjectionConfig] = None) -> CandidateOutput:
        try:
            # 1. full_name from first_name + last_name
            fn = candidate.first_name.value if candidate.first_name else ""
            ln = candidate.last_name.value if candidate.last_name else ""
            full_name = f"{fn} {ln}".strip()

            # 2. emails & phones
            emails = candidate.emails.value if candidate.emails else []
            phones = candidate.phones.value if candidate.phones else []

            # 3. Parse location into city, region, country
            loc_str = candidate.location.value if candidate.location else ""
            city = None
            region = None
            country = None
            if loc_str:
                parts = loc_str.split(",")
                if len(parts) >= 3:
                    city = parts[0].strip()
                    region = parts[1].strip()
                    country = parts[2].strip()
                elif len(parts) == 2:
                    city = parts[0].strip()
                    region = parts[1].strip()
                elif len(parts) == 1:
                    city = parts[0].strip()
            location = LocationOutput(city=city, region=region, country=country)

            # 4. Links & Headline
            links_meta = candidate.metadata.get("links", {})
            links = LinksOutput(
                linkedin=links_meta.get("linkedin"),
                github=links_meta.get("github"),
                portfolio=links_meta.get("portfolio"),
                other=links_meta.get("other", [])
            )
            headline = candidate.metadata.get("headline")

            # 5. Calculate years_experience
            total_years = 0.0
            has_exp = False
            if candidate.experience:
                for job in candidate.experience.value:
                    dates = job.get("dates") or ""
                    if not dates:
                        continue
                    years = re.findall(r"\b(19\d{2}|20\d{2})\b", dates)
                    if not years:
                        continue
                    has_exp = True
                    start_yr = int(years[0])
                    is_pres = any(x in dates.lower() for x in ["present", "current", "now"])
                    if is_pres:
                        end_yr = datetime.now(timezone.utc).year
                    elif len(years) > 1:
                        end_yr = int(years[1])
                    else:
                        end_yr = start_yr + 1
                    diff = end_yr - start_yr
                    if diff > 0:
                        total_years += diff
            years_experience = round(total_years, 1) if has_exp else None

            # 6. Skills mapping
            skills_out = []
            if candidate.skills:
                field_conf = candidate.skills.metadata.confidence.score if candidate.skills.metadata else 1.0
                field_source = candidate.skills.metadata.provenance.source_type if candidate.skills.metadata else "ats_json"
                for sk in candidate.skills.value:
                    sources = [field_source]
                    for comp in candidate.skills.competing_values:
                        if comp.value and sk.lower() in str(comp.value).lower():
                            if comp.source_type not in sources:
                                sources.append(comp.source_type)
                    skills_out.append(SkillItemOutput(
                        name=sk,
                        confidence=field_conf,
                        sources=sources
                    ))

            # 7. Experience list
            exp_out = []
            if candidate.experience:
                for job in candidate.experience.value:
                    company = job.get("company", "Unknown")
                    title = job.get("title", "Engineer")
                    dates = job.get("dates", "")
                    start = "Unknown"
                    end = None
                    if dates:
                        parts = dates.split("-")
                        if len(parts) == 2:
                            start = parts[0].strip()
                            end = parts[1].strip()
                        elif len(parts) == 1:
                            start = parts[0].strip()
                    exp_out.append(ExperienceItemOutput(
                        company=company,
                        title=title,
                        start=start,
                        end=end,
                        summary=job.get("summary")
                    ))

            # 8. Education list
            edu_out = []
            if candidate.education:
                for edu in candidate.education.value:
                    institution = edu.get("school", "Unknown")
                    degree = edu.get("degree", "Degree")
                    field = edu.get("major")
                    end_year = None
                    for key in ["end_year", "graduation_year", "grad_year", "year", "date", "dates"]:
                        val = edu.get(key)
                        if val:
                            if isinstance(val, int):
                                end_year = val
                                break
                            match = re.search(r"\b(19\d{2}|20\d{2})\b", str(val))
                            if match:
                                end_year = int(match.group(1))
                                break
                    edu_out.append(EducationItemOutput(
                        institution=institution,
                        degree=degree,
                        field=field,
                        end_year=end_year
                    ))

            # 9. Provenance simplified array
            prov_out = []
            for f_name in ["first_name", "last_name", "emails", "phones", "location", "skills", "experience", "education"]:
                f_val = getattr(candidate, f_name, None)
                if f_val and f_val.metadata:
                    prov_out.append(ProvenanceItemOutput(
                        field=f_name,
                        selected_source=f_val.metadata.provenance.source_id,
                        confidence=f_val.metadata.confidence.score,
                        reason=f_val.selection_reason or "Consolidated authoritative values."
                    ))

            # 10. Overall confidence
            scores = []
            for f_name in ["first_name", "last_name", "emails", "phones", "location", "skills", "experience", "education"]:
                f_val = getattr(candidate, f_name, None)
                if f_val and f_val.metadata and f_val.metadata.confidence:
                    scores.append(f_val.metadata.confidence.score)
            overall_confidence = round(sum(scores) / len(scores), 2) if scores else 0.0

            # 11. Metadata mapping
            gen_at_str = candidate.metadata.get("merged_at")
            generated_at = datetime.fromisoformat(gen_at_str) if gen_at_str else datetime.now(timezone.utc)
            metadata = MetadataOutput(
                generated_at=generated_at,
                pipeline_version="v1.0.0",
                sources_processed=candidate.metadata.get("resolved_sources_count", 1),
                ai_enrichment_enabled=candidate.metadata.get("semantic_enrichment_applied", False)
            )

            # 12. AI summary mapping
            ai_summary = None
            if candidate.metadata.get("semantic_enrichment_applied"):
                se = candidate.metadata.get("semantic_enrichment", {})
                insights_list = []
                raw_insights = se.get("recruiter_insights")
                if isinstance(raw_insights, list):
                    insights_list = raw_insights
                elif isinstance(raw_insights, str):
                    insights_list = [raw_insights]
                ai_summary = AISemanticSummaryOutput(
                    professional_summary=se.get("professional_summary"),
                    core_strengths=se.get("core_strengths", []),
                    recommended_roles=se.get("recommended_roles", []),
                    technical_highlights=se.get("technical_highlights", []),
                    leadership_signals=se.get("leadership_signals", []),
                    communication_signals=se.get("communication_signals", []),
                    interview_focus=se.get("interview_focus_areas") or se.get("interview_focus") or se.get("interview_focus_areas", []),
                    recruiter_insights=insights_list,
                    potential_concerns=se.get("potential_concerns", [])
                )

            # --- Apply Dynamic Validation pre-checks (Required Fields check) ---
            if config and config.required_fields:
                for req in config.required_fields:
                    if config.exclude_fields and req in config.exclude_fields:
                        raise ProjectionException(f"Required field '{req}' is excluded.")
                    if config.selected_fields:
                        if req == "first_name" and "first_name" not in config.selected_fields and "full_name" not in config.selected_fields:
                            raise ProjectionException(f"Required field 'first_name' is not in selected whitelist.")
                        elif req == "last_name" and "last_name" not in config.selected_fields and "full_name" not in config.selected_fields:
                            raise ProjectionException(f"Required field 'last_name' is not in selected whitelist.")
                        elif req not in ["first_name", "last_name"] and req not in config.selected_fields:
                            raise ProjectionException(f"Required field '{req}' is not in selected whitelist.")

                    val = None
                    if req in ["first_name", "last_name", "full_name"]:
                        val = full_name
                    elif req == "emails":
                        val = emails
                    elif req == "phones":
                        val = phones
                    elif req == "location":
                        val = location.city or location.region
                    elif req == "skills":
                        val = skills_out
                    elif req == "experience":
                        val = exp_out
                    elif req == "education":
                        val = edu_out
                    
                    if val is None or (isinstance(val, (list, dict, str)) and not val):
                        raise ProjectionException(f"Required field '{req}' is missing or empty in the projected output.")

            # --- Apply Dynamic Filters (Exclusion & Whitelist) ---
            if config:
                if config.exclude_fields:
                    for excl in config.exclude_fields:
                        if excl in ["first_name", "last_name", "full_name"]:
                            full_name = ""
                        elif excl == "emails":
                            emails = []
                        elif excl == "phones":
                            phones = []
                        elif excl == "location":
                            location = LocationOutput()
                        elif excl == "skills":
                            skills_out = []
                        elif excl == "experience":
                            exp_out = []
                        elif excl == "education":
                            edu_out = []
                        elif excl == "links":
                            links = LinksOutput()
                        elif excl == "headline":
                            headline = None
                        elif excl == "ai_semantic_summary":
                            ai_summary = None

                if config.selected_fields:
                    if "full_name" not in config.selected_fields and "first_name" not in config.selected_fields and "last_name" not in config.selected_fields:
                        full_name = ""
                    if "emails" not in config.selected_fields:
                        emails = []
                    if "phones" not in config.selected_fields:
                        phones = []
                    if "location" not in config.selected_fields:
                        location = LocationOutput()
                    if "skills" not in config.selected_fields:
                        skills_out = []
                    if "experience" not in config.selected_fields:
                        exp_out = []
                    if "education" not in config.selected_fields:
                        edu_out = []
                    if "links" not in config.selected_fields:
                        links = LinksOutput()
                    if "headline" not in config.selected_fields:
                        headline = None
                    if "ai_semantic_summary" not in config.selected_fields:
                        ai_summary = None

            return CandidateOutput(
                candidate_id=candidate.candidate_id,
                full_name=full_name,
                emails=emails,
                phones=phones,
                location=location,
                links=links,
                headline=headline,
                years_experience=years_experience,
                skills=skills_out,
                experience=exp_out,
                education=edu_out,
                provenance=prov_out,
                overall_confidence=overall_confidence,
                metadata=metadata,
                ai_semantic_summary=ai_summary
            )

        except ProjectionException:
            raise
        except Exception as e:
            raise ProjectionException(f"Error executing projection: {str(e)}")
