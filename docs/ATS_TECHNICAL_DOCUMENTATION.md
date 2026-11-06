# Zecpath AI – ATS Technical Documentation

## 1. Project Overview

### 1.1 What is Zecpath AI?
**Zecpath AI** is an automated Applicant Tracking System (ATS) engine built with Python. It analyzes resumes in common document formats against job descriptions (JDs) to provide objective, explainable, and multi-dimensional candidate evaluation.

### 1.2 Purpose and Main Capabilities
The engine provides automated decision support for recruiters and hiring managers without functioning as an opaque black box. Its core capabilities include:
- **Multi-Format Ingestion**: Extracts text from PDF and DOCX resumes, as well as TXT, PDF, and DOCX job descriptions.
- **Explainable Multi-Component Scoring**: Scores candidate fitness across four independent dimensions:
  1. *Skill Match* (40% default weight)
  2. *Experience Relevance* (25% default weight)
  3. *Education Alignment* (15% default weight)
  4. *Semantic Similarity* (20% default weight)
- **Candidate Timeline Analysis**: Computes total calendar duration (merging overlapping employments to prevent double-counting) and detects career gaps.
- **Fairness & Privacy Safeguards**: Masks direct personal identifiers (emails and phone numbers) prior to candidate evaluation.
- **Coverage Safeguards**: Enforces an 80% minimum scoring data coverage threshold; candidates with insufficient profile data are flagged for mandatory human review (`manual_review_required = True`).
- **Batch Ranking and Shortlisting**: Ranks candidate pools for a given job and classifies them into actionable recommendations (`shortlist`, `review`, `reject_recommendation`, or `manual_review`).
- **Dual Interfaces**: Operates via standalone Command-Line Interface (CLI) tools and a FastAPI REST service.

### 1.3 Current Scope of the Project
The current scope is focused on heuristic parsing, lexical/statistical matching, and explainable scoring for single-tenant evaluation. The system currently uses an offline lexical fallback for semantic similarity rather than dense transformer embeddings, stores background API jobs in process memory, and executes scoring sequentially.

---

## 2. Technology Stack

| Category | Technology / Library | Version / Specification | Role in Architecture |
| :--- | :--- | :--- | :--- |
| **Language** | Python | 3.12+ | Core runtime environment. |
| **API Framework** | FastAPI | 0.162.0 | High-performance asynchronous REST API framework. |
| **ASGI Server** | Uvicorn | 0.54.0 | ASGI server used to run the FastAPI application. |
| **Data Validation** | Pydantic | >= 2.0 | Request body validation, data schemas, and threshold constraints. |
| **File Multipart** | python-multipart | 0.0.33 | Streaming multipart/form-data upload handling in FastAPI. |
| **PDF Extraction** | PyMuPDF (`pymupdf`/`fitz`) | Latest | Fast C-backed PDF text extraction and metadata processing. |
| **DOCX Extraction** | `python-docx` | Latest | Microsoft Word XML parsing for paragraphs and table structures. |
| **Standard Libraries** | `difflib`, `re`, `unicodedata`, `functools`, `math`, `collections` | Built-in | String sequence matching, regex tokenization, normalization, and caching. |
| **Configuration** | `python-dotenv` | 1.2.3 | Environment variable loading from `.env` files. |
| **Testing** | `pytest`, `httpx` | 9.1.1, Latest | Automated test runner and asynchronous API test client. |
| **Data Storage** | Local Filesystem & In-Memory Dict | N/A | Disk storage for uploaded documents; in-memory dictionary for API job states. |

*Note on Optional Dependencies*: `requirements-semantic.txt` references `sentence-transformers>=3.0.0` as an optional dependency for neural embedding similarity. In the current standard environment, this package is not installed, and the ATS operates using its built-in token-bigram fallback.

---

## 3. Repository Structure

### 3.1 Directory Layout

