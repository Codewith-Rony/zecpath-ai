
# Zecpath AI – ATS API Specification

## 1. Overview

The Zecpath AI ATS API exposes resume upload, candidate scoring, job status tracking, and candidate shortlisting functionality through REST endpoints.

**Base URL:** `http://127.0.0.1:8000`

**API Version:** v1

**Framework:** FastAPI

## 2. API Endpoints

### 2.1 Health Check

- Method: GET
- Endpoint: `/health`
- Purpose: Check whether the API is running.

Success response (200):

{
  "status": "healthy"
}

### 2.2 Resume Upload

- Method: POST
- Endpoint: `/api/v1/resumes`
- Content-Type: `multipart/form-data`
- Field: `file`
- Accepted formats: PDF, DOCX
- Maximum file size: 10 MB

Success response (201):

{
  "message": "Resume uploaded successfully.",
  "resume_id": "generated-uuid",
  "original_filename": "resume.pdf",
  "file_type": "pdf",
  "status": "uploaded"
}

The API generates a unique ID and stores the uploaded file using that ID.

### 2.3 Submit ATS Scoring Job

- Method: POST
- Endpoint: `/api/v1/scoring/jobs`
- Content-Type: `multipart/form-data`

Fields:

- `resume_id`: UUID of a previously uploaded resume.
- `job_description`: PDF, DOCX, or TXT file.
- Maximum file size: 10 MB.

Success response (202):

{
  "message": "ATS scoring job submitted successfully.",
  "job_id": "generated-job-uuid",
  "resume_id": "resume-uuid",
  "status": "queued"
}

The API schedules ATS processing using FastAPI BackgroundTasks.

### 2.4 Retrieve Job Status and Result

- Method: GET
- Endpoint: `/api/v1/jobs/{job_id}`

Possible job statuses:

- queued
- processing
- completed
- failed

The response contains the job ID, resume ID, creation timestamp, status, result, and error information.

A completed job includes the ATS candidate report.

### 2.5 Candidate Shortlisting

- Method: POST
- Endpoint: `/api/v1/shortlisting`
- Content-Type: `application/json`

Request fields:

- `candidate_reports`: List of candidate reports.
- `thresholds.shortlist`: Minimum score for shortlist classification.
- `thresholds.review`: Minimum score for review classification.

Default thresholds:

- Shortlist: 70
- Review: 40

Success response (200):

{
  "message": "Candidate shortlisting completed successfully.",
  "status": "completed",
  "total_candidates": 1,
  "candidates": [],
  "report": "Candidate ranking report"
}

Candidates requiring manual review are classified as `manual_review`.

## 3. Error Handling

| HTTP Status | Meaning |
|---|---|
| 400 | Invalid file or request |
| 404 | Resume or job not found |
| 413 | Uploaded file exceeds size limit |
| 422 | Request validation failure |
| 201 | Resource created |
| 202 | Scoring job accepted |
| 200 | Request successful |

Scoring failures are represented by the job status `failed`.

## 4. Asynchronous Processing

ATS scoring is scheduled as a background task.

The client receives a job ID immediately and can retrieve the processing status through the job status endpoint.

Current implementation uses in-memory job storage. Job records are lost when the API process restarts.

## 5. Security and Validation

- Only supported file extensions are accepted.
- PDF and DOCX file structures are checked.
- Uploads are limited to 10 MB.
- UUIDs are used for stored filenames.
- Original filenames are not used as storage paths.
- Invalid resume IDs are rejected.

## 6. API Documentation

Interactive API documentation is available through:

`/docs`

OpenAPI schema is available through:

`/openapi.json`

## 7. Future Improvements

- Persistent job storage.
- Redis/Celery or another durable background task queue.
- Authentication and authorization.
- Rate limiting.
- Production-grade logging and monitoring.
- Automated cleanup of uploaded files.
- Database-backed resume and candidate management.
