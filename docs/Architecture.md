# CandidateCore Architecture Design Document

This document outlines the system architecture, component layout, and structural design choices of the Candidate Ingestion and Canonicalization Engine (`CandidateCore`).

---

## 1. Architectural Blueprint & Data Flow

```mermaid
graph TD
    subgraph Input Sources
        CSV[Recruiter CSV]
        ATS[ATS JSON]
        PDF[Resume PDF]
        TXT[Recruiter Notes]
    end

    subgraph Ingestion & Adapters
        CSV_A[CSVAdapter]
        ATS_A[ATSAdapter]
        PDF_A[ResumeAdapter]
        TXT_A[RecruiterNotesAdapter]
    end

    subgraph Services & Processing
        V_S[ValidationService]
        N_S[Normalization Engines]
        M_E[MergeEngine]
        C_R[ConflictResolver]
        C_E[ConfidenceEngine]
        P_E[ProvenanceEngine]
    end

    subgraph Canonical Domain Model
        CF[CandidateFragment]
        CC[CanonicalCandidate]
        H[Linage History]
    end

    CSV --> CSV_A
    ATS --> ATS_A
    PDF --> PDF_A
    TXT --> TXT_A

    CSV_A --> CF
    ATS_A --> CF
    PDF_A --> CF
    TXT_A --> CF

    CF --> V_S
    CF --> N_S
    N_S --> M_E
    M_E --> C_R
    M_E --> C_E
    M_E --> P_E
    C_R --> CC
    P_E --> H
```

---

## 2. Core Architectural Pillars

### I. Immobility of Canonical Profiles
The `CanonicalCandidate` profile is defined as a frozen Pydantic structure. Once written, no service can modify it. Any changes (like semantic enrichments) return a copy-on-write representation.

### II. Unified Raw Ingest (`CandidateFragment`)
Different data formats are parsed, validated, and normalized inside their respective adapters. They exit the adapter layer as a standardized `CandidateFragment`. Merging logic never communicates directly with raw payloads.

### III. Granular Linage Traceability (`CanonicalField[T]`)
Rather than storing simple types, attributes in `CanonicalCandidate` wrap values inside a `CanonicalField[T]`. This metadata track:
* **Provenance**: Source identifier, format type, extraction timestamp, raw input.
* **Confidence**: Mathematical certainty score and the heuristic criteria used.
* **History**: An audit trail of overridden source fields to trace conflicts.

### IV. Field-Level Resilience (Fail Field, Never Fail Pipeline)
If validation checks find errors (e.g. an invalid email format) on specific entries, the pipeline flags the issue under `PipelineStatus.errors` but continues processing other sources and attributes rather than crashing the whole job.

---

## 3. Class Directory & Core Responsibilities

| Directory | Components | Responsibility |
| :--- | :--- | :--- |
| `app/adapters/` | `CSVAdapter`, `ATSAdapter`, `ResumeAdapter`, `RecruiterNotesAdapter` | Parse raw payloads, validate schemas, and compile candidate fragments. |
| `app/models/` | `CandidateFragment`, `CanonicalCandidate`, `FieldMetadata` | Represent data models. |
| `app/services/` | `MergeEngine`, `ConfidenceEngine`, `ProjectionEngine` | Core services executing normalization, conflict resolution, score calculations, and projections. |
| `app/config/` | `settings.py`, `projection_schema.json` | Configuration management. |
| `app/exceptions/` | `custom_exceptions.py`, `handlers.py` | Unified exceptions and global route middleware. |