```
zecpath-ai/
├── api/                   # FastAPI REST API implementation
│   ├── job_manager.py     # In-memory job state tracker
│   ├── main.py            # API routes, exception handlers, and endpoints
│   └── schemas.py         # Pydantic request and response schemas
├── data/                  # Static assets, dictionaries, and testing data
│   ├── skill_dictionary.json # Canonical skill taxonomy and synonym map
│   ├── sample_jobs/       # Sample job descriptions
│   ├── sample_resumes/    # Sample candidate resumes
│   └── testing/           # Synthetic resumes, benchmark definitions, and CSVs
├── docs/                  # Architecture, milestone, and performance reports
├── parsers/               # Document extraction, normalization, and section parsers
│   ├── docx_parser.py     # Word document (.docx) extractor
│   ├── education_parser.py# Academic degree and certification extractor
│   ├── experience_parser.py# Employment history, dates, and timeline extractor
│   ├── jd_extractor.py    # Job description text loader
│   ├── jd_parser.py       # Job description section, role, and requirement parser
│   ├── pdf_parser.py      # PDF document (.pdf) extractor
│   ├── privacy_masker.py  # Email and phone number anonymizer
│   ├── resume_extractor.py# Main document extraction dispatcher
│   ├── resume_normalizer.py# Text standardizer and cleaner
│   ├── resume_section_classifier.py # Standalone resume block classifier
│   ├── skill_extractor.py # Skill extractor with synonym & stack inference
│   └── text_cleaner.py    # Whitespace and control character sanitizer
├── scoring/               # Evaluation algorithms and aggregation rules
│   ├── ats_scorer.py      # Weighted ATS score aggregator and coverage safeguards
│   ├── candidate_pipeline.py # High-level ranking and shortlisting orchestrator
│   ├── candidate_ranker.py# Stable candidate score sorting
│   ├── education_relevance.py # Role-adaptive academic scoring
│   ├── experience_relevance.py # Role similarity and requirement scoring
│   ├── ranking_report.py  # Recruiter text report generator
│   ├── semantic_matcher.py# Lexical fallback and cosine similarity engine
│   ├── shortlisting.py    # Score thresholding and recommendation classifier
│   └── skill_matcher.py   # Required vs. preferred skill scoring
├── scripts/               # Automated benchmarks and evaluation matrices
│   ├── benchmark_day18.py # Reproducible latency and memory profiling harness
│   └── evaluation.py      # 48-pair evaluation matrix test script
├── storage/               # Runtime upload storage (created automatically)
│   ├── job_descriptions/  # Uploaded JD documents
│   └── resumes/           # Uploaded resume documents
├── tests/                 # 28 test modules (159 passing unit/integration tests)
├── utils/                 # Common shared utilities
│   ├── file_handler.py    # UTF-8 JSON serialization helpers
│   └── logger.py          # Rotating file and console logger
├── main.py                # Legacy single-resume extractor CLI
├── main_ats_scorer.py     # Primary CLI for full ATS candidate scoring
├── main_candidate_ranking.py # Primary CLI for ranking candidate report batches
├── requirements.txt       # Production dependencies
└── requirements-semantic.txt # Optional dependencies for embedding models
```

### 3.2 Key Root-Level Python Files
- `main_ats_scorer.py`: The central CLI entry point for scoring a single resume against a job description. Orchestrates the full parsing and scoring pipeline and generates output JSON reports.
- `main_candidate_ranking.py`: The CLI entry point for sorting multiple candidate JSON reports, classifying them against shortlisting thresholds, and generating ranking summaries.
- `main_skill_extractor.py`, `main_experience_parser.py`, `main_education_parser.py`, `main_semantic_matcher.py`, `main_jd.py`: Focused developer CLI tools for inspecting and testing individual parsing and scoring components in isolation.

### 3.3 Inactive Scaffolding Directories
The repository contains three root directories—`ats_engine/`, `interview_ai/`, and `screening_ai/`—which each contain only an empty `__init__.py`. These represent planned modular packages from early scaffolding that are not currently referenced by the active codebase.

---

## 4. System Architecture

The Zecpath AI ATS architecture consists of four distinct operational layers:

1. **Ingestion & Normalization Layer (`parsers/`)**: Reads binary document formats (PDF, DOCX) and plain text into Python strings. Sanitizes control characters, strips personally identifiable contact details, and extracts structured entities (skills, work history entries, academic credentials, and JD requirements).
2. **Component Scoring Layer (`scoring/`)**: Evaluates candidate fitness across four independent dimensions. Each component yields a normalized score between 0.0 and 100.0, or returns `None` if the candidate lacks data for that dimension.
3. **Aggregation & Governance Layer (`scoring/ats_scorer.py`, `scoring/shortlisting.py`)**: Applies role-specific or default weights to available components, renormalizes the score if components are missing, computes overall data coverage, and flags profiles with less than 80% coverage for human review.
4. **Interface Layer (`main_ats_scorer.py`, `main_candidate_ranking.py`, `api/`)**: Surfaces functionality via terminal CLI commands and REST API endpoints.

