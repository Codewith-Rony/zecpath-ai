# Zecpath AI – Automated ATS Evaluation Engine

[![Python Version](https://img.shields.io/badge/python-3.12.0-blue.svg)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-183%20passed-brightgreen.svg)]()
[![FastAPI](https://img.shields.io/badge/FastAPI-0.162.0-009688.svg)](https://fastapi.tiangolo.com/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)]()
[![Status](https://img.shields.io/badge/status-Day%2020%20Verified-blue.svg)]()

**Zecpath AI** is an explainable, multi-dimensional Applicant Tracking System (ATS) evaluation engine built with Python. It parses resumes in PDF and DOCX formats, masks sensitive personal identifiers (PII), evaluates candidates across four qualification dimensions against structured job descriptions, and generates transparent, recruiter-friendly score breakdowns and candidate rankings.

> [!IMPORTANT]
> **Heuristic Decision-Support System**: Zecpath AI is strictly an **assistive decision-support tool**, not an autonomous hiring system. The generated ATS score (0–100) reflects algorithmic similarity to a job description. The system incorporates algorithmic safeguards (such as data coverage thresholds) to mandate human review when extracted evidence is incomplete.

---

## Table of Contents

- [Key Features](#key-features)
- [Technology Stack](#technology-stack)
- [System Architecture & Workflow](#system-architecture--workflow)
- [ATS Scoring Methodology](#ats-scoring-methodology)
  - [Component Weights & Role Overrides](#component-weights--role-overrides)
  - [Dynamic Weight Renormalization](#dynamic-weight-renormalization)
  - [Data Coverage Safeguard](#data-coverage-safeguard)
  - [Semantic Similarity Modes](#semantic-similarity-modes)
- [Project Structure](#project-structure)
- [Installation & Environment Setup](#installation--environment-setup)
- [CLI Usage](#cli-usage)
  - [1. Single Candidate ATS Scoring](#1-single-candidate-ats-scoring)
  - [2. Batch Candidate Ranking & Shortlisting](#2-batch-candidate-ranking--shortlisting)
- [REST API Service](#rest-api-service)
  - [Running the API Server](#running-the-api-server)
  - [Interactive Swagger UI](#interactive-swagger-ui)
  - [API Endpoint Reference](#api-endpoint-reference)
- [Sample Outputs](#sample-outputs)
- [Automated Testing](#automated-testing)
- [Performance Optimization Benchmarks](#performance-optimization-benchmarks)
- [Production Readiness & Known Limitations](#production-readiness--known-limitations)
- [Future Roadmap](#future-roadmap)
- [Documentation Directory](#documentation-directory)

---

## Key Features

- **Multi-Format Document Ingestion**: Robust text extraction from `.pdf` (PyMuPDF) and `.docx` (`python-docx`) resumes, and `.txt`, `.pdf`, `.docx` job descriptions.
- **Privacy & Fairness Safeguards**: Automatic regex-based masking of candidate email addresses (`[EMAIL]`) and telephone numbers (`[PHONE]`) prior to feature extraction.
- **Multi-Dimensional Scoring**: Evaluates candidates across **Skill Match** (40%), **Experience Relevance** (25%), **Education Alignment** (15%), and **Semantic Similarity** (20%).
- **Dynamic Renormalization**: If a resume lacks a component (e.g., an entry-level fresher without employment history), missing components are excluded and available weights scale dynamically to 100%.
- **Recruiter Coverage Safeguard**: Programmatically flags resumes with `manual_review_required = True` whenever data coverage drops below 80%.
- **Candidate Triage & Shortlisting**: Classifies applicants into actionable recruitment tiers: `Shortlist`, `Review`, `Reject Recommendation`, or `Manual Review`.
- **Dual Interface**: Full CLI suite for batch terminal workflows and FastAPI REST API with interactive Swagger UI.
- **High Test Quality**: 183 automated tests running in under 5 seconds with storage isolation fixtures.

---

## Technology Stack

| Layer | Technologies |
| :--- | :--- |
| **Language** | Python 3.12 (compatible with Python 3.10+, tested on 3.12.0) |
| **API Framework** | FastAPI 0.162.0, Uvicorn 0.54.0, Starlette, python-multipart |
| **Document Parsers** | PyMuPDF (`fitz`), `python-docx` |
| **Data Validation** | Pydantic v2 (`BaseModel`, `Field`, `model_validator`) |
| **Testing** | Pytest 9.1.1, Starlette `TestClient`, HTTPX |
| **NLP & Semantic** | Token-bigram cosine similarity (standard); optional `sentence-transformers` |

---

## System Architecture & Workflow

```
[Candidate Resume]              [Job Description]
   (PDF / DOCX)                   (TXT / PDF / DOCX)
        │                                 │
        ▼                                 ▼
┌──────────────────┐             ┌──────────────────┐
│ Document Parsers │             │    JD Parser     │
│ (fitz / docx)    │             │  (Regex / Dict)  │
└───────┬──────────┘             └────────┬─────────┘
        │ Raw Text                        │ Role & Requirements
        ▼                                 │
┌──────────────────┐                      │
│ Privacy Masker   │                      │
│ (Email/Phone PII)│                      │
└───────┬──────────┘                      │
        │ Masked Text                     │
        ├─────────────────────────────────┤
        ▼                                 ▼
┌──────────────────┬──────────────────┬──────────────────┬──────────────────┐
│   Skill Match    │    Experience    │    Education     │     Semantic     │
│  (Dict & Regex)  │ (Timeline / Role)│  (Degree / Tier) │ (Bigram Overlap) │
│   Weight: 40%    │   Weight: 25%    │   Weight: 15%    │   Weight: 20%    │
└────────┬─────────┴────────┬─────────┴────────┬─────────┴────────┬─────────┘
         │                  │                  │                  │
         └──────────────────┼──────────────────┼──────────────────┘
                            ▼
             ┌─────────────────────────────┐
             │    Weighted ATS Scorer      │
             │  - Dynamic Weight Renorm    │
             │  - Data Coverage Percentage │
             │  - Manual Review Safeguard  │
             └──────────────┬──────────────┘
                            │ Candidate Report
                            ▼
             ┌─────────────────────────────┐
             │ Candidate Pipeline & Ranker │
             │  - Stable TimSort           │
             │  - Threshold Classification │
             └──────────────┬──────────────┘
                            │
            ┌───────────────┴───────────────┐
            ▼                               ▼
┌───────────────────────┐       ┌───────────────────────┐
│      CLI Output       │       │    REST API Output    │
│ (JSON & Text Reports) │       │ (FastAPI JSON Schema) │
└───────────────────────┘       └───────────────────────┘
```

---

## ATS Scoring Methodology

### Component Weights & Role Overrides

Scoring weights are defined in [`scoring/ats_scorer.py`](scoring/ats_scorer.py). If a target role matches a configured profile in `ROLE_WEIGHTS`, role-specific weights are applied; otherwise, the engine uses `DEFAULT_WEIGHTS`.

| Component | Default Weights (`DEFAULT_WEIGHTS`) | Software Developer (`ROLE_WEIGHTS`) | AI Engineer (`ROLE_WEIGHTS`) | Evaluation Logic |
| :--- | :---: | :---: | :---: | :--- |
| **Skill Match** | **40%** | **45%** | **35%** | Matches candidate skills against JD required skills (80% weight) and preferred skills (20% weight) loaded from `data/skill_dictionary.json`. |
| **Experience Relevance** | **25%** | **25%** | **25%** | Evaluates job title similarity (60%) and responsibility overlap (40%). Checks duration against requirements and flags employment gaps. |
| **Education Alignment** | **15%** | **10%** | **10%** | Awards up to 30 points for recognized degree levels (Bachelors, Masters, PhD) and up to 70 points for discipline relevance. |
| **Semantic Similarity** | **20%** | **20%** | **30%** | Measures global document alignment between resume text and JD text. |

### Dynamic Weight Renormalization

When a component cannot be extracted from a resume (e.g., an entry-level candidate with no prior job entries), the score is marked as `None` and excluded from the denominator. Available weights dynamically scale to 100%:

$$\text{Renormalized Weight}_i = \frac{\text{Nominal Weight}_i}{\sum_{j \in \text{Available}} \text{Nominal Weight}_j}$$

### Data Coverage Safeguard

To prevent incomplete resumes from receiving inflated scores, the system monitors data coverage:

$$\text{Coverage Percentage} = \sum_{j \in \text{Available}} \text{Nominal Weight}_j$$

- **Safeguard Rule**: If `coverage_percentage < 80.0%`, the system automatically sets:
  ```python
  manual_review_required = True
  ```
- **Recruiter Action**: The candidate's classification recommendation is set to `manual_review`, mandating human inspection before any automated progression.

### Semantic Similarity Modes

1. **`token-bigram-fallback` (Default / Standard)**:
   - Offline, fast, and deterministic. Builds sparse frequency vectors using word unigrams and bigrams, calculating cosine similarity. Requires no GPU or heavyweight model downloads.
2. **Dense Sentence Embeddings (Optional)**:
   - When `sentence-transformers` is installed, the engine automatically detects it and uses dense contextual embeddings (`all-MiniLM-L6-v2`).

---

## Project Structure

```
zecpath-ai/
├── api/                           # FastAPI REST service
│   ├── main.py                    # API routes, error handlers, and background tasks
│   ├── job_manager.py             # In-memory job state storage
│   └── schemas.py                 # Pydantic v2 request/response schemas
├── parsers/                       # Document ingestion and extraction
│   ├── pdf_parser.py              # PyMuPDF (fitz) text extractor
│   ├── docx_parser.py             # python-docx parser with table deduplication
│   ├── jd_extractor.py            # Job description extractor (PDF, DOCX, TXT)
│   ├── jd_parser.py               # JD requirement and role analyzer
│   ├── privacy_masker.py          # Email and phone PII masking
│   ├── skill_extractor.py         # Skill dictionary matcher
│   ├── experience_parser.py       # Employment timeline and title parser
│   └── education_parser.py        # Degree and discipline extractor
├── scoring/                       # Evaluation engines and aggregation
│   ├── ats_scorer.py              # Weighted score aggregator & coverage safeguard
│   ├── skill_matcher.py           # Required vs. preferred skill scoring
│   ├── experience_relevance.py    # Title & responsibility relevance scoring
│   ├── education_relevance.py     # Degree level & discipline scoring
│   ├── semantic_matcher.py        # Token-bigram & sentence-transformer matcher
│   ├── candidate_ranker.py        # Stable TimSort candidate ranker
│   ├── shortlisting.py            # Threshold classification engine
│   ├── candidate_pipeline.py      # Unified ranking and report pipeline
│   └── ranking_report.py          # Text report generator
├── data/                          # Dictionaries and benchmark datasets
│   ├── skill_dictionary.json      # Structured skill taxonomies and aliases
│   ├── sample_resumes/            # Sample test resumes
│   ├── sample_jobs/               # Sample job descriptions
│   └── testing/                   # Synthetic 12-candidate evaluation benchmark
├── docs/                          # Technical documentation and audit reports
│   ├── ATS_TECHNICAL_DOCUMENTATION.md
│   ├── ATS_ARCHITECTURE_DIAGRAMS.md
│   ├── DEVELOPER_GUIDE.md
│   ├── DAY20_FINAL_ATS_EVALUATION_REPORT.md
│   └── DAY20_FINAL_SYSTEM_AUDIT.md
├── outputs/                       # Generated CLI evaluation reports
│   ├── ats_scoring/               # Single candidate JSON reports
│   └── candidate_ranking/         # Batch ranking JSON and TXT reports
├── storage/                       # Local API file uploads
│   ├── resumes/                   # Uploaded resume files (<resume_id>.<ext>)
│   └── job_descriptions/          # Uploaded JD files (<job_id>.<ext>)
├── tests/                         # Automated test suite (30 test modules)
│   └── test_api.py                # 30 API integration tests with isolated fixtures
├── main_ats_scorer.py             # CLI entry point: single candidate scoring
├── main_candidate_ranking.py      # CLI entry point: batch candidate ranking
├── requirements.txt               # Core runtime dependencies
├── requirements-semantic.txt      # Optional sentence-transformer dependencies
└── README.md                      # Project documentation
```

---

## Installation & Environment Setup

### 1. Prerequisites
- **Python 3.12.0** (tested environment; compatible with Python 3.10+)
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/Codewith-Rony/zecpath-ai.git
cd zecpath-ai
```

### 3. Create and Activate a Virtual Environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On Linux / macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies

**Standard Installation:**
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Optional: Heavy Neural Embeddings (Dense Sentence Transformers):**
```bash
pip install -r requirements-semantic.txt
```

---

## CLI Usage

### 1. Single Candidate ATS Scoring

Evaluate a resume against a target job description:

```powershell
python main_ats_scorer.py `
  --resume "data/testing/resumes/tech_fresher/T-F01_aarav_menon.pdf" `
  --job-description "data/testing/job_descriptions/JD01_junior_python_developer.txt"
```

**Options:**
- `--resume`: Path to the resume (`.pdf` or `.docx`).
- `--job-description`: Path to the job description (`.txt`, `.pdf`, or `.docx`).
- `--role` *(Optional)*: Override the inferred target job role (e.g., `"Software Developer"` or `"AI Engineer"`).

JSON reports are saved to `outputs/ats_scoring/<resume>_vs_<jd>_ats_report.json`.

---

### 2. Batch Candidate Ranking & Shortlisting

Rank multiple evaluated candidates against a shared job description:

```powershell
python main_candidate_ranking.py `
  --reports `
    "outputs/ats_scoring/T-F01_aarav_menon_vs_JD01_junior_python_developer_ats_report.json" `
    "outputs/ats_scoring/T-F03_neha_varghese_vs_JD01_junior_python_developer_ats_report.json" `
    "outputs/ats_scoring/N-F01_ananya_pillai_vs_JD01_junior_python_developer_ats_report.json" `
  --shortlist-threshold 60 `
  --review-threshold 40
```

**Options:**
- `--reports`: Space-separated paths to one or more ATS JSON reports.
- `--shortlist-threshold` *(Optional, default: 70)*: Minimum ATS score for `Shortlist`.
- `--review-threshold` *(Optional, default: 40)*: Minimum ATS score for `Review`.
- `--output-dir` *(Optional)*: Custom directory for output reports.

Outputs are saved to:
- `outputs/candidate_ranking/ranked_candidates.json`
- `outputs/candidate_ranking/ranking_report.txt`

---

## REST API Service

### Running the API Server

Start the FastAPI application using Uvicorn:

```powershell
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```

The server starts at `http://127.0.0.1:8000`.

### Interactive Swagger UI

FastAPI provides an interactive web interface to test endpoints directly in your browser:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)

---

### API Endpoint Reference

| Method | Endpoint | Description | Status Code |
| :--- | :--- | :--- | :---: |
| `GET` | `/` | Service root and status | `200 OK` |
| `GET` | `/health` | Health check probe | `200 OK` |
| `POST` | `/api/v1/resumes` | Upload candidate resume (`.pdf` / `.docx`, max 10 MB) | `201 Created` |
| `POST` | `/api/v1/scoring/jobs` | Submit asynchronous scoring job (`resume_id` + JD file) | `202 Accepted` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll scoring job status (`queued`, `processing`, `completed`, `failed`) | `200 OK` / `404` |
| `POST` | `/api/v1/shortlisting` | Classify and rank candidate reports with thresholds | `200 OK` |

#### Example: Scoring Workflow via `curl`

**1. Upload Resume:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resumes" \
  -F "file=@data/testing/resumes/tech_fresher/T-F01_aarav_menon.pdf"
```
*Returns `resume_id`.*

**2. Submit Scoring Job:**
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scoring/jobs" \
  -F "resume_id=4b684821-65f5-4674-bf72-885ecb123456" \
  -F "job_description=@data/testing/job_descriptions/JD01_junior_python_developer.txt"
```
*Returns `job_id` and status `"queued"`.*

**3. Poll Job Status & Retrieve Report:**
```bash
curl "http://127.0.0.1:8000/api/v1/jobs/a92e92cf-3298-4c90-951d-768fba654321"
```

> [!NOTE]
> **API Storage & State**: Uploaded files are written to `storage/resumes/` and `storage/job_descriptions/`. Background job states and results are stored in an in-memory dictionary (`api.job_manager.jobs`) and do not persist across server restarts.

---

## Sample Outputs

### 1. Single Candidate CLI Output (`main_ats_scorer.py`)

```text
=== Zecpath AI: ATS Candidate Score Report ===
Resume: T-F01_aarav_menon.pdf
Job Description: JD01_junior_python_developer.txt
Job Role: Python Developer
ATS Score: 62.81/100
Data Coverage: 100.0%

Component Breakdown:

Skill Match
  Score: 70.0
  Weight: 40%
  Contribution: 28.0
  Status: available

Experience Relevance
  Score: 46.95
  Weight: 25%
  Contribution: 11.74
  Status: available

Education Alignment
  Score: 100.0
  Weight: 15%
  Contribution: 15.0
  Status: available

Semantic Similarity
  Score: 40.38
  Weight: 20%
  Contribution: 8.08
  Status: available

Semantic mode: token-bigram-fallback
Report saved to: outputs\ats_scoring\T-F01_aarav_menon_vs_JD01_junior_python_developer_ats_report.json
Note: This is a heuristic similarity score, not a probability or hiring decision.
```

### 2. Batch Ranking CLI Output (`main_candidate_ranking.py`)

```text
=== Zecpath AI: Candidate Ranking ===
Candidates processed: 3

Rank 1: T-F01_aarav_menon.pdf | Score: 62.81/100 | Recommendation: Shortlist
Rank 2: T-F03_neha_varghese.pdf | Score: 48.37/100 | Recommendation: Review
Rank 3: N-F01_ananya_pillai.pdf | Score: 9.01/100 | Recommendation: Reject Recommendation

JSON results saved to: outputs\candidate_ranking\ranked_candidates.json
Text report saved to: outputs\candidate_ranking\ranking_report.txt

Note: These are heuristic recommendations, not final hiring decisions.
```

---

## Automated Testing

Zecpath AI includes a comprehensive automated test suite covering unit functionality, parser edge cases, scoring math, regression milestones, and API integration.

### Running Tests

Execute pytest in the active virtual environment:

```powershell
python -m pytest
```

### Current Test Suite Status (Day 20 Verified)
- **Total Tests**: **183 passed**, **0 failed**, **0 skipped**
- **Warnings**: 1 (Starlette deprecation notice regarding `httpx` in testclient)
- **Execution Time**: **2.55s – 5.04s** across 30 test modules
- **API Test Suite (`tests/test_api.py`)**: 30 dedicated integration tests validating:
  - File upload restrictions (empty files, invalid extensions, size limits > 10 MB)
  - Malformed and corrupt document detection (PDF header and DOCX ZIP verification)
  - Job submission contracts, UUID parsing, and status transitions
  - In-memory state isolation and temporary directory fixtures (`tmp_path`)

---

## Performance Optimization Benchmarks

On Day 18, targeted optimizations were applied across the ingestion and scoring pipelines:

| Benchmark Task | Baseline Measurement | Optimized Measurement | Improvement |
| :--- | :---: | :---: | :---: |
| **PDF Extraction** (18 runs) | 18.47 ms / file | **8.48 ms / file** | **54.1% faster** |
| **DOCX Extraction** (18 runs) | 57.54 ms / file | **37.70 ms / file** | **34.5% faster** |
| **Full ATS Scoring** (48 candidate pairs) | 146.50 ms / pair | **142.15 ms / pair** | **3.0% faster** |
| **Semantic Matcher Init** (100 calls) | 0.3776 s total | **0.0004 s total** | **99.9% faster** |
| **Peak Memory Allocation** (Scoring) | 5.68 MB | **5.51 MB** | **3.0% reduction** |

*(Benchmarks verified in `data/testing/benchmark_baseline.json` and `benchmark_optimized.json`).*

---

## Production Readiness & Known Limitations

### Production Readiness Verdict
**CONDITIONAL NO-GO FOR PUBLIC CLOUD DEPLOYMENT**

Zecpath AI is fully verified, fast, and deterministic for **local CLI execution, batch evaluation, and controlled internal developer testing**. However, it is not currently production-ready for public internet deployment due to architectural boundaries:

1. **In-Memory Job State**: The API tracks jobs in a Python dictionary (`api.job_manager.jobs`). If the server restarts, job history is lost.
2. **In-Process Task Dispatch**: Background tasks execute using Starlette's thread pool. Worker failures do not feature persistent task retries or dead-letter queues.
3. **No Authentication or Rate Limiting**: API endpoints are currently unauthenticated without request throttling or user management.
4. **Local Disk Storage**: Uploaded files accumulate in `storage/` without automated TTL pruning policies.
5. **Lexical Semantic Scope**: The default `token-bigram-fallback` mode uses statistical n-gram overlap. It does not identify deep conceptual synonyms unless captured in `skill_dictionary.json`.

---

## Future Roadmap

- [ ] **Database Persistence**: Replace in-memory `jobs` with PostgreSQL via SQLAlchemy/SQLModel.
- [ ] **Distributed Task Queue**: Integrate Celery or ARQ with Redis for robust asynchronous job scheduling.
- [ ] **Cloud Object Storage**: Migrate from local disk storage to S3/GCS with pre-signed URLs and lifecycle policies.
- [ ] **Authentication & RBAC**: Add JWT/OAuth2 authentication with role-based recruiter and manager permissions.
- [ ] **Containerized Neural Workers**: Package dense transformer embeddings into dedicated GPU worker containers.

---

## Documentation Directory

For in-depth technical documentation, refer to the `docs/` directory:
- [`docs/ATS_TECHNICAL_DOCUMENTATION.md`](docs/ATS_TECHNICAL_DOCUMENTATION.md): Deep-dive into algorithms, mathematics, and parser design.
- [`docs/ATS_ARCHITECTURE_DIAGRAMS.md`](docs/ATS_ARCHITECTURE_DIAGRAMS.md): High-level system architecture and sequence diagrams.
- [`docs/DEVELOPER_GUIDE.md`](docs/DEVELOPER_GUIDE.md): Developer onboarding, coding standards, and debugging guide.
- [`docs/DAY20_FINAL_ATS_EVALUATION_REPORT.md`](docs/DAY20_FINAL_ATS_EVALUATION_REPORT.md): Comprehensive Day 20 evaluation and benchmark report.
- [`docs/DAY20_FINAL_SYSTEM_AUDIT.md`](docs/DAY20_FINAL_SYSTEM_AUDIT.md): Final code audit, security evaluation, and gap analysis.
