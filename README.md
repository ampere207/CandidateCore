# CandidateCore Canonicalization Engine

`CandidateCore` is a production-quality, deterministic multi-source candidate ingestion and canonicalization pipeline. It transforms heterogeneous and conflicting candidate data from various recruitment sources (ATS JSONs, Recruiter CSVs, raw Resume PDFs, and unstructured Interview Notes) into a single, immutable, and explainable **Canonical Candidate Profile**.

---

## 🚀 Features & Pipeline Stages

CandidateCore executes a highly deterministic data pipeline to resolve conflicts and construct a unified candidate identity. 

1. **Extraction (Adapters):** Intelligently detects and maps incoming raw files (PDF, JSON, CSV, TXT) to their respective adapters, parsing unstructured data into structured `CandidateFragment` objects.
2. **Validation:** Executes schema checks on extracted fragments (e.g., verifying `ats_id` existence, email formats, and required identifying fields) before proceeding.
3. **Normalization:** Standardizes structural anomalies across sources (e.g., standardizing location strings, stripping whitespace, and normalizing dates and phone numbers).
4. **Merge Engine (Conflict Resolution):** Compares fragmented profiles, resolving conflicts using field-specific consensus logic and confidence weighting. Scalar fields take the highest confidence value, while collection fields (skills, links) perform union deduplication.
5. **Confidence Scoring:** Applies a deterministic scoring algorithm to evaluate the reliability of extracted data. Different sources are weighted differently (e.g., ATS data carries a higher base confidence than raw Recruiter notes).
6. **Provenance Tracking:** Every single resolved attribute is wrapped in a `CanonicalField[T]`, carrying a comprehensive audit trail of exactly which file and line it originated from, alongside the rejected competing values.
7. **AI Semantic Enrichment:** Leverages **Gemini 2.5 Flash** to synthesize unstructured recruiter notes and raw candidate profiles into deep qualitative insights (Leadership Signals, Core Strengths, Communication Signals) without hallucinating facts.
8. **Runtime Projection Engine:** Allows exporting the heavy internal Domain Model (CanonicalCandidate) into a lightweight, clean consumer-facing JSON schema (CandidateOutput) using custom mapping configuration, field selection, and aliasing rules.

---

## 🤝 Merge & Conflict Resolution

When CandidateCore processes multiple sources for a single candidate, it inevitably encounters conflicting data (e.g., a recruiter CSV has a different email than the ATS JSON, or the Resume has a newer job title). The pipeline handles this deterministically based on the field type:

1. **Scalar Fields (Names, Locations, etc.)**: 
   The `ConflictResolver` evaluates all competing normalized values. It requests a score from the `ConfidenceEngine` for each competing value. The value with the highest mathematical confidence score is promoted to the final canonical profile. The "losing" values are not deleted; they are preserved inside the `CanonicalField` history audit trail for lineage explainability.

2. **Collection Fields (Emails, Phones, Skills)**: 
   The `MergeEngine` performs intelligent union deduplication. It normalizes all entries (e.g., converting phone numbers to E.164, stripping whitespace and casing from skills) and groups identical items. It then merges the collections, keeping the metadata of the highest confidence source that provided each unique item.

3. **Complex Timelines (Experience, Education)**: 
   Custom merger strategies are applied. For work experience, the engine normalizes company names and job titles. If multiple sources provide the same job (e.g., a Resume and an ATS), they are merged into a single entry. If one source has missing date ranges but another provides them, the engine stitches the dates together into a unified timeline.

---

## 🧮 Confidence Scoring Heuristics

The `ConfidenceEngine` calculates a mathematical certainty score (0.0 to 1.0) for every extracted field to systematically resolve conflicts across heterogeneous sources. The final score is computed using a multi-factor deterministic algorithm:

1. **Base Source Reliability:**
   Every field starts with a base score depending on its origin:
   * **ATS JSON (`ats_json`)**: `0.95` (Highest trust, structured system of record)
   * **Resume PDF (`resume_pdf`)**: `0.85` (High trust, primary candidate artifact)
   * **Recruiter CSV (`recruiter_csv`)**: `0.75` (Medium trust, prone to manual entry errors)
   * **Recruiter Notes (`recruiter_notes`)**: `0.60` (Lowest trust, unstructured qualitative data)

2. **Validation Penalties:**
   * **`-0.20` Penalty**: Applied if the field triggered any schema validation warnings (e.g., malformed email, missing required attributes).

3. **Normalization Adjustments:**
   * **`+0.05` Bonus**: Awarded if the field was successfully normalized into a standard format.
   * **`-0.15` Penalty**: Applied if normalization failed and the engine had to fall back to the raw payload string.

4. **Consensus Agreement Bonus:**
   * **`+0.10` Bonus (per matching source)**: Awarded for every *other* source that independently provided the exact same normalized value. Capped at a maximum bonus of `+0.20`.

The final aggregated score is bounded between `[0.0, 1.0]` and rounded to two decimal places to guarantee determinism. The Conflict Resolver then simply promotes the competing field with the highest confidence score to the Canonical Profile.

---