```
+-------------------------------------------------------------------------------+
|                                Interface Layer                                |
|   CLI (main_ats_scorer.py, main_candidate_ranking.py)   |   FastAPI (api/main.py)|
+---------------------------------------+---------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|                         Ingestion & Normalization Layer                       |
|   parsers/pdf_parser.py      parsers/docx_parser.py     parsers/jd_extractor.py|
|   parsers/privacy_masker.py  parsers/text_cleaner.py    parsers/jd_parser.py  |
+---------------------------------------+---------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|                            Component Scoring Layer                            |
|   scoring/skill_matcher.py          |   scoring/experience_relevance.py       |
|   (Required 80% / Preferred 20%)    |   (Title 60% / Responsibilities 40%)    |
|   ----------------------------------+---------------------------------------  |
|   scoring/education_relevance.py    |   scoring/semantic_matcher.py           |
|   (Field 70% / Degree Level 30%)    |   (Token-Bigram Cosine Fallback)        |
+---------------------------------------+---------------------------------------+
                                        |
+---------------------------------------v---------------------------------------+
|                       Aggregation & Governance Layer                          |
|   scoring/ats_scorer.py       -> Weighted sum, coverage calculation (<80% flag)|
|   scoring/candidate_ranker.py -> Stable score sorting (highest to lowest)     |
|   scoring/shortlisting.py     -> Categorization (shortlist, review, reject)   |
+-------------------------------------------------------------------------------+
```

> [!NOTE]
> The diagram above illustrates logical module organization and data flow across layers, not parallel execution. In the live candidate scoring pipeline (`main_ats_scorer.py`), the four scoring components (Skill Match, Experience Relevance, Education Alignment, and Semantic Similarity) execute strictly sequentially on a single thread.

---

## 5. Core Components

### 5.1 Resume Extraction
- **Files & Primary Functions**:
  - `parsers/resume_extractor.py`: `extract_resume(file_path)`
  - `parsers/pdf_parser.py`: `extract_text_from_pdf(file_path)`
  - `parsers/docx_parser.py`: `extract_text_from_docx(file_path)`
- **Responsibility**: Ingests document files, identifies file type via extension (`.pdf` or `.docx`), and extracts plain text.
- **Inputs**: Path to a document file (`str` or `Path`).
- **Outputs**: Dictionary with keys: `"file_name"`, `"file_type"`, `"raw_text"`, `"cleaned_text"`.
- **Dependencies**: `pymupdf` (PyMuPDF), `python-docx`, `parsers/text_cleaner.py`.
- **Details**:
  - `pdf_parser` uses a context manager (`with fitz.open(...) as document:`) and joins pages via list comprehension. Returns `""` on 0-byte files and raises descriptive `ValueError` on corrupted PDF streams.
  - `docx_parser` deduplicates merged table cells by tracking XML node element identity (`cell._tc`). Spanned cells are emitted once, while separate distinct cells with identical text are preserved.

### 5.2 Text Cleaning and Normalization
- **Files & Primary Functions**:
  - `parsers/text_cleaner.py`: `clean_resume_text(text)`, `clean_line(line)`
  - `parsers/resume_normalizer.py`: `normalize_resume_text(text)`
- **Responsibility**: Strips unprintable control characters, normalizes line endings, standardizes bullet points, and applies Unicode `NFKC` normalization.
- **Inputs**: Raw string text.
- **Outputs**: Cleaned, standardized string text.
- **Dependencies**: Built-in `re`, `unicodedata`.
- **Details**: Removes null bytes and non-printable control characters (`\x00-\x08\x0b\x0c\x0e-\x1f\x7f`) before line splitting, preventing vertical tabs and form feeds from prematurely breaking sentences across lines.

### 5.3 Privacy Masking
- **Files & Primary Functions**:
  - `parsers/privacy_masker.py`: `mask_personal_attributes(text)`
- **Responsibility**: Detects and replaces candidate contact information with standardized tokens prior to candidate scoring.
- **Inputs**: Cleaned resume text string.
- **Outputs**: Masked text string.
- **Dependencies**: Built-in `re`.
- **Details**: Replaces email addresses with `[EMAIL]` and telephone patterns with `[PHONE]` using regular expressions. Masked text is passed to all subsequent scoring components (`score_skill_match`, `extract_experience`, `extract_academic_profile`, and `SemanticMatcher.similarity`).

### 5.4 Job Description Parsing
- **Files & Primary Functions**:
  - `parsers/jd_extractor.py`: `extract_jd_text(file_path)`
  - `parsers/jd_parser.py`: `build_job_profile(text, known_skills, known_roles, job_id)`
- **Responsibility**: Reads JD files (TXT, PDF, DOCX) and structures them into a profile containing role title, experience requirements, education requirements, responsibilities, and required/preferred skills.
- **Inputs**: Raw JD text string, canonical skills list, known roles list.
- **Outputs**: Structured dictionary containing `"job_id"`, `"title"`, `"experience_requirement"`, `"required_skills"`, `"preferred_skills"`, `"education_requirements"`, `"responsibilities"`.
- **Dependencies**: `parsers/pdf_parser.py`, `parsers/docx_parser.py`, built-in `re`.
- **Details**: Recognizes 33 role title variations (covering both engineering titles and HR titles such as `HR Executive`, `HR Business Partner`, `Talent Acquisition Specialist`, and `Recruiter`). Extracts structured experience ranges (`minimum_years`, `maximum_years`).

