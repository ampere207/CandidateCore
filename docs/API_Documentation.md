# CandidateCore API Specification

This document details the REST API specifications for the CandidateCore canonicalization service.

---

## 1. Health Status
Returns check indicators on service connectivity.

* **URL**: `/health`
* **Method**: `GET`
* **Response**: `200 OK`
```json
{
  "status": "healthy",
  "timestamp": "2026-06-29T17:00:00Z",
  "service": "CandidateCore Ingestion Pipeline Engine"
}
```

---

## 2. Ingest and Canonicalize
Uploads multiple documents (e.g. CSVs, resumes, JSON payloads) and runs the pipeline. Optionally triggers asynchronous Semantic Enrichment via Gemini.

* **URL**: `/pipeline/run`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Request Payload**:
  * `files`: Binary file upload (multiple allowed)
  * `enable_enrichment`: Boolean (Form Data, default `true`)
* **Response**: `200 OK` (Returns the Pipeline Status)
```json
{
  "job_id": "8b7fa436-b529-455f-8700-0e12d4d9b62f",
  "status": "COMPLETED",
  "processed_sources": [
    "candidate_info.csv",
    "ats_profile.json"
  ],
  "errors": [],
  "started_at": "2026-06-29T17:00:01Z",
  "completed_at": "2026-06-29T17:00:15Z",
  "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33"
}
```

---

## 3. Retrieve Candidate
Retrieves a resolved Canonical Candidate Profile by ID mapped to the consumer-facing `CandidateOutput` schema.

* **URL**: `/pipeline/candidate/{candidate_id}`
* **Method**: `GET`
* **Response**: `200 OK`
```json
{
  "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33",
  "full_name": "Alex Rivera",
  "emails": ["alex@example.com"],
  "phones": ["+1 555-0100"],
  "location": "San Francisco, CA",
  "skills": ["Python", "React", "AWS"],
  "experience": [
    {
      "company": "Tech Corp",
      "title": "Senior Engineer",
      "dates": "2020-01 to Present"
    }
  ],
  "education": [],
  "metadata": {
    "completeness_score": 0.85,
    "semantic_enrichment_applied": true,
    "semantic_enrichment": {
      "professional_summary": "Highly skilled backend developer...",
      "core_strengths": ["System Design"]
    }
  }
}
```

---

## 4. Apply Schema Projection
Filters, renames, and validates canonical candidate profiles for specific consumer targets.

* **URL**: `/projection/{candidate_id}`
* **Method**: `POST`
* **Content-Type**: `application/json`
* **Request Payload**: (ProjectionConfig)
```json
{
  "selected_fields": ["full_name"],
  "field_mappings": {
    "full_name": "candidateName"
  },
  "exclude_fields": [],
  "required_fields": ["full_name"],
  "output_format": "json"
}
```
* **Response**: `200 OK` (Returns the customized `CandidateOutput` projection)
```json
{
  "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33",
  "candidateName": "Alex Rivera",
  "metadata": {}
}
```

---

## 5. Semantic Enrichment (Standalone)
Computes and applies taxonomy intelligence layers on top of a canonical profile using an LLM. Note that this is usually invoked automatically within `/pipeline/run`.

* **URL**: `/semantic-enrichment/{candidate_id}`
* **Method**: `POST`
* **Response**: `200 OK` (Returns `CandidateOutput` with enriched metadata fields)
