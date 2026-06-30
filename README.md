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

## 🧪 Testing

We verify model constraints, adapter detection rules, async enrichment capabilities, and routing endpoints using `pytest`.

Execute the backend test suite:
```bash
backend/.venv/bin/pytest backend/
```