### 5.5 Skill Extraction and Matching
- **Files & Primary Functions**:
  - `parsers/skill_extractor.py`: `load_skill_dictionary(path)`, `extract_skills(resume_text)`
  - `scoring/skill_matcher.py`: `score_skill_match(resume_text, job_description_text, job_profile)`
- **Responsibility**: Identifies candidate skills from text, maps synonyms to canonical skill names, infers component skills from skill stacks, and computes match coverage against the JD.
- **Inputs**: Resume text, JD text, optional pre-built `job_profile`.
- **Outputs**: Dictionary with `"skill_match_score"` (0.0 to 100.0 or `None`), matched/missing required lists, and matched/missing preferred lists.
- **Dependencies**: `data/skill_dictionary.json`, built-in `re`, `difflib`.
- **Details**:
  - `load_skill_dictionary()` caches the parsed JSON and validates against `st_mtime_ns` on disk. Returns an isolated dictionary clone (`_clone_dictionary`) to prevent shared mutable state.
  - Matches skills using boundary regexes `(?<!\w)skill(?!\w)` to avoid false positive substring matches.
  - Recognizes composite skill stacks (e.g., detecting `"MERN"` automatically infers `"MongoDB"`, `"Express.js"`, `"React"`, and `"Node.js"`).
  - Matches required skills at 80% weight and preferred skills at 20% weight.

### 5.6 Experience Extraction and Evaluation
- **Files & Primary Functions**:
  - `parsers/experience_parser.py`: `extract_experience(resume_text)`, `analyze_experience_timeline(entries)`
  - `scoring/experience_relevance.py`: `score_experience_relevance(entries, target_role, target_requirements, experience_requirement)`
- **Responsibility**: Identifies employment entries, extracts job titles, companies, dates, and responsibilities. Computes calendar duration, merges overlapping tenures, detects gaps, and scores entry relevance against JD requirements.
- **Inputs**: Masked resume text, target role string, JD responsibilities list, structured experience requirement dict.
- **Outputs**: List of parsed employment entries, timeline metrics (`total_experience_years`, `employment_gaps`, `overlapping_roles`), entry relevance scores, and an overall experience score.
- **Dependencies**: Built-in `datetime`, `re`, `difflib`, `functools`.
- **Details**:
  - Parses dates in diverse formats (`Month YYYY`, `MM/YYYY`, `YYYY`, `Present`) with hyphens, en dashes, em dashes, and `"to"`.
  - Merges concurrent employments to avoid double-counting experience months.
  - Evaluates entry relevance by combining title similarity (60%) and responsibility matching (40%). Similarity uses a hybrid of token Jaccard overlap (70%) and `SequenceMatcher` character similarity (30%), accelerated by `@functools.lru_cache(maxsize=2048)`.
  - If a resume contains no employment entries (e.g., a student fresher), experience relevance evaluates to `None` rather than fabricating an arbitrary zero or baseline score.

### 5.7 Education Extraction and Evaluation
- **Files & Primary Functions**:
  - `parsers/education_parser.py`: `extract_academic_profile(resume_text)`
  - `scoring/education_relevance.py`: `score_education_relevance(academic_profile, target_role)`
- **Responsibility**: Extracts academic degrees, fields of study, graduation years, and certifications from resume text. Evaluates educational relevance against the target job role.
- **Inputs**: Masked resume text and normalized target role string.
- **Outputs**: Academic profile dictionary (`education`, `certifications`) and education relevance scores (0 to 100 or `None`).
- **Dependencies**: Built-in `re`.
- **Details**:
  - `extract_education()` identifies degree names using regex patterns, extracts fields of study from following text segments, extracts graduation years, and attaches any nearby institution lines matched by simple keyword heuristics (`university`, `college`, `institute`).
  - `extract_certifications()` identifies lines with certification keywords and assigns broad relevance categories (`cloud`, `programming`, `ai_ml`, etc.).
  - `score_education_relevance()` evaluates degree names and fields of study against the target role category (technical disciplines for engineering roles; management, HR, and commerce disciplines for HR roles). It does not score institution names or evaluate institution prestige.
  - Scores each degree entry: +70 points for discipline match, +30 points for recognized degree level (capped at 100). Returns `None` if no education entries are found.

