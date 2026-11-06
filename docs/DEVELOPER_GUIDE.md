# Zecpath AI – Developer Guide

Welcome to the Zecpath AI Applicant Tracking System (ATS) project! This guide provides new and contributing engineers with practical, verified instructions for onboarding, setting up the local environment, running the engine, running tests, extending features, and navigating the codebase.

For deep theoretical details, formulas, and visual workflows, also consult:
- [`docs/ATS_TECHNICAL_DOCUMENTATION.md`](ATS_TECHNICAL_DOCUMENTATION.md) (Architecture specifications and component formulas)
- [`docs/ATS_ARCHITECTURE_DIAGRAMS.md`](ATS_ARCHITECTURE_DIAGRAMS.md) (System architecture, end-to-end flowcharts, and API sequence diagrams)

---

## 1. Introduction

### 1.1 What Zecpath AI Does
Zecpath AI is a heuristic and statistical Applicant Tracking System (ATS) designed to assist recruiters in evaluating candidate resumes against job descriptions. The system parses unstructured resume documents, extracts structured competencies (skills, career timelines, and education), computes multidimensional match scores, applies governance safeguards, and sorts candidate batches for recruiter review.

### 1.2 Main Capabilities
- **Document Text Extraction**: Ingests PDF and DOCX resumes, as well as TXT, PDF, and DOCX job descriptions.
- **Privacy Masking**: Automatically redacts selected candidate personal identifiers (email addresses and telephone numbers) prior to scoring.
- **Role-Adaptive Scoring**: Evaluates candidates across four sequential dimensions:
  1. *Skill Match* (required vs. preferred skills)
  2. *Experience Relevance* (job title similarity, duty overlap, timeline analysis, and duration checks)
  3. *Education Alignment* (degree level, academic discipline, and certifications)
  4. *Semantic Document Similarity* (token-bigram cosine similarity fallback or optional neural embeddings)
- **Governance & Safeguards**: Dynamically renormalizes component weights when profile data is missing and flags candidates with less than 80% data coverage for manual human review.
- **Batch Ranking & Recommendation**: Sorts candidate pools using stable TimSort and categorizes them into actionable buckets: `shortlist`, `review`, `reject_recommendation`, or `manual_review`.
- **Dual Interfaces**: Standalone terminal Command-Line Interface (CLI) tools and a FastAPI REST service.

### 1.3 Scope and Known Limitations
- The project is an explainable decision-support tool; scores represent heuristic similarity indicators rather than definitive hiring decisions.
- Background API scoring runs in-process via Starlette thread workers; jobs are stored in volatile process memory rather than an external persistent database.
- Standard installation operates offline using a lexical token-bigram fallback rather than dense transformer embeddings.

---

## 2. Development Environment Setup

### 2.1 Python Environment & Compatibility
- **Tested Environment**: Python 3.12.0.
- **Compatibility Note**: Development, automated testing, and benchmarking have been conducted exclusively on Python 3.12.0. While the codebase uses standard typing features (e.g. PEP 585 collections) without hard version locks in a configuration file, compatibility with earlier Python versions (such as Python 3.10 or 3.11) has not been tested or verified.

### 2.2 Virtual Environment Setup

#### Windows (PowerShell)
```powershell
# 1. Clone or navigate to the repository directory
cd "d:\Desktop\Zecser Bussiness\zecpath-ai"

# 2. Create a virtual environment named 'venv'
python -m venv venv

# 3. Activate the virtual environment
.\venv\Scripts\Activate.ps1
```

#### Linux / macOS (Bash / Zsh)
```bash
# 1. Create a virtual environment named 'venv'
python3 -m venv venv

# 2. Activate the virtual environment
source venv/bin/activate
```

### 2.3 Installing Dependencies

The project maintains two requirements files in the repository root:

1. **Standard Runtime and Testing Dependencies (`requirements.txt`)**:
   Includes FastAPI, Uvicorn, Pydantic, PyMuPDF, python-docx, pytest, httpx, and python-dotenv.
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

