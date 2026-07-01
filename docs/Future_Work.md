# CandidateCore Future Development Roadmap

This document outlines the planned future features and integrations for the `CandidateCore` engine.

---

## 1. Advanced Identity Resolution
* Establish deeper matching logic to decide if incoming fragments belong to existing candidates across long periods of time:
  * Phonetic first/last name matches with location constraints (Double Metaphone algorithms).
  * Strict deduplication merging for identical LinkedIn URLs or GitHub profiles.

---

## 2. Advanced Conflict Resolution
* Provide configurable strategies:
  * **Freshness Decay**: Decouple old values using decay half-lives based on extraction timestamps (e.g., an ATS record from 2 years ago loses confidence against a Resume from today).
  * **User Overrides**: Allow recruiters to manually pin winning fields in the UI, overriding the deterministic Merge Engine.

---

## 3. Expanded Adapter Ecosystem
* **LinkedIn & GitHub API Adapters**: Build adapters to parse raw API structures directly from LinkedIn Recruiter or GitHub profiles without manual data entry.
* **Webhook Listeners**: Expose ingestion endpoints for ATS systems (like Greenhouse or Lever) to automatically push updates into the pipeline.

---

## 4. Enhanced Semantic Enrichment Taxonomy
* The current Semantic Enrichment uses Gemini to infer qualitative strengths. Future iterations will integrate strict skill taxonomies (like ESCO or custom O*NET mappings) to semantically group identical skills (e.g., mapping "Python3" and "Py" strictly to "Python", or grouping "FastAPI" and "Flask" under "Python Web Frameworks").
* Use LLM projections to predict candidate retention or flight risks based on historical tenure data.

---

## 5. Persistence & Multi-tenancy
* Currently, the engine uses an in-memory `CANDIDATE_STORE` for rapid processing.
* **Database Integration**: Implement a robust PostgreSQL/MongoDB storage layer for persistent canonical profiles and fragment histories.
* **Multi-tenancy**: Support isolated workspaces for different recruiting agencies or enterprise departments.