### 5.8 Semantic Similarity
- **Files & Primary Functions**:
  - `scoring/semantic_matcher.py`: `SemanticMatcher`, `similarity(text_a, text_b)`
- **Responsibility**: Computes overall lexical/semantic document similarity between the full resume text and full JD text.
- **Inputs**: Resume text string and JD text string (`text_a`, `text_b`).
- **Outputs**: Float similarity score from 0.0 to 100.0 (returns `0.0` if either input string is empty or whitespace-only).
- **Dependencies**: Built-in `re`, `math`, `collections`, `functools`.
- **Details**:
  - When either `text_a` or `text_b` is empty or whitespace-only, `SemanticMatcher.similarity()` explicitly returns `0.0`. In the caller pipeline ([`main_ats_scorer.py:119-120`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/main_ats_scorer.py#L119-L120)), this `0.0` is normalized to `None` if either document is empty, so an empty document is treated as a missing component rather than an evaluated score of zero.
  - Checks once at module load whether `sentence-transformers` is installed. When uninstalled, operates in `token-bigram-fallback` mode.
  - Generates L2-normalized sparse frequency vectors over alphanumeric unigrams and adjacent bigrams, computing cosine similarity via `_cosine_sparse`.
  - Accelerated via `@functools.lru_cache(maxsize=256)`. Output scores are lexical similarity indicators, not hiring probabilities.

### 5.9 ATS Score Calculation
- **Files & Primary Functions**:
  - `scoring/ats_scorer.py`: `calculate_ats_score(component_scores, role, weights, min_coverage)`
- **Responsibility**: Aggregates component scores into a weighted final ATS score, renormalizes weights when components are missing, and computes data coverage percentage.
- **Inputs**: Component scores dict (`skill_match`, `experience_relevance`, `education_alignment`, `semantic_similarity`), role string, optional custom weights dict, minimum coverage threshold (default: 80%).
- **Outputs**: Dictionary with `"ats_score"`, `"coverage_percentage"`, `"missing_components"`, `"manual_review_required"`, and `"score_breakdown"`.
- **Dependencies**: None (pure Python arithmetic and validation).
- **Details**:
  - Assigns weights based on role: `Software Developer` (Skill 45%, Exp 25%, Edu 10%, Semantic 20%), `AI Engineer` (Skill 35%, Exp 25%, Edu 10%, Semantic 30%), or Default (Skill 40%, Exp 25%, Edu 15%, Semantic 20%).
  - If any component is `None`, its weight is excluded, and the available components are renormalized to 100%.
  - If coverage drops below 80% (`MIN_SCORE_COVERAGE`), sets `manual_review_required = True`.

### 5.10 Candidate Ranking and Shortlisting
- **Files & Primary Functions**:
  - `scoring/candidate_ranker.py`: `rank_candidates(candidate_reports)`
  - `scoring/shortlisting.py`: `classify_candidate(score, thresholds, manual_review_required)`, `shortlist_candidates(ranked_candidates, thresholds)`
  - `scoring/candidate_pipeline.py`: `process_candidates(candidate_reports, thresholds)`
  - `scoring/ranking_report.py`: `generate_ranking_report(candidates)`
- **Responsibility**: Sorts candidates descending by score, assigns integer ranks, classifies candidates into decision buckets, and formats human-readable text summaries.
- **Inputs**: List of candidate scoring dictionaries, optional threshold dictionary (`shortlist` default: 70, `review` default: 40).
- **Outputs**: Ranked candidate list with `"rank"` and `"recommendation"` fields, and formatted text report string.
- **Dependencies**: Built-in `copy`.
- **Details**:
  - Sorting is stable (Python TimSort preserves original input order for tied scores). Candidates with `ats_score = None` are placed at the bottom.
  - Recommendation rules:
    - If `manual_review_required == True` or `score is None`: **`manual_review`** (safeguard override).
    - If `score >= shortlist_threshold`: **`shortlist`**.
    - If `score >= review_threshold`: **`review`**.
    - Otherwise: **`reject_recommendation`**.

---

## 6. End-to-End Processing Workflow

The processing of a candidate against a job description follows an explicit, deterministic sequence. In [`main_ats_scorer.py::generate_candidate_report`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/main_ats_scorer.py#L42), the scoring components execute **strictly sequentially on a single thread**:

```
[Resume File]                [Job Description File]
      |                                |
      v                                v
1. extract_resume()          2. extract_jd_text()
      |                                |
      v                                v
3. mask_personal_attributes() 4. build_job_profile()
      |                                |
      +----------------+---------------+
                       |
                       v
       5. score_skill_match()
          (Extracts skills, matches required vs preferred)
                       |
                       v
       6. score_experience_relevance()
          (Parses employment dates, timeline, title & requirement match)
                       |
                       v
       7. score_education_relevance()
          (Parses degrees & certifications, evaluates role discipline)
                       |
                       v
       8. SemanticMatcher.similarity()
          (Token-bigram vector cosine similarity)
                       |
                       v
       9. calculate_ats_score()
          (Applies weights, renormalizes missing components, checks >=80% coverage)
                       |
                       v
      10. Generate Candidate JSON Report
```

### Execution Details:
1. **Extraction**: The resume is read from disk via `extract_resume()`, and the JD is read via `extract_jd_text()`. If the resume yields no text, a `ValueError` is raised immediately.
2. **Masking**: `mask_personal_attributes()` replaces emails and phone numbers with placeholders.
3. **JD Profiling**: `build_job_profile()` runs once per scoring request, identifying the job title, requirements, and required/preferred skills.
4. **Sequential Scoring**:
   - Step 5: `score_skill_match` evaluates skill coverage.
   - Step 6: `extract_experience`, `analyze_experience_timeline`, and `score_experience_relevance` evaluate work history.
   - Step 7: `extract_academic_profile` and `score_education_relevance` evaluate academic alignment.
   - Step 8: `SemanticMatcher().similarity` evaluates document-level lexical similarity.
5. **Aggregation**: `calculate_ats_score` validates all four component scores, applies weights, calculates data coverage, and sets the manual review flag if coverage is below 80%.
6. **Report Generation**: Output dictionary is structured with full explanations, component breakdowns, and timeline analysis.

---

## 7. Application Interfaces

### 7.1 Command-Line Interfaces (CLI)

#### 1. Single Candidate ATS Scorer (`main_ats_scorer.py`)
Scores a single resume against a job description and writes the report to `outputs/ats_scoring/`.
```bash
python main_ats_scorer.py --resume path/to/resume.pdf --job-description path/to/jd.txt [--role "Python Developer"]
```

#### 2. Candidate Batch Ranking CLI (`main_candidate_ranking.py`)
Ranks a collection of candidate reports for the same job description and writes `ranked_candidates.json` and `ranking_report.txt` to `outputs/candidate_ranking/`.
```bash
python main_candidate_ranking.py --reports report1.json report2.json --shortlist-threshold 70 --review-threshold 40
```

### 7.2 FastAPI REST Endpoints

The API is defined in [`api/main.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/api/main.py) and runs via Uvicorn.

| Method | Endpoint | Description | Request Payload | Response |
| :--- | :--- | :--- | :--- | :--- |
| `GET` | `/` | Service root and welcome message. | None | `{"message": "...", "status": "running", "version": "1.0.0"}` |
| `GET` | `/health` | Health check endpoint. | None | `{"status": "healthy"}` |
| `POST` | `/api/v1/resumes` | Uploads and validates a resume file (max 10MB, PDF/DOCX). | Multipart form: `file` | HTTP 201: `{"resume_id": UUID, "status": "uploaded", ...}` |
| `POST` | `/api/v1/scoring/jobs` | Submits an asynchronous scoring job for an uploaded resume and a JD file. | Form: `resume_id` (str), Multipart: `job_description` (file) | HTTP 202: `{"job_id": UUID, "resume_id": UUID, "status": "queued"}` |
| `GET` | `/api/v1/jobs/{job_id}` | Polls status and retrieves results of a scoring job. | Path: `job_id` | HTTP 200: Job record (`status`: `queued`, `processing`, `completed`, `failed`; `result`: report dict) |
| `POST` | `/api/v1/shortlisting` | Ranks and classifies a list of candidate report objects. | JSON: `ShortlistingRequest` (`candidate_reports`, `thresholds`) | HTTP 200: `{"total_candidates": int, "candidates": [...], "report": "..."}` |

### 7.3 Background Scoring Workflow in the API
When `POST /api/v1/scoring/jobs` is invoked:
1. The server validates that `resume_id` exists in `storage/resumes/`.
2. The uploaded JD file is validated and saved to `storage/job_descriptions/{job_id}.ext`.
3. A job record is created in `api/job_manager.py` with status `"queued"`.
4. FastAPI's `BackgroundTasks.add_task(process_scoring_job, job_id, resume_path, jd_path)` registers the synchronous scoring task.
5. FastAPI sends the HTTP 202 Accepted response with the `job_id`.
6. After the response is sent, the FastAPI/Starlette background-task runner executes synchronous task functions (`process_scoring_job`) in an in-process thread pool via `anyio.to_thread.run_sync`.
7. `process_scoring_job` updates the job status to `"processing"`, calls `generate_candidate_report()`, and on completion updates status to `"completed"` with the full scoring dictionary stored in the job's `"result"` field (or `"failed"` with an error message on exception).
8. **In-Process Execution vs. Distributed Queue**: This execution takes place entirely within the local Python process. It does not utilize a persistent external message broker or distributed worker queue (such as Celery, RQ, or RabbitMQ). If the process terminates while a job is running or queued, the task is lost.

---

## 8. Data Storage and File Handling

### 8.1 Disk Storage vs. In-Memory State
A clear architectural distinction exists between physical file storage and job execution state:

- **Uploaded Files on Disk (`storage/`)**:
  - Resumes are stored on disk at `storage/resumes/{resume_id}.{pdf|docx}`.
  - Job descriptions are stored on disk at `storage/job_descriptions/{job_id}.{pdf|docx|txt}`.
  - Files persist across server restarts.
- **Job Execution State in Memory (`api/job_manager.py`)**:
  - The job tracker stores all job records in a plain global Python dictionary: `jobs = {}`.
  - **Volatile State**: Job state is **not persisted** to a database or disk file.
  - **Single-Process Constraint**: If the Uvicorn process restarts, or if the server is deployed with multiple worker processes (`--workers N`), each worker has its own isolated memory space. Polling requests that route to a different worker process or occur after a restart will return `404 Not Found`.

### 8.2 Generated Output Reports
When executed via CLI, output reports are written as formatted UTF-8 JSON files:
- Single candidate scoring reports: `outputs/ats_scoring/{resume_stem}_vs_{jd_stem}_ats_report.json`
- Candidate ranking batches: `outputs/candidate_ranking/ranked_candidates.json` and `ranking_report.txt`

---

## 9. Caching and Logging

### 9.1 In-Memory Caching Mechanisms
To minimize redundant I/O and CPU overhead without introducing shared mutable state or cross-candidate data leakage, three specific caching mechanisms are implemented:

1. **Skill Dictionary Caching (`parsers/skill_extractor.py`)**:
   - The master JSON file (`data/skill_dictionary.json`) is cached in module-level memory alongside its filesystem modification time (`st_mtime_ns`).
   - If the file is modified on disk, `load_skill_dictionary()` automatically invalidates the cache and reloads.
   - Every caller receives an isolated dictionary clone via `_clone_dictionary()`, ensuring mutations cannot corrupt the shared cache.
   - Can be explicitly reset via `clear_skill_dictionary_cache()`.
2. **Semantic Fallback Vector Caching (`scoring/semantic_matcher.py`)**:
   - The token-bigram vector calculation `_cached_fallback_vector(text)` is decorated with `@functools.lru_cache(maxsize=256)`.
   - Repeated vectorization of identical texts (such as the same JD scored against multiple candidates) is retrieved instantly from memory.
3. **Experience Similarity Memoization (`scoring/experience_relevance.py`)**:
   - The string comparison function `calculate_similarity(text_a, text_b)` is decorated with `@functools.lru_cache(maxsize=2048)`.
   - Caches repeated string comparisons between candidate bullet points and static JD requirement sentences.

### 9.2 Logging Configuration
- Configured in [`utils/logger.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/utils/logger.py).
- Ensures the `logs/` directory exists and initializes standard Python logging.
- Formats logs as `%(asctime)s - %(levelname)s - %(message)s` and writes directly to `logs/app.log`.
- Log entries are generated across API lifecycle events (file uploads, job enqueuing, background task completion, shortlisting requests, and HTTP error handlers).

---

## 10. Testing Structure

### 10.1 Pytest Architecture
The test suite is located in [`tests/`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/tests) and executed with `pytest`. It comprises 28 test files containing **159 automated tests**, all passing with 0 failures:

| Test Module Category | Key Test Files | Scope of Coverage |
| :--- | :--- | :--- |
| **Document Parsers** | `test_pdf_parser.py`, `test_docx_parser.py`, `test_resume_extractor.py`, `test_file_handler.py` | Valid PDF/DOCX extraction, merged-cell handling, 0-byte files, corrupt archives. |
| **Text Sanitization** | `test_text_cleaner.py`, `test_resume_normalizer.py`, `test_privacy_masker.py` | Control character removal, Unicode normalization, email/phone masking. |
| **Entity Parsers** | `test_skill_extractor.py`, `test_experience_parser.py`, `test_education_step1.py`, `test_jd_parser.py` | Canonical skills, synonym expansion, date ranges, timeline overlap merging, degree extraction. |
| **Component Scorers** | `test_skill_matcher.py`, `test_experience_relevance.py`, `test_education_relevance.py`, `test_semantic_matcher.py` | 80/20 skill weighting, experience title/responsibility matching, role-adaptive education, token-bigram cosine similarity. |
| **Scoring Governance** | `test_ats_scorer.py`, `test_candidate_ranker.py`, `test_shortlisting.py`, `test_ranking_report.py`, `test_fairness_evaluation.py` | Renormalization math, coverage percentage, `<80%` manual review flag, score thresholding, stable rank sorting. |
| **REST API** | `test_api.py` | Upload endpoints, magic-byte format validation, asynchronous scoring jobs, status polling, shortlisting API. |
| **Milestone Regressions** | `test_day17_regressions.py`, `test_day18_optimizations.py` | 11 Day 17 regression tests (Unicode dashes, fresher resumes, HR roles) and 9 Day 18 optimization tests (cache isolation, deterministic `os.utime` invalidation, parser robustness). |

*Note on Execution Environment*: `test_api.py` utilizes FastAPI `TestClient`, which requires loopback network sockets. In Windows sandboxed environments, loopback calls can block; API integration tests must run with network/loopback permissions enabled (`BypassSandbox: true`).

---

## 11. Current Limitations and Known Technical Debt

1. **Lexical Fallback Instead of Neural Embeddings**:
   - `sentence-transformers` is not installed in the standard environment. The ATS uses a token-bigram lexical cosine fallback. While fast and transparent, it matches words and adjacent pairs rather than true conceptual or contextual semantics.
2. **Resume Section Classifier Omission**:
   - [`parsers/resume_section_classifier.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/parsers/resume_section_classifier.py) was built and tested as a standalone module, but it is **not integrated into `main_ats_scorer.py`**. The main scoring pipeline relies on individual regex-based extractors scanning the entire document text.
3. **Limited Customized Role Weights**:
   - In [`scoring/ats_scorer.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/scoring/ats_scorer.py), customized weight profiles exist for exactly two roles: `"Software Developer"` and `"AI Engineer"`. All other roles (including all HR titles, Data Scientist, DevOps, etc.) default to the standard 40/25/15/20 weights.
4. **Volatile In-Memory API Job Storage**:
   - The REST API stores job metadata and scoring results in a global Python dictionary (`jobs = {}` in `api/job_manager.py`). Restarting the server wipes all job history, and multi-worker Uvicorn configurations will experience intermittent 404 errors due to unshared memory across worker processes.
5. **In-Process Synchronous Background Tasks**:
   - FastAPI's `BackgroundTasks` executes candidate scoring within the same Python process. Heavy text diffing and scoring across concurrent users competes for the Python Global Interpreter Lock (GIL) and CPU resources.
6. **DOCX XML DOM Memory Retention**:
   - `python-docx` loads the entire Word XML package into memory, resulting in a peak memory footprint of ~5.45 MB per DOCX file compared to ~0.05 MB for PyMuPDF PDF parsing.
7. **Static Dictionaries and Hardcoded Regexes**:
   - Skill identification relies on `data/skill_dictionary.json`, and education identification relies on hardcoded regex patterns in `education_parser.py`. Unlisted emerging technologies or specialized degrees require periodic manual updates to static lists.

---

## 12. Future Improvement Areas

*The following items represent proposed architectural improvements for future development and are not part of the current implementation:*

1. **Persistent Job and Result Storage**:
   - Replace the in-memory `jobs = {}` dictionary with a relational database (PostgreSQL/SQLite) or Redis key-value store to ensure persistent job states and enable multi-worker API scaling.
2. **Distributed Asynchronous Task Queue**:
   - Migrate scoring job execution from FastAPI `BackgroundTasks` to a distributed task queue (e.g., Celery, Redis Queue, or ARQ) with dedicated background worker processes.
3. **Optional Neural Embeddings via Quantized Microservice**:
   - Introduce dense embedding models (e.g., `all-MiniLM-L6-v2`) hosted via an external embedding microservice or ONNX Runtime to provide true semantic matching without imposing massive multi-gigabyte memory footprints on the main application process.
4. **Streaming DOCX Extraction**:
   - Explore streaming XML extraction (`xml.etree.cElementTree.iterparse` targeting `word/document.xml`) for DOCX files to reduce the ~5.45 MB DOM memory overhead during high-volume ingestion.
5. **Dynamic Role-Weight Profiles**:
   - Expand `ROLE_WEIGHTS` in `ats_scorer.py` to support role-specific weightings for non-technical disciplines (e.g. emphasizing experience and education for managerial and HR roles).
6. **Integration of Section Classification**:
   - Refactor `main_ats_scorer.py` to optionally utilize `parsers/resume_section_classifier.py` for structured block segmentation, reducing search spaces for entity parsers and improving extraction precision on non-standard layouts.

