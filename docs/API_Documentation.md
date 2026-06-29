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
Uploads multiple documents (e.g. CSVs, resumes, JSON payloads) and runs the pipeline.

* **URL**: `/pipeline/run`
* **Method**: `POST`
* **Content-Type**: `multipart/form-data`
* **Request Payload**:
  * `files`: Binary file upload (multiple allowed)
* **Response**: `200 OK`
```json
{
  "job_id": "8b7fa436-b529-455f-8700-0e12d4d9b62f",
  "status": "COMPLETED",
  "processed_sources": [
    "candidate_info.csv",
    "ats_profile.json"
  ],
  "errors": [
    {
      "field": "contact",
      "error_type": "missing_contact",
      "message": "Both email and phone lists are empty",
      "critical": false
    }
  ],
  "started_at": "2026-06-29T17:00:01Z",
  "completed_at": "2026-06-29T17:00:04Z",
  "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33"
}
```

---

## 3. Apply Schema Projection
Filters, renames, and validates canonical candidate profiles for specific targets.

* **URL**: `/projection`
* **Method**: `POST`
* **Content-Type**: `application/json`
* **Request Payload**:
```json
{
  "candidate": {
    "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33",
    "first_name": {
      "value": "Alex",
      "metadata": {
        "provenance": {
          "source_id": "recruiter_csv",
          "source_type": "recruiter_csv"
        },
        "confidence": { "score": 0.85 }
      },
      "history": []
    }
  },
  "config": {
    "selected_fields": ["first_name"],
    "field_mappings": {
      "first_name": "firstName"
    },
    "exclude_fields": [],
    "required_fields": ["first_name"],
    "output_format": "json"
  }
}
```
* **Response**: `200 OK`
```json
{
  "success": true,
  "projected_data": {
    "firstName": "Alex",
    "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33"
  }
}
```

---

## 4. Semantic Enrichment
Computes and applies taxonomy intelligence layers on top of a canonical profile.

* **URL**: `/semantic-enrichment`
* **Method**: `POST`
* **Content-Type**: `application/json`
* **Request Payload**: (Standard `CanonicalCandidate` object structure)
* **Response**: `200 OK` (Standard `CanonicalCandidate` with enriched metadata fields)
```json
{
  "candidate_id": "a2b0e6df-c1ff-48b4-a4f5-46b5a37f5b33",
  "metadata": {
    "semantic_enrichment_applied": true,
    "inferred_seniority": "Senior Engineer"
  }
}
```
