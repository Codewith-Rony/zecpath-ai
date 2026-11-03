# Zecpath AI – Day 17 ATS Accuracy, Reliability & Role Adaptability Report

## 1. Executive Summary

This report documents the Day 17 investigation, root cause analysis, targeted implementation fixes, regression testing, and before-and-after evaluation matrix for the Zecpath AI Applicant Tracking System (ATS).

In the initial Day 17 evaluation across 48 resume–job description combinations (12 synthetic candidates $\times$ 4 job descriptions):
- **100% of reports (48/48) had missing experience relevance**, triggering automated manual review safeguards on all candidates due to data coverage dropping below the 80% threshold.
- **50% of reports (24/48) had missing education alignment**, specifically impacting all non-technical candidate profiles.
- **50% of job roles (24/48) were incorrectly defaulted to Software Developer**, because Human Resources (HR) roles were not supported by the parser or role catalog.
- **Unsuitable candidates received inflated scores** (e.g., non-technical candidates scoring >70 on technical roles) due to section alias omissions and renormalization of weights across missing components.

Following minimal, targeted architectural fixes:
- **Experience extraction success rate improved from 0.0% to 100.0% (48/48)**.
- **Education alignment success rate improved from 50.0% to 100.0% (48/48)**.
- **Job role detection accuracy reached 100.0% (48/48)** with explicit support for technical and HR job families.
- **Scoring coverage reached 100.0% across all 48 evaluations** (up from an average of 68.8%), reducing spurious coverage-driven manual reviews from 48 to 0.
- **Candidate ranking integrity was restored**, dropping inflated unsuitable candidates (e.g., non-tech candidate on Junior Python Developer dropped from 72.23 to 19.47).
- **All 150 automated tests passed** (139 existing tests + 11 new Day 17 regression tests), preserving 100% test suite integrity and API contracts.

---

## 2. Dataset Description

The Day 17 evaluation dataset consists of:
- **12 Synthetic Resumes** across four distinct cohorts (stored in `data/testing/resumes/`):
  1. *Tech Fresher (T-F)*: `T-F01` (Aarav Menon - Python Dev), `T-F02` (Diya Joseph - Software Trainee), `T-F03` (Neha Varghese - QA Automation).
  2. *Tech Senior (T-S)*: `T-S01` (Vikram Nair - Backend Engineer, 9 yrs), `T-S02` (Meera Iyer - Full Stack Lead / Engineering Manager, 11 yrs), `T-S03` (Rahul Das - Senior Data Engineer, 7 yrs).
  3. *Non-Tech Fresher (N-F)*: `N-F01` (Ananya Pillai - HR Operations Intern), `N-F02` (Joel Mathew - Marketing Coordinator), `N-F03` (Sara Thomas - Business Analyst).
  4. *Non-Tech Senior (N-S)*: `N-S01` (Kavitha Rao - Senior HRBP, 12 yrs), `N-S02` (Arjun Fernandes - Senior Marketing Manager, 10 yrs), `N-S03` (Priya Menon - Senior Finance Analyst, 8 yrs).
- **4 Benchmark Job Descriptions** (stored in `data/testing/job_descriptions/`):
  1. `JD01`: Junior Python Developer (Engineering, Entry-level / 0–2 years)
  2. `JD02`: Senior Backend Engineer (Engineering, Senior / 6+ years)
  3. `JD03`: Junior HR Executive (Human Resources, Entry-level / 0–2 years)
  4. `JD04`: Senior HR Business Partner (Human Resources, Senior / 8+ years)
- **48 Evaluation Pairs**: Evaluated through the FastAPI asynchronous job manager and candidate scoring pipeline.
- **Ground Truth Reference**: Confirmed human reviewer labels in `data/testing/manual_evaluation_reference.csv` (5 Suitable, 6 Borderline, 37 Not Suitable).

---

## 3. Initial Test Results & Identified Root Causes