2. **Optional Semantic Embeddings (`requirements-semantic.txt`)**:
   Contains `sentence-transformers>=3.0.0` for dense embedding similarity. Installing this package is **optional** and downloads PyTorch and transformer weights (~1 GB+). When the optional `sentence-transformers` dependency is unavailable, the application automatically uses `token-bigram-fallback` mode.
   ```bash
   # Optional: install only if testing dense neural embeddings
   pip install -r requirements-semantic.txt
   ```

### 2.4 Environment Variables Configuration
The application is pre-configured with robust code defaults and does not require mandatory environment variables to run locally. A template file [`.env.example`](../.env.example) exists in the repository root for custom runtime configurations if needed.

---

## 3. Project Structure

```
zecpath-ai/
├── api/                   # FastAPI REST API implementation
│   ├── job_manager.py     # In-memory job state tracker (jobs = {})
│   ├── main.py            # API routes, error handlers, and endpoints
│   └── schemas.py         # Pydantic request and response schemas
├── data/                  # Static assets, taxonomies, and testing datasets
│   ├── skill_dictionary.json # Canonical skill taxonomy and synonym maps
│   ├── sample_jobs/       # Sample job description documents
│   ├── sample_resumes/    # Sample candidate resumes
│   └── testing/           # Synthetic benchmark datasets, test resumes, and CSVs
├── docs/                  # Technical documentation, diagrams, and performance reports
│   ├── ATS_TECHNICAL_DOCUMENTATION.md # Comprehensive architectural reference
│   ├── ATS_ARCHITECTURE_DIAGRAMS.md   # Visual Mermaid architecture flows
│   └── DEVELOPER_GUIDE.md             # This developer guide
├── parsers/               # Text extraction, sanitization, and entity extraction
│   ├── docx_parser.py     # python-docx extractor with merged-cell deduplication
│   ├── education_parser.py# Degree, field of study, and certification extractor
│   ├── experience_parser.py# Employment timeline, date range, and gap analyzer
│   ├── jd_extractor.py    # Multi-format JD text loader (.txt, .pdf, .docx)
│   ├── jd_parser.py       # Job profile constructor (role title, skills, duties)
│   ├── pdf_parser.py      # PyMuPDF document extractor
│   ├── privacy_masker.py  # Personal identifier anonymizer ([EMAIL], [PHONE])
│   ├── resume_extractor.py# Main document extraction dispatcher
│   ├── resume_normalizer.py# Section and text structure normalizer
│   ├── resume_section_classifier.py # Section header classifier
│   ├── skill_extractor.py # Skill extractor with synonym & stack inference
│   └── text_cleaner.py    # Control character and whitespace sanitizer
├── scoring/               # Scoring engines, aggregation, ranking, and shortlisting
│   ├── ats_scorer.py      # Weighted score aggregator, renormalization & coverage check
│   ├── candidate_pipeline.py # High-level candidate batch orchestrator
│   ├── candidate_ranker.py# Stable TimSort score sorting
│   ├── education_relevance.py # Discipline match & degree level scoring
│   ├── experience_relevance.py # Title similarity, duty overlap & experience check
│   ├── ranking_report.py  # Recruiter text report generator
│   ├── semantic_matcher.py# Lexical token-bigram fallback / embedding matcher
│   ├── shortlisting.py    # Decision threshold classifier (shortlist/review/reject)
│   └── skill_matcher.py   # Required (80%) vs. preferred (20%) skill matcher
├── scripts/               # Benchmarks and evaluation matrix runners
│   ├── benchmark_day18.py # Latency and memory profiling harness
│   └── evaluation.py      # 48-pair evaluation matrix runner
├── storage/               # Runtime upload storage (created dynamically)
│   ├── job_descriptions/  # Uploaded JD documents
│   └── resumes/           # Uploaded resume documents
├── tests/                 # 30 automated test modules (159 passing unit/integration tests)
├── utils/                 # Shared cross-cutting utilities
│   ├── file_handler.py    # Safe UTF-8 JSON reading and writing
│   └── logger.py          # Rotating file and console logger (logs/app.log)
├── main.py                # Legacy single-resume extractor CLI (Day 5)
├── main_ats_scorer.py     # Primary CLI for single candidate ATS evaluation
├── main_candidate_ranking.py # Primary CLI for ranking candidate report batches
├── requirements.txt       # Standard runtime and testing dependencies
└── requirements-semantic.txt # Optional dependencies for sentence-transformers
```