## 🏗️ Core Architecture Principles

* **Separation of Concerns:** The engine strictly separates the internal rich domain model (which holds provenance, confidence, and conflict metadata) from the external output model (which consumers use).
* **Immutability:** Once compiled, `CanonicalCandidate` objects are strictly frozen and immutable to guarantee data lineage integrity.
* **Fail Field, Never Fail Pipeline:** The pipeline is fault-tolerant. Field normalization or parsing issues raise handled warnings rather than crashing the core execution loop.

---

## 🛠️ Getting Started

### 1. Prerequisites
Ensure you have the following installed locally on your machine:
* **Python 3.12+**
* **Node.js 20+**

### 2. Configuration & API Keys
To utilize the AI Semantic Enrichment phase, you must configure a Gemini API key.
Create a `.env` file in the `backend/` directory:
```bash
echo "GEMINI_API_KEY=your_gemini_api_key_here" > backend/.env
```

### 3. Initial Workspace Setup
Run the bootstrap setup script from the root of the project to configure python virtual environments and download all required backend and frontend dependencies:
```bash
bash scripts/setup.sh
```

### 4. Run the Application

You will need two separate terminal windows to run both the backend and frontend concurrently.

* **Start Backend API (FastAPI):**
  This will launch the engine on [http://localhost:8000](http://localhost:8000).
  ```bash
  bash scripts/run_backend.sh
  ```

* **Start Frontend UI (Next.js):**
  This will launch the interactive UI on [http://localhost:3000](http://localhost:3000).
  ```bash
  bash scripts/run_frontend.sh
  ```

### 5. Running a Pipeline Job
1. Open the Frontend UI at `http://localhost:3000`.
2. Upload one or multiple candidate data sources simultaneously (e.g., a `.pdf` resume, a `.json` ATS dump, and a `.txt` notes file).
3. Click **Run Pipeline**.
4. The system will automatically detect the file types, extract, merge, and present the fully canonicalized profile alongside the provenance audit trail and semantic insights!
5. Navigate to the Custom Export Projection section to rename and map specific fields into a clean output schema.

---

## 📊 Example Inputs & Output Schemas

CandidateCore accepts a variety of heterogeneous data formats and synthesizes them into a clean, predictable output model.

> [!NOTE]
> **Why no direct LinkedIn or GitHub APIs?**
> A core architectural decision of CandidateCore is to maintain absolute data sovereignty and zero external API dependencies for primary data ingestion. By forcing ingestion to happen via standard offline artifacts (like exported JSON dumps, PDFs, or CSVs), the engine avoids third-party rate limits, unexpected API deprecations, expensive enterprise API tier lock-ins, and data-sharing compliance risks. The system remains completely deterministic and locally runnable.

### 📥 Example Input: ATS JSON (`candidate.json`)
```json
{
  "ats_id": "ATS-88219",
  "candidate_profile": {
    "first_name": "Rahul",
    "last_name": "Sharma",
    "emails": ["rahul.sharma@gmail.com"],
    "skills": ["Python", "Docker", "Kubernetes"]
  }
}
```

### 📥 Example Input: Recruiter CSV (`candidate.csv`)
```csv
Candidate Name,Email,Phone,Current Company,Location
Rahul Sharma,rahul.s@outlook.com,98765-43210,Razorpay,Bengaluru
```

### 📤 Final Projected Output (`CandidateOutput` Schema)
After the pipeline extracts the inputs, merges them, resolves conflicts using confidence heuristics, and applies AI semantic enrichment, the `ProjectionEngine` flattens the heavy internal domain model into a clean, consumer-ready JSON structure:

```json
{
  "candidate_id": "2b23101b-87a7-4cb6-bde3-43c2fe5cf54b",
  "full_name": "Rahul Sharma",
  "emails": [
    "rahul.sharma@gmail.com",
    "rahul.s@outlook.com"
  ],
  "phones": [
    "+91 9876543210"
  ],
  "location": "Bengaluru, India",
  "skills": [
    "Python",
    "Docker",
    "Kubernetes"
  ],
  "experience": [
    {
      "company": "Razorpay",
      "title": "Backend Engineer",
      "dates": "Jan 2023 - Present"
    }
  ],
  "education": [],
  "metadata": {
    "completeness_score": 0.85,
    "resolved_sources_count": 4,
    "merged_at": "2026-07-01T14:30:00Z",
    "links": {
      "linkedin": "https://linkedin.com/in/rahulsharma",
      "github": "https://github.com/rahul-sharma-dev"
    },
    "headline": "Backend Engineer | Scalable Systems",
    "semantic_enrichment_applied": true,
    "semantic_enrichment": {
      "success": true,
      "professional_summary": "Strong backend developer with expertise in distributed systems...",
      "core_strengths": ["System Design", "Microservices"],
      "recruiter_insights": "Solid candidate. Good background in payments."
    }
  }
}
```

---

## 🧪 Testing

We verify model constraints, adapter detection rules, async enrichment capabilities, and routing endpoints using `pytest`.

Execute the backend test suite:
```bash
backend/.venv/bin/pytest backend/
```