### 3.1 Issue 1: Missing Experience Relevance Across All 48 Reports
* **Symptom:** `experience_relevance` was missing in every evaluation result, reducing coverage to 60.0%–75.0% and forcing `manual_review_required = True`.
* **Root Causes:**
  1. **Mojibake Date Separator:** In `parsers/experience_parser.py`, the date separator pattern contained double-encoded UTF-8 bytes (`â€“` / `â€”`) instead of actual Unicode en-dash (`\u2013` / `–`) or em-dash (`\u2014` / `—`). All 12 test resumes utilized en-dash separators (e.g. `Jul 2021 – Present`), preventing any date range from matching.
  2. **Delimiter Mismatch:** Resumes formatted work history on single lines with pipe delimiters (e.g. `Senior Backend Engineer | Northstar Commerce | Jul 2021 – Present`). The parser only split on `\s+(?:at|@)\s+`.
  3. **Restricted Employment Terms:** `employment_terms` omitted common fresher and non-technical terms (`partner`, `executive`, `recruiter`, `trainee`, `coordinator`, `assistant`, `officer`, `generalist`).

### 3.2 Issue 2: Role Detection Failure for Non-Technical Jobs
* **Symptom:** Both `JD03` (Junior HR Executive) and `JD04` (Senior HR Business Partner) were identified as `"Software Developer"`.
* **Root Causes:**
  1. `ROLE_VARIATIONS` in `parsers/jd_parser.py` and `KNOWN_ROLES` in `scoring/skill_matcher.py` only contained software engineering titles.
  2. `main_ats_scorer.py` contained an unconditional fallback: `role = role_override or job_profile.get("title") or "Software Developer"`.

### 3.3 Issue 3: Section Alias Omission Causing Skill Mismatches & Score Inflation
* **Symptom:** In `JD01`, candidate `N-F03` (Sara Thomas, non-tech finance profile) received an inflated ATS score of **72.23** on Junior Python Developer.
* **Root Causes:**
  1. The JDs used headings `REQUIRED CRITERIA` and `PREFERRED CRITERIA`.
  2. `SECTION_ALIASES` in `parsers/jd_parser.py` did not map `"required criteria"` or `"preferred criteria"`, causing requirement lines to fall into `"general"`.
  3. Consequently, `required_skills` was empty (`[]`) for all 4 JDs.
  4. For `JD01`, optional skill search extracted only `"SQL"`. Since Sara had SQL in her resume, her preferred skill coverage was scored at 100%.
  5. With experience and education missing, the scorer renormalized weights over only `skill_match` (40) and `semantic_similarity` (20), inflating the score above 70.

### 3.4 Issue 4: Missing Education Alignment in 24 Non-Technical Reports
* **Symptom:** Education alignment was missing (`None`) in all 24 non-technical combinations.
* **Root Causes:**
  1. In `parsers/education_parser.py`, `degree_pattern` only matched technical degrees (`B.Tech`, `B.E.`, `M.Tech`, `B.Sc.`, `MCA`). Non-technical degrees (`BBA`, `MBA`, `B.Com`, `M.Com`, `PGDM`) were omitted.
  2. Field-of-study parsing only looked for `\bin\s+<field>`, failing on `<Degree>, <Field> | <Institution>`.
  3. In `scoring/education_relevance.py`, `relevant_fields` had no entries for HR or business roles.

### 3.5 Issue 5: Structured Experience Requirement Disconnect
* **Symptom:** `build_job_profile()` returns `experience_requirement` as a dictionary `{"minimum_years": ..., "maximum_years": ...}`, but `main_ats_scorer.py` checked `if isinstance(experience_requirement, str)`. Structured experience requirements were entirely ignored.

### 3.6 Issue 6: API Exception Handling Contract Inconsistency
* **Symptom:** `tests/test_api.py::test_resume_upload_invalid_extension` failed with `KeyError: 'detail'`.
* **Root Cause:** The custom `http_exception_handler` in `api/main.py` returned `{"error": ...}`, omitting FastAPI's standard top-level `"detail"` field.

---

## 4. Implemented Targeted Changes

All changes were implemented incrementally with verification at each step:

| File Modified | Summary of Targeted Changes |
|---|---|
| `parsers/experience_parser.py` | • Replaced mojibake with true Unicode en-dash (`\u2013`) and em-dash (`\u2014`) in date parsing regex, description trimming, and bullet removal.<br>• Added pipe delimiter (`\|`) parsing for `Job Title \| Company \| Dates` formats.<br>• Expanded `employment_terms` to support non-technical and fresher titles (`partner`, `executive`, `recruiter`, `coordinator`, `trainee`, `assistant`, `generalist`, `officer`).<br>• Guarded `parse_date` to prevent out-of-range numeric years.<br>• Collected responsibility lines following employment entries into candidate work history. |
| `parsers/jd_parser.py` | • Added section aliases: `"required criteria": "required"`, `"preferred criteria": "preferred"`, `"experience expectation": "experience"`, `"role summary": "about"`, `"manual review notes": "notes"`.<br>• Expanded `ROLE_VARIATIONS` with HR roles (`HR Executive`, `HR Manager`, `HR Business Partner`, `Talent Acquisition Specialist`, `Recruiter`) and seniority variants.<br>• Implemented prioritized role extraction in `extract_role()`: header line matching first, followed by top 5 lines, then full text using boundary regex and longest-match ordering.<br>• Expanded `EDUCATION_VARIATIONS` to support `BBA`, `MBA`, `B.Com`, `M.Com`, `Business Administration`, `Human Resources`.<br>• Updated `extract_skills` to match singular/plural synonym variants (`REST API` / `REST APIs`). |
| `scoring/skill_matcher.py` | • Added all recognized HR roles to `KNOWN_ROLES`. |
| `parsers/education_parser.py` | • Expanded `degree_pattern` and `normalize_degree` to parse and normalize `BBA`, `MBA`, `B.Com`, `M.Com`, `B.A.`, `M.A.`, `PGDM`, `Ph.D.`, `Bachelor of Business Administration`, `Master of Business Administration`, `Bachelor of Commerce`.<br>• Enhanced field extraction to support both `in <field>` and comma/pipe layouts (`<Degree>, <Field> \| <Institution>`). |
| `scoring/education_relevance.py` | • Added comprehensive relevant fields for HR roles (`human resources`, `business administration`, `management`, `psychology`, `commerce`, `organizational behavior`, `labor relations`, `communications`).<br>• Added flexible matching across combined degree and field text, ensuring candidates with relevant educational backgrounds are not penalized.<br>• Added `software systems` to technical role relevant fields. |
| `scoring/experience_relevance.py` | • Added support for structured `experience_requirement` parameter.<br>• Preserved title and responsibility similarity calculation without converting numeric years into text strings.<br>• Added structured experience level assessment. |
| `main_ats_scorer.py` | • Integrated timeline analysis using `analyze_experience_timeline()`.<br>• Passed structured experience requirements to experience assessment without inventing arbitrary scores.<br>• Set default unrecognized role to `"Undetected Role"` rather than `"Software Developer"`.<br>• Preserved role override functionality and existing scoring weights.<br>• Updated `_education_role()` to map HR role families. |
| `api/main.py` | • Updated `http_exception_handler` to return both `"detail": exc.detail` and `"error": {"code": ..., "message": exc.detail}`, preserving standard FastAPI error contracts while maintaining custom error structures. |
| `scripts/evaluation.py` | • Added `--output` argument allowing execution of the 48-pair evaluation matrix into `data/testing/ats_evaluation_results_v2.csv` without modifying the original baseline. |
| `tests/test_day17_regressions.py` | • Added 11 regression test cases covering Unicode date parsing, pipe layouts, HR role detection, section criteria mapping, non-technical degree extraction, and experience requirement integration. |

---

## 5. Before-and-After Evaluation Comparison

### 5.1 System Metric Comparison (48 Evaluation Pairs)