### Inactive Scaffolding Directories
The directories `ats_engine/`, `interview_ai/`, and `screening_ai/` each contain only an empty `__init__.py`. These represent planned modular packages from early project scaffolding and are not utilized in the active pipeline.

---

## 4. Running the Application

### 4.1 Single Candidate Scoring CLI (`main_ats_scorer.py`)
Scores a single resume against a job description and writes a JSON report to `outputs/ats_scoring/`.

```bash
# Basic usage:
python main_ats_scorer.py --resume data/sample_resumes/sample_resume.pdf --job-description data/sample_jobs/sample_job.txt

# Usage with explicit role override:
python main_ats_scorer.py --resume data/sample_resumes/sample_resume.pdf --job-description data/sample_jobs/sample_job.txt --role "Python Developer"
```

**CLI Arguments**:
- `--resume` *(required)*: Path to the candidate's `.pdf` or `.docx` resume file.
- `--job-description` *(required)*: Path to the target `.txt`, `.pdf`, or `.docx` job description.
- `--role` *(optional)*: Role title override (e.g. `"Software Developer"`, `"AI Engineer"`). If omitted, the title is automatically inferred from the job description.

**Output Artifact**:
- Writes: `outputs/ats_scoring/{resume_stem}_vs_{jd_stem}_ats_report.json`
- Prints a formatted score breakdown and data coverage summary to the terminal.

---

### 4.2 Candidate Batch Ranking CLI (`main_candidate_ranking.py`)
Takes one or more JSON reports generated by `main_ats_scorer.py`, sorts candidates by score, classifies them against recommendation thresholds, and outputs batch ranking reports.

```bash
# Rank two or more candidate reports:
python main_candidate_ranking.py --reports outputs/ats_scoring/cand1_vs_job_ats_report.json outputs/ats_scoring/cand2_vs_job_ats_report.json --shortlist-threshold 70 --review-threshold 40
```

**CLI Arguments**:
- `--reports` *(required, 1 or more)*: File paths to candidate ATS JSON reports.
- `--shortlist-threshold` *(optional, default: 70.0)*: Minimum ATS score for a `shortlist` recommendation.
- `--review-threshold` *(optional, default: 40.0)*: Minimum ATS score for a `review` recommendation.
- `--output-dir` *(optional, default: `outputs/candidate_ranking`)*: Destination directory for ranking outputs.

