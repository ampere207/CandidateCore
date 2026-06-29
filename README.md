# CandidateCore Canonicalization Engine

`CandidateCore` is a production-quality foundation for a deterministic multi-source candidate ingestion and canonicalization pipeline. It transforms heterogeneous candidate data from recruiter sheets (CSVs), applicant tracking systems (ATS JSON), resumes (PDFs), and interview writeups (Notes) into a single, immutable, and explainable **Canonical Candidate Profile**.

---

## 🏗️ Core Architecture Design
* **Immutability**: Once compiled, `CanonicalCandidate` objects are frozen.
* **Granular Traceability**: Every canonical attribute is wrapped in `CanonicalField[T]`, carrying extraction provenance, confidence levels, and an override audit trail.
* **Resilience**: The pipeline follows a **"Fail Field, Never Fail Pipeline"** principle where field normalization/parsing issues raise handled warnings rather than crashing execution.

---

## 🛠️ Getting Started

### 1. Prerequisites
Ensure you have **Python 3.12** and **Node.js 20+** installed locally.

### 2. Initial Setup
Run the bootstrap setup script to configure python virtual environments and download dependencies:
```bash
bash scripts/setup.sh
```

### 3. Run Servers

* **Start Backend (FastAPI)** on [http://localhost:8000](http://localhost:8000):
  ```bash
  bash scripts/run_backend.sh
  ```

* **Start Frontend (Next.js)** on [http://localhost:3000](http://localhost:3000):
  ```bash
  bash scripts/run_frontend.sh
  ```

---

## 🧪 Testing

We verify model constraints, adapter detection rules, services, and routing endpoints using `pytest`.

Execute tests:
```bash
backend/.venv/bin/pytest backend/
```