| Metric | Day 17 Baseline (`ats_evaluation_results.csv`) | Day 17 Post-Fix (`ats_evaluation_results_v2.csv`) | Absolute Change |
|---|---|---|---|
| **Total Scoring Jobs** | 48 / 48 (100.0%) | 48 / 48 (100.0%) | 0 |
| **Experience Extraction Success Rate** | 0.0% (0 / 48) | **100.0% (48 / 48)** | **+100.0%** |
| **Education Extraction Success Rate** | 50.0% (24 / 48) | **100.0% (48 / 48)** | **+50.0%** |
| **Job Role Detection Accuracy** | 50.0% (24 / 48) | **100.0% (48 / 48)** | **+50.0%** |
| **Average Component Coverage** | 68.8% | **100.0%** | **+31.2%** |
| **Pairs Meeting $\ge 80\%$ Coverage** | 0 / 48 (0.0%) | **48 / 48 (100.0%)** | **+100.0%** |
| **Manual Review Flag Rate** | 100.0% (48 / 48) | **0.0% (0 / 48)** | **-100.0%** |

### 5.2 Key Candidate Score Changes

| Candidate & Background | Target Role | Baseline Score (v1) | Post-Fix Score (v2) | Difference | Analysis |
|---|---|---|---|---|---|
| **N-F03 (Sara Thomas)**<br>Finance / B.Com Fresher | JD01: Junior Python Developer | **72.23** | **19.47** | **-52.76** | **Fixed**: Previously inflated due to missing required skills and 1 optional skill match (SQL). Now correctly rejected. |
| **T-S01 (Vikram Nair)**<br>Senior Backend Engineer | JD04: Senior HRBP | **39.27** | **10.79** | **-28.48** | **Fixed**: Technical engineer correctly receives minimal alignment against an HR leadership role. |
| **N-S02 (Arjun Fernandes)**<br>Senior Marketing Manager | JD04: Senior HRBP | **41.60** | **22.05** | **-19.55** | **Fixed**: Marketing candidate appropriately distinguished from strategic HR business partner requirements. |
| **N-S03 (Priya Menon)**<br>Senior Finance Analyst | JD03: Junior HR Executive | **74.58** | **59.99** | **-14.59** | **Improved**: Drop reflects actual lack of HR operations experience while acknowledging business transferable skills. |
| **N-F01 (Ananya Pillai)**<br>HR Assistant Intern | JD03: Junior HR Executive | 80.03 | **67.16** | -12.87 | **Calibrated**: Solid candidate now evaluated across all 4 components (100% coverage) rather than an inflated partial subset. |
| **T-F01 (Aarav Menon)**<br>Python Dev Fresher | JD01: Junior Python Developer | 70.10 | **62.81** | -7.29 | **Calibrated**: True positive candidate scores consistently in the top tier for entry-level Python development. |
| **T-S01 (Vikram Nair)**<br>Senior Backend Engineer | JD02: Senior Backend Engineer | 61.71 | **54.29** | -7.42 | **Calibrated**: High fit candidate maintains solid standing across all backend criteria. |

---

## 6. Classification Accuracy & Validation Metrics

To measure classification performance, the candidate shortlisting recommendations (`review` / `shortlist` for score $\ge 40$ vs. `reject_recommendation` for score $< 40$) were evaluated against confirmed reviewer decisions in `data/testing/manual_evaluation_reference.csv`.

In accordance with testing standards, **borderline cases are evaluated separately** from the binary metrics.

### 6.1 Binary Classification Metrics (Excluding 6 Borderline Cases; $N = 42$)

* **Ground Truth**: 5 Suitable, 37 Not Suitable
* **True Positives (TP)**: 3 (`T-F01` on JD01, `T-S01` on JD02, `N-F01` on JD03)
* **True Negatives (TN)**: 28 (unsuitable candidates correctly rejected below 40)
* **False Positives (FP)**: 9 (unsuitable candidates scoring $\ge 40$)
* **False Negatives (FN)**: 2 (`T-S02` on JD02, `N-S01` on JD04)

$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN} = \frac{3 + 28}{42} = \mathbf{73.8\%}$$

$$\text{Precision} = \frac{TP}{TP + FP} = \frac{3}{3 + 9} = \mathbf{25.0\%}$$