**Output Artifacts**:
- Writes: `outputs/candidate_ranking/ranked_candidates.json` (Structured ranked array)
- Writes: `outputs/candidate_ranking/ranking_report.txt` (Human-readable recruiter summary; confirmed via [`main_candidate_ranking.py:100`](../main_candidate_ranking.py#L100))

---

### 4.3 Starting the FastAPI REST Service
Runs the API server using Uvicorn:

```bash
# Development mode with auto-reload:
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

### 4.4 Accessing Interactive API Documentation
Once the server is running, FastAPI automatically serves interactive API documentation:
- **Swagger UI**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc UI**: [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **OpenAPI JSON**: [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5. Testing

### 5.1 Test Environment and Dependencies
Testing dependencies (`pytest==9.1.1` and `httpx`) are included directly in `requirements.txt`. Ensure your virtual environment is activated before running tests.

### 5.2 Running the Complete Test Suite
To execute all test modules across parsers, scorers, and the API:

```bash
pytest
```

> [!NOTE]
> **Windows Sandbox Note**: When running `pytest` inside restricted Windows sandbox environments without elevated network permissions, test cases utilizing `httpx` and `fastapi.testclient.TestClient` (`tests/test_api.py`) may hang because Windows sandboxes restrict loopback socketpair creation. In such restricted environments, run unit tests directly or run pytest with network permissions enabled.

### 5.3 Running Specific Test Modules or Functions
```bash
# Run scoring unit tests:
pytest tests/test_ats_scorer.py

# Run experience relevance tests:
pytest tests/test_experience_relevance.py

# Run a specific test case:
pytest tests/test_ats_scorer.py -k "test_renormalization"
```

### 5.4 Test Suite Organization
The test suite consists of 30 test modules located under `tests/` (excluding `__init__.py`):
- **Document & Text Parsing (6 modules)**: `test_pdf_parser.py`, `test_docx_parser.py`, `test_resume_extractor.py`, `test_resume_normalizer.py`, `test_section_accuracy.py`, `test_section_classifier.py`
- **Entity Extraction & Masking (5 modules)**: `test_privacy_masker.py`, `test_skill_extractor.py`, `test_experience_parser.py`, `test_education_step1.py`, `test_jd_parser.py`
- **Component Scorers (5 modules)**: `test_skill_matcher.py`, `test_experience_relevance.py`, `test_education_relevance.py`, `test_semantic_matcher.py`, `test_scoring.py`
- **ATS Governance & Ranking (7 modules)**: `test_ats_scorer.py`, `test_candidate_ranker.py`, `test_shortlisting.py`, `test_candidate_pipeline.py`, `test_ranking_report.py`, `test_ats_pipeline.py`, `test_fairness_evaluation.py`
- **CLI, API & Utilities (5 modules)**: `test_main_ats_scorer.py`, `test_candidate_ranking_cli.py`, `test_api.py`, `test_file_handler.py`, `test_basic.py`
- **Milestone Regression & Optimization Suites (2 modules)**: `test_day17_regressions.py`, `test_day18_optimizations.py`

### 5.5 Recorded Test Baseline
- **Day 18 Recorded Baseline**: 159 passing tests (0 failures, 0 errors) recorded in [`docs/day18_performance_report.md`](day18_performance_report.md) under Python 3.12.0 and pytest 9.1.1.
- *Note*: This represents the last officially documented milestone test run; developers should run `pytest` locally to verify current live status before and after making changes.

---

## 6. Understanding the Scoring Pipeline

Inside [`main_ats_scorer.py::generate_candidate_report()`](../main_ats_scorer.py#L42), the scoring pipeline executes **strictly sequentially on a single thread**:

```
[Resume File]                [Job Description File]
      │                                │
      ▼                                ▼
1. extract_resume()          2. extract_jd_text()
      │                                │
      ▼                                ▼
3. mask_personal_attributes() 4. build_job_profile()
      │                                │
      └────────────────┬───────────────┘
                       │
                       ▼
       5. score_skill_match()
          (Extracts skills, matches required 80% vs preferred 20%)
                       │
                       ▼
       6. score_experience_relevance()
          (Parses dates, timeline, title similarity 60% & duty match 40%)
                       │
                       ▼
       7. score_education_relevance()
          (Parses degrees, evaluates discipline 70% & degree level 30%)
                       │
                       ▼
       8. SemanticMatcher.similarity()
          (Token-bigram vector cosine similarity fallback)
                       │
                       ▼
       9. calculate_ats_score()
          (Applies role weights, renormalizes missing components, checks >=80% coverage)
```

### Component Breakdown
1. **Skill Match**: Compares candidate skills against required skills (80% weight) and preferred skills (20% weight).
2. **Experience Relevance**: Evaluates title similarity (60% weight) and duty overlap (40% weight), and performs candidate duration verification against job requirements. Returns `None` if no work entries are extracted.
3. **Education Alignment**: Scores discipline alignment (+70 points) and recognized degree level (+30 points) against the target role category. Returns `None` if no education entries are extracted.
4. **Semantic Similarity**: Computes lexical cosine similarity across the full documents. If the job description is empty or whitespace-only, `main_ats_scorer.py` normalizes this score to `None`.
5. **ATS Score Aggregation**:
   - Default weights: Skill 40%, Experience 25%, Education 15%, Semantic 20%.
   - Role weights: Defined in `ROLE_WEIGHTS` (e.g., Software Developer, AI Engineer).
   - If any component returns `None`, its weight is excluded, and the remaining weights are renormalized to 100%.
   - **Manual Review Flag**: If `coverage_percentage < 80%`, `manual_review_required` is set to `True`. Downstream, `scoring/shortlisting.py` assigns the candidate the recommendation label `"manual_review"` rather than an automated shortlist or rejection.

*(For exact formulas and mathematical proofs, see [`docs/ATS_TECHNICAL_DOCUMENTATION.md`](ATS_TECHNICAL_DOCUMENTATION.md#L202-L285).)*

---

## 7. Extending the Project

### 7.1 Adding or Updating Skill Taxonomy Entries
The canonical skill dictionary is located at [`data/skill_dictionary.json`](../data/skill_dictionary.json).
- Organized by category: `"technical"`, `"business"`, `"creative"`.
- Each category maps canonical skill names to lists of synonyms and aliases:
  ```json
  "technical": {
      "kubernetes": ["k8s", "kube", "kubernetes cluster"]
  }
  ```
- **Caching & Reloading**: [`parsers/skill_extractor.py`](../parsers/skill_extractor.py) tracks the file modification timestamp (`st_mtime_ns`). If `data/skill_dictionary.json` is modified, the cache auto-invalidates on the next call. Developers can also invoke `parsers.skill_extractor.clear_skill_dictionary_cache()`.

### 7.2 Adding or Updating Role-Specific Weights
Role-specific weighting profiles are defined in [`scoring/ats_scorer.py`](../scoring/ats_scorer.py#L11-L24):
```python
ROLE_WEIGHTS = {
    "Software Developer": {
        "skill_match": 45,
        "experience_relevance": 25,
        "education_alignment": 10,
        "semantic_similarity": 20,
    },
    "Data Scientist": {  # Example of adding a new role profile
        "skill_match": 35,
        "experience_relevance": 25,
        "education_alignment": 15,
        "semantic_similarity": 25,
    },
}
```
**Rules**:
- All component weights must be non-negative numbers.
- The weights across the four components must sum to exactly 100 (`validate_weights()` enforces this).

### 7.3 Modifying or Extending a Scoring Component
When modifying or extending scoring components in `scoring/`, note that individual scoring functions have distinct return structures rather than a uniform dictionary contract:

1. **Component Return Contracts**:
   - **`scoring/skill_matcher.py::score_skill_match()`**: Returns a dictionary where the overall score is under `"skill_match_score"` (`float` or `None`), alongside detailed breakdown keys (`resume_skills`, `required_skills`, `matched_required_skills`, `preferred_skills`, etc.).
   - **`scoring/experience_relevance.py::score_experience_relevance()`**: Returns a dictionary with `"target_role"`, `"role_scores"` (a list of dicts, each containing an individual role's `"relevance_score"`), and `"experience_requirement_assessment"`. It does **not** return a single top-level score key. The caller ([`main_ats_scorer.py:105-107`](../main_ats_scorer.py#L105-L107)) derives the scalar score by computing `_mean_or_none([item.get("relevance_score") for item in role_scores])`.
   - **`scoring/education_relevance.py::score_education_relevance()`**: Returns a dictionary with `"target_role"` and `"education_scores"` (a list of dicts, each containing an education entry's `"relevance_score"`). It does **not** return a single top-level score key. The caller ([`main_ats_scorer.py:112-114`](../main_ats_scorer.py#L112-L114)) derives the scalar score by computing `_mean_or_none([item.get("relevance_score") for item in education_scores])`.
   - **`scoring/semantic_matcher.py::SemanticMatcher.similarity()`**: Returns a scalar `float` directly (`0.0` to `100.0`), **not** a dictionary. In [`main_ats_scorer.py:119-120`](../main_ats_scorer.py#L119-L120), if either document text is empty, this is explicitly converted to `None`.

2. **Aggregator Input Contract (`scoring/ats_scorer.py::calculate_ats_score`)**:
   - The aggregator expects a flat dictionary mapping each of the four component keys to a scalar score (`float` or `None`):
     ```python
     component_scores = {
         "skill_match": skill_score,              # float (0.0 - 100.0) or None
         "experience_relevance": experience_score, # float (0.0 - 100.0) or None
         "education_alignment": education_score,   # float (0.0 - 100.0) or None
         "semantic_similarity": semantic_score,   # float (0.0 - 100.0) or None
     }
     ```
   - **Critical Rule**: When candidate data is absent or unscoreable, the component score must be `None` (never substitute an arbitrary default like `0.0` or `50.0`). The aggregator relies on `score is None` to exclude the component weight and renormalize available weights to 100%. Returning `0.0` penalizes the candidate and distorts the coverage calculation.
   - Keep scoring components independent; do not introduce circular dependencies between scoring modules.

### 7.4 Adding Tests for New Features
1. Place unit tests in `tests/test_<feature>.py`.
2. Add assertions verifying both valid inputs and defensive edge cases (e.g., empty strings, null values, malformed files).
3. If modifying core scoring logic, verify that existing candidate evaluation baselines in `tests/test_day17_regressions.py` and `tests/test_day18_optimizations.py` continue to pass.

---

## 8. API Development

### 8.1 API Module Structure
The REST API is implemented using FastAPI in the [`api/`](../api/) package:
- [`api/main.py`](../api/main.py): Application factory, routing, exception handlers, and background worker functions.
- [`api/job_manager.py`](../api/job_manager.py): In-memory job state tracking dictionary (`jobs = {}`).
- [`api/schemas.py`](../api/schemas.py): Pydantic models for request bodies (`ShortlistingRequest`, `CandidateReport`, `ThresholdConfig`).

### 8.2 Endpoints and Purposes

| Method | Endpoint | Purpose | Request Type | Expected Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Service root and status | None | `200 OK` |
| `GET` | `/health` | Health check probe | None | `200 OK {"status": "healthy"}` |
| `POST` | `/api/v1/resumes` | Upload resume file | `multipart/form-data: file` | `201 Created {"resume_id": UUID, ...}` |
| `POST` | `/api/v1/scoring/jobs` | Submit async scoring job | `Form: resume_id`, `File: job_description` | `202 Accepted {"job_id": UUID, "status": "queued"}` |
| `GET` | `/api/v1/jobs/{job_id}` | Poll scoring job status | Path parameter `job_id` | `200 OK` (Job record with `result` or `error`) |
| `POST` | `/api/v1/shortlisting` | Batch rank candidate reports | `application/json: ShortlistingRequest` | `200 OK {"candidates": [...], "report": "..."}` |

### 8.3 Background Scoring Job Lifecycle
1. **Upload Resume**: Client posts file to `/api/v1/resumes`. Saved to `storage/resumes/{resume_id}.ext`.
2. **Submit Job**: Client posts `resume_id` and JD file to `/api/v1/scoring/jobs`. JD is saved to `storage/job_descriptions/{job_id}.ext`. A job entry is added to `api/job_manager.py::jobs` with status `"queued"`.
3. **In-Process Background Task**: Starlette dispatches `process_scoring_job` to an in-process thread pool via `anyio.to_thread.run_sync`. Status updates to `"processing"`.
4. **Execution**: `generate_candidate_report()` executes.
5. **State Finalization**: On success, status becomes `"completed"` and the full report dictionary is attached to `"result"`. On exception, status becomes `"failed"` with `"error"`.
6. **Result Polling**: The client polls `GET /api/v1/jobs/{job_id}` until the job reaches a terminal state.

### 8.4 Example Requests

#### Upload Resume
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/resumes" \
  -F "file=@data/sample_resumes/sample_resume.pdf"
```

#### Submit Scoring Job
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/scoring/jobs" \
  -F "resume_id=<RESUME_UUID>" \
  -F "job_description=@data/sample_jobs/sample_job.txt"
```

#### Poll Job Status
```bash
curl "http://127.0.0.1:8000/api/v1/jobs/<JOB_UUID>"
```

#### Batch Shortlisting Request
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/shortlisting" \
  -H "Content-Type: application/json" \
  -d '{
    "candidate_reports": [
      {
        "candidate_id": "cand_01",
        "candidate_name": "Alice Developer",
        "ats_score": 85.5,
        "coverage_percentage": 100.0,
        "manual_review_required": false
      }
    ],
    "thresholds": {
      "shortlist": 70.0,
      "review": 40.0
    }
  }'
```

---

## 9. Logging and Troubleshooting

### 9.1 Application Logging
Application logs are maintained by [`utils/logger.py`](../utils/logger.py) and written to:
```
logs/app.log
```
The logger formats events with timestamps, log levels (`INFO`, `WARNING`, `ERROR`, `EXCEPTION`), and detailed exception tracebacks.

### 9.2 Common Troubleshooting Scenarios

#### 1. Unsupported or Unreadable Resume File
- **Symptom**: `ValueError: No readable text found in the resume.`
- **Cause**: The resume file is either empty, password-protected, or a scanned image-only PDF without an embedded text layer.
- **Fix**: The ATS relies on text extraction via PyMuPDF and python-docx. Scanned images without OCR text layers are not currently supported. Verify that the file contains selectable text.

#### 2. API Validation Errors (HTTP 400 / 413 / 422)
- **HTTP 413 (`FILE_TOO_LARGE`)**: The uploaded file exceeds the 10 MB limit (`MAX_FILE_SIZE = 10 * 1024 * 1024` bytes).
- **HTTP 400 (`BAD_REQUEST`)**: The file has an invalid extension, lacks required magic bytes (e.g., PDF not starting with `%PDF-` or corrupted DOCX archive), or the `resume_id` is an invalid UUID string.
- **HTTP 422 (`VALIDATION_ERROR`)**: Request JSON body violates the Pydantic schema in `POST /api/v1/shortlisting` or score thresholds are invalid (e.g. `review_threshold > shortlist_threshold`).

#### 3. Job Records Disappearing After Server Restart
- **Symptom**: `GET /api/v1/jobs/{job_id}` returns `HTTP 404 Resource Not Found` for previously submitted jobs.
- **Cause**: Job states are stored in volatile process memory (`api/job_manager.py::jobs = {}`).
- **Fix**: This is an architectural limitation of the current development implementation. Restarting the Uvicorn process clears in-memory state. In multi-worker deployments (`uvicorn --workers N`), requests routed to different workers cannot access jobs created by another worker.

#### 4. Semantic Matching Dependency Warning
- **Symptom**: Module operates in `token-bigram-fallback` mode.
- **Cause**: `sentence-transformers` is an optional dependency and is not installed in standard setups.
- **Behavior**: This is expected normal behavior. The ATS falls back to token-bigram cosine similarity automatically without throwing exceptions.

---

## 10. Development Best Practices

1. **Maintain Architectural Separation**:
   - Keep document parsing logic in `parsers/`.
   - Keep evaluation algorithms and mathematical formulas in `scoring/`.
   - Keep HTTP routing and schemas in `api/`.
   - Keep common utilities in `utils/`.
2. **Preserve Scoring Determinism**:
   - Component scores must remain strictly deterministic for identical inputs.
   - Any caching implementation (such as dictionary or vector caches) must ensure isolation against shared mutable state (use deep copies or immutable tuples).
3. **Defensive Null Handling**:
   - Never substitute arbitrary scores (e.g. 0.0 or 50.0) when profile information is absent. Return `None` so `scoring/ats_scorer.py` can properly exclude the component and renormalize available weights.
4. **Git Hygiene & Data Privacy**:
   - Never commit candidate resumes or job descriptions to version control.
   - Do not commit virtual environments (`venv/`), `.env` configuration files, or runtime outputs (`outputs/`, `storage/`, `logs/`).
5. **Regression Testing**:
   - Every bug fix or optimization must include an accompanying automated test in `tests/`.
   - Run `pytest` before submitting changes to ensure all existing baseline tests remain green.

---

## 11. Known Limitations and Future Improvements

To maintain technical clarity, current system constraints are separated from proposed architectural enhancements:

### Verified Current Limitations
- **In-Memory Volatility**: Scoring jobs are tracked in a global Python dictionary and do not persist across server restarts.
- **In-Process Task Dispatch**: Background tasks run within the application thread pool (`anyio.to_thread.run_sync`), lacking distributed queueing, persistence, or worker retry semantics.
- **Single-Threaded Sequential Scoring**: The four scoring components execute sequentially on a single thread inside `generate_candidate_report()`.
- **Lexical Semantic Matching**: By default, semantic matching relies on sparse token-bigram vector cosine similarity rather than dense contextual embeddings.
- **No Native OCR**: Scanned documents or image-only resumes cannot be parsed without selectable text layers.

### Proposed Future Improvements
- **Persistent Database**: Transition `api/job_manager.py` to an asynchronous relational database (e.g. PostgreSQL with SQLAlchemy / Alembic).
- **Distributed Worker Queue**: Migrate background scoring from Starlette `BackgroundTasks` to a distributed queue (e.g. Celery, RQ, or RabbitMQ) backed by Redis.
- **OCR Pipeline**: Integrate a lightweight OCR fallback (such as Tesseract or pdf2image) for scanned resumes lacking text streams.
- **Dense Embedding Service**: Deploy dedicated neural embedding microservices or GPU-backed SentenceTransformer pipelines.

---

## 12. Quick Reference

| Task | Command / URL | Notes |
| :--- | :--- | :--- |
| **Create Virtual Environment** | `python -m venv venv` | Tested on Python 3.12.0; earlier versions are unverified. |
| **Activate Environment (Win)** | `.\venv\Scripts\Activate.ps1` | Windows PowerShell |
| **Activate Environment (Unix)**| `source venv/bin/activate` | Linux / macOS Bash/Zsh |
| **Install Dependencies** | `pip install -r requirements.txt` | Standard runtime & test dependencies |
| **Install Optional Embeddings**| `pip install -r requirements-semantic.txt` | Optional dense neural models (~1 GB+) |
| **Run All Tests** | `pytest` | 159 tests in recorded Day 18 baseline |
| **Run Specific Test File** | `pytest tests/test_ats_scorer.py` | Runs isolated module tests |
| **Single Candidate Scoring** | `python main_ats_scorer.py --resume <path> --job-description <path>` | Outputs report to `outputs/ats_scoring/` |
| **Candidate Batch Ranking** | `python main_candidate_ranking.py --reports <r1.json> <r2.json>` | Outputs ranked_candidates.json & ranking_report.txt to outputs/candidate_ranking/ |
| **Start API Server** | `uvicorn api.main:app --reload --host 127.0.0.1 --port 8000` | Development ASGI server |
| **API Swagger UI** | `http://127.0.0.1:8000/docs` | Interactive API documentation |
| **API ReDoc UI** | `http://127.0.0.1:8000/redoc` | Alternative API reference |
| **Inspect Application Logs** | `Get-Content -Tail 50 logs/app.log` (Win) / `tail -f logs/app.log` | Rotating application log file |

