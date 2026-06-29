# Phase 2 Development Roadmap

This document outlines the planned future features and integrations for the `CandidateCore` engine.

---

## 1. Adapter Implementation Detail
* **Resume PDF Parser**: Integrate `pdfplumber` to extract plain text layout coordinates. Use regex engines or local lightweight models to parse contact details, experience chronologies, and academic accomplishments.
* **LinkedIn & GitHub Adapters**: Build adapters to parse raw API structures or profile exports.

---

## 2. Identity Resolution
* Establish matching logic to decide if incoming fragments belong to existing candidates:
  * Exact email matches.
  * Phonetic first/last name matches with phone/location constraints (Double Metaphone algorithms).
  * Unique ID matches (ATS IDs, LinkedIn profiles).

---

## 3. Advanced Conflict Resolution
* Provide configurable strategies:
  * **Trust Weights**: Assign priority based on source trustworthiness metrics.
  * **Freshness Decay**: Decouple old values using decay half-lives based on extraction timestamps.
  * **User Overrides**: Allow recruiters to manually pin winning fields.

---

## 4. Semantic Enrichment
* Integrate skill taxonomies (like ESCO or custom O*NET mappings) to group skills (e.g. mapping "Python3" and "Py" to "Python", or grouping "FastAPI" and "Flask" under "Python Web Frameworks").
* Deduce experience tenure to predict seniority levels.