$$\text{Recall} = \frac{TP}{TP + FN} = \frac{3}{3 + 2} = \mathbf{60.0\%}$$

$$\text{F1 Score} = 2 \times \frac{\text{Precision} \times \text{Recall}}{\text{Precision} + \text{Recall}} = \mathbf{35.3\%}$$

### 6.2 Borderline Cohort Evaluation ($N = 6$)

Borderline candidates possess transferable capabilities or relevant experience, but with minor gaps noted in human review:
- `T-F02` on JD01 (Java/MySQL background, no Python): **31.35** $\rightarrow$ `Reject (<40)`
- `T-F03` on JD01 (QA automation background, pytest/SQL present): **48.37** $\rightarrow$ `Review (>=40)`
- `T-S03` on JD01 (Senior Data Engineer on entry Python): **36.76** $\rightarrow$ `Reject (<40)`
- `T-S03` on JD02 (Data Engineer on Senior Backend): **48.00** $\rightarrow$ `Review (>=40)`
- `N-F02` on JD03 (Marketing Coordinator on Junior HR): **60.37** $\rightarrow$ `Review (>=40)`
- `N-F03` on JD03 (Business Analyst on Junior HR): **59.79** $\rightarrow$ `Review (>=40)`

---

## 7. Remaining Limitations & Analysis of Discrepancies

1. **Seniority vs. Level Mismatches (Root of False Positives)**:
   - Several False Positives (e.g. `T-F01` on `JD02`, `N-F01` on `JD04`) occur because the candidates' skills and education align well with the domain, but they are freshers applying for senior roles (6+ or 8+ years).
   - Currently, `ats_scorer.py` weights skill matching (40%), experience relevance (25%), education (15%), and semantic similarity (20%). It does not hard-filter based on minimum experience duration.
   - The structured `experience_level_assessment` now captures this (`candidate_total_years` vs. `required_minimum_years`), but preserving the existing scoring weights precluded applying an unapproved penalty directly to the composite ATS score.
2. **Generic Keyword Extraction in HR JDs (Root of False Negative on N-S01)**:
   - For `JD04` (Senior HRBP), only `"Communication"` was extracted as a required skill from the criteria section.
   - `N-S01` (12 years in HR, Senior HRBP) had specific strategic competencies (`Workforce Planning`, `Employee Relations`, `Talent Acquisition`, `HR Analytics`), but did not explicitly repeat the generic word "Communication" in her resume skills list.
   - Because `skill_match` has a 40% weight, a 0 score on `Communication` pulled her overall score to 34.62, causing a false negative.
3. **Alternative Technology Recognition (Root of False Negative on T-S02)**:
   - `JD02` states: "Significant hands-on experience with Python or another production backend language."
   - The parser extracted `Python` and `SQL` as required skills.
   - `T-S02` has 11 years of experience in Java, Node.js, Spring Boot, and PostgreSQL, but no Python. Since alternative languages were not expanded as OR-conditions in the required skill list, her skill score suffered.

---

## 8. Future Improvement Backlog

1. **Experience Duration Gating / Level Fit Factor**:
   - Introduce an explicit level fit multiplier or eligibility filter in candidate shortlisting when a candidate's actual work experience (from `analyze_experience_timeline`) deviates substantially from the required minimum years (e.g. fresher applying for a 8+ year senior role).
2. **Domain-Specific Skill Expansion for Non-Technical Roles**:
   - Expand `data/skill_dictionary.json` to include standard HR, recruitment, and people operations skills (`Talent Acquisition`, `Workforce Planning`, `Employee Relations`, `Onboarding`, `HR Information Systems`, `Performance Management`).
3. **Alternative / Disjunctive Skill Requirements**:
   - Enhance the job description parser and skill matcher to recognize disjunctive criteria (e.g., "Python OR Java OR Node.js"), preventing candidates with valid alternative production languages from being marked missing on required skills.
4. **Persistent Job Queue & Storage**:
   - Migrate in-memory job tracking in `api/job_manager.py` to Redis/database storage to ensure durability across application restarts.

