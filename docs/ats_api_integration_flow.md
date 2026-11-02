
# Zecpath AI – ATS API Integration Flow

## 1. Architecture

The ATS API connects external applications to the existing Zecpath AI processing engine.

Main components:

1. Frontend / Recruiter Dashboard
2. FastAPI REST API
3. Resume and Job Description Storage
4. ATS Processing Engine
5. Background Job Manager
6. Candidate Ranking and Shortlisting Module

## 2. Resume Upload Flow

1. Recruiter selects a resume.
2. Frontend sends the file to `POST /api/v1/resumes`.
3. API validates the extension, file structure, and size.
4. API generates a unique resume ID.
5. Resume is saved in local storage.
6. API returns the resume ID and upload status.

## 3. ATS Scoring Flow

1. Recruiter submits a resume ID and job description.
2. API validates the resume ID.
3. API validates and saves the job description.
4. A scoring job is created with a unique job ID.
5. FastAPI schedules background processing.
6. Job status changes from queued to processing.
7. Existing `generate_candidate_report()` function is executed.
8. ATS report is stored in the job manager.
9. Job status changes to completed or failed.

## 4. Result Retrieval Flow

1. Frontend requests `GET /api/v1/jobs/{job_id}`.
2. API retrieves the job record.
3. API returns the current status.
4. If completed, the ATS report is included in the response.

## 5. Shortlisting Flow

1. Frontend submits candidate reports and thresholds.
2. API validates the request using Pydantic schemas.
3. Candidate reports are passed to the existing candidate pipeline.
4. Candidates are ranked by ATS score.
5. Shortlisting logic assigns recommendations.
6. Candidates requiring manual review receive the manual_review classification.
7. API returns ranked candidates and a ranking report.

## 6. Data Flow Diagram

Frontend
    |
    v
FastAPI REST API
    |
    +---- Resume Upload
    |          |
    |          v
    |     Resume Storage
    |
    +---- Scoring Job
    |          |
    |          v
    |     Background Task
    |          |
    |          v
    |     ATS Engine
    |          |
    |          v
    |     Candidate Report
    |
    +---- Shortlisting
               |
               v
        Candidate Pipeline
               |
               v
       Ranked Candidates

## 7. Current Implementation Limitations

- Job state is stored in memory.
- Uploaded files are stored locally.
- Background processing runs within the API process.
- No authentication or authorization is implemented.
- Production deployment requires persistent storage, durable task processing, and additional security controls.
