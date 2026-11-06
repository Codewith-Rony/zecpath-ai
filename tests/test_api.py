from io import BytesIO
from pathlib import Path
from uuid import uuid4
from zipfile import ZipFile

import pytest
from fastapi.testclient import TestClient

from api.job_manager import create_job, get_job, jobs, update_job
from api.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures and Helpers
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def isolate_api_environment(tmp_path, monkeypatch):
    """Isolate storage directories and in-memory job state for every test."""
    resume_storage = tmp_path / "storage" / "resumes"
    jd_storage = tmp_path / "storage" / "job_descriptions"
    resume_storage.mkdir(parents=True, exist_ok=True)
    jd_storage.mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr("api.main.RESUME_STORAGE", resume_storage)
    monkeypatch.setattr("api.main.JD_STORAGE", jd_storage)

    jobs.clear()
    yield
    jobs.clear()


def create_mock_docx() -> bytes:
    """Generate a minimal valid DOCX byte stream containing word/document.xml."""
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zf:
        zf.writestr(
            "word/document.xml",
            "<w:document><w:body><w:p/></w:body></w:document>"
        )
    return buffer.getvalue()


def create_mock_pdf() -> bytes:
    """Generate a minimal valid PDF byte stream."""
    return b"%PDF-1.4\n% Mock PDF content for API testing\n%%EOF"


# ---------------------------------------------------------------------------
# Base & Health Endpoints (Existing Tests)
# ---------------------------------------------------------------------------

def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


# ---------------------------------------------------------------------------
# POST /api/v1/resumes Tests
# ---------------------------------------------------------------------------

def test_resume_upload_invalid_extension():
    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "resume.txt",
                b"Invalid resume",
                "text/plain"
            )
        }
    )

    assert response.status_code == 400
    assert "Only PDF and DOCX" in response.json()["detail"]


def test_resume_upload_valid_pdf():
    fake_pdf = b"%PDF-1.4\nTest PDF content"

    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "test_resume.pdf",
                fake_pdf,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 201

    data = response.json()

    assert data["status"] == "uploaded"
    assert data["file_type"] == "pdf"
    assert "resume_id" in data


def test_resume_upload_valid_docx():
    docx_bytes = create_mock_docx()

    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "test_resume.docx",
                docx_bytes,
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == "uploaded"
    assert data["file_type"] == "docx"
    assert data["original_filename"] == "test_resume.docx"
    assert "resume_id" in data


def test_resume_upload_empty_file():
    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "empty_resume.pdf",
                b"",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Uploaded file is empty."


def test_resume_upload_invalid_pdf_content():
    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "not_a_pdf.pdf",
                b"Not a PDF header",
                "application/pdf"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file."


def test_resume_upload_invalid_docx_content():
    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "corrupt.docx",
                b"Not a zip archive",
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file."


def test_resume_upload_docx_missing_document_xml():
    buffer = BytesIO()
    with ZipFile(buffer, "w") as zf:
        zf.writestr("unrelated.txt", "Some content")

    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "missing_xml.docx",
                buffer.getvalue(),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )
        }
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file."


def test_resume_upload_exceeds_size_limit():
    large_payload = b"%PDF-" + b"0" * (10 * 1024 * 1024)

    response = client.post(
        "/api/v1/resumes",
        files={
            "file": (
                "large.pdf",
                large_payload,
                "application/pdf"
            )
        }
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "File size exceeds the 10 MB limit."


# ---------------------------------------------------------------------------
# POST /api/v1/scoring/jobs Tests
# ---------------------------------------------------------------------------

def test_submit_scoring_job_invalid_resume_id():
    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": "not-a-valid-uuid"},
        files={"job_description": ("jd.txt", b"Software Engineer", "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid resume ID."


def test_submit_scoring_job_resume_not_found():
    unknown_uuid = str(uuid4())
    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": unknown_uuid},
        files={"job_description": ("jd.txt", b"Software Engineer", "text/plain")}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found. Upload the resume first."


def test_submit_scoring_job_invalid_jd_extension():
    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.json", b'{"title": "Developer"}', "application/json")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF, DOCX and TXT job descriptions are allowed."


def test_submit_scoring_job_empty_jd():
    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.txt", b"", "text/plain")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Job description is empty."


def test_submit_scoring_job_jd_exceeds_size_limit():
    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    large_jd = b"x" * (10 * 1024 * 1024 + 1)
    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.txt", large_jd, "text/plain")}
    )

    assert response.status_code == 413
    assert response.json()["detail"] == "Job description exceeds the 10 MB limit."


def test_submit_scoring_job_invalid_pdf_jd():
    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.pdf", b"Corrupt PDF data", "application/pdf")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid PDF file."


def test_submit_scoring_job_invalid_docx_jd():
    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.docx", b"Not a zip file", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Invalid DOCX file."


def test_submit_scoring_job_success_mocked_background(monkeypatch):
    recorded_calls = []

    def mock_process_scoring_job(job_id, resume_path, jd_path):
        recorded_calls.append((job_id, resume_path, jd_path))

    monkeypatch.setattr("api.main.process_scoring_job", mock_process_scoring_job)

    res = client.post(
        "/api/v1/resumes",
        files={"file": ("resume.pdf", create_mock_pdf(), "application/pdf")}
    )
    assert res.status_code == 201
    resume_id = res.json()["resume_id"]

    response = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("jd.txt", b"Python Developer with 3+ years experience.", "text/plain")}
    )

    assert response.status_code == 202
    data = response.json()
    assert data["message"] == "ATS scoring job submitted successfully."
    assert data["resume_id"] == resume_id
    assert data["status"] == "queued"
    job_id = data["job_id"]

    assert len(recorded_calls) == 1
    call_job_id, call_resume_path, call_jd_path = recorded_calls[0]
    assert call_job_id == job_id
    assert call_resume_path.is_file()
    assert call_jd_path.is_file()

    stored_job = get_job(job_id)
    assert stored_job is not None
    assert stored_job["status"] == "queued"
    assert stored_job["resume_id"] == resume_id


def test_submit_job_and_execute_full_scoring_pipeline():
    """End-to-end integration test: upload sample files, submit scoring job,

    allow the real background task to execute via TestClient, and verify
    the completed score report.
    """
    project_root = Path(__file__).resolve().parent.parent
    sample_resume = project_root / "data" / "sample_resumes" / "sample_resume.pdf"
    sample_jd = project_root / "data" / "sample_jobs" / "junior_software_dev.txt"

    assert sample_resume.is_file(), f"Sample resume missing: {sample_resume}"
    assert sample_jd.is_file(), f"Sample JD missing: {sample_jd}"

    resume_bytes = sample_resume.read_bytes()
    jd_bytes = sample_jd.read_bytes()

    upload_res = client.post(
        "/api/v1/resumes",
        files={"file": ("sample_resume.pdf", resume_bytes, "application/pdf")}
    )
    assert upload_res.status_code == 201
    resume_id = upload_res.json()["resume_id"]

    submit_res = client.post(
        "/api/v1/scoring/jobs",
        data={"resume_id": resume_id},
        files={"job_description": ("junior_software_dev.txt", jd_bytes, "text/plain")}
    )
    assert submit_res.status_code == 202
    job_id = submit_res.json()["job_id"]
    assert submit_res.json()["status"] == "queued"

    # In TestClient, BackgroundTasks execute synchronously before client.post returns.
    # Therefore, checking the job reflects the completed status.
    status_res = client.get(f"/api/v1/jobs/{job_id}")
    assert status_res.status_code == 200
    job_info = status_res.json()

    assert job_info["job_id"] == job_id
    assert job_info["status"] == "completed"
    assert job_info["error"] is None
    assert isinstance(job_info["result"], dict)
    assert "ats_score" in job_info["result"]
    assert 0 <= job_info["result"]["ats_score"] <= 100
    assert "score_breakdown" in job_info["result"]


# ---------------------------------------------------------------------------
# GET /api/v1/jobs/{job_id} Tests
# ---------------------------------------------------------------------------

def test_get_job_unknown_id():
    response = client.get("/api/v1/jobs/non-existent-uuid")
    assert response.status_code == 404
    assert response.json()["detail"] == "Job not found."


def test_get_job_status_queued():
    job = create_job("sample-resume-id")
    response = client.get(f"/api/v1/jobs/{job['job_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job["job_id"]
    assert data["status"] == "queued"
    assert data["result"] is None
    assert data["error"] is None


def test_get_job_status_processing():
    job = create_job("sample-resume-id")
    update_job(job["job_id"], "processing")

    response = client.get(f"/api/v1/jobs/{job['job_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job["job_id"]
    assert data["status"] == "processing"
    assert data["result"] is None
    assert data["error"] is None


def test_get_job_status_completed():
    job = create_job("sample-resume-id")
    dummy_report = {"ats_score": 87.5, "candidate_name": "Test Candidate"}
    update_job(job["job_id"], "completed", result=dummy_report)

    response = client.get(f"/api/v1/jobs/{job['job_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job["job_id"]
    assert data["status"] == "completed"
    assert data["result"] == dummy_report
    assert data["error"] is None


def test_get_job_status_failed():
    job = create_job("sample-resume-id")
    error_msg = "Scoring failed. Check the server logs."
    update_job(job["job_id"], "failed", error=error_msg)

    response = client.get(f"/api/v1/jobs/{job['job_id']}")

    assert response.status_code == 200
    data = response.json()
    assert data["job_id"] == job["job_id"]
    assert data["status"] == "failed"
    assert data["result"] is None
    assert data["error"] == error_msg


# ---------------------------------------------------------------------------
# POST /api/v1/shortlisting Tests
# ---------------------------------------------------------------------------

def test_shortlisting_api():
    payload = {
        "candidate_reports": [
            {
                "candidate_name": "Candidate A",
                "ats_score": 85.5,
                "manual_review_required": False
            },
            {
                "candidate_name": "Candidate B",
                "ats_score": 55.77,
                "manual_review_required": True
            },
            {
                "candidate_name": "Candidate C",
                "ats_score": 35,
                "manual_review_required": False
            }
        ],
        "thresholds": {
            "shortlist": 70,
            "review": 40
        }
    }

    response = client.post(
        "/api/v1/shortlisting",
        json=payload
    )

    assert response.status_code == 200

    data = response.json()

    assert data["total_candidates"] == 3

    candidates = data["candidates"]

    assert candidates[0]["recommendation"] == "shortlist"
    assert candidates[1]["recommendation"] == "manual_review"
    assert candidates[2]["recommendation"] == "reject_recommendation"


def test_shortlisting_invalid_thresholds():
    payload = {
        "candidate_reports": [
            {
                "candidate_name": "Candidate A",
                "ats_score": 85
            }
        ],
        "thresholds": {
            "shortlist": 60,
            "review": 70
        }
    }

    response = client.post(
        "/api/v1/shortlisting",
        json=payload
    )

    assert response.status_code == 422


def test_shortlisting_default_thresholds():
    payload = {
        "candidate_reports": [
            {
                "candidate_name": "Candidate High",
                "ats_score": 82.0,
                "manual_review_required": False
            },
            {
                "candidate_name": "Candidate Mid",
                "ats_score": 55.0,
                "manual_review_required": False
            },
            {
                "candidate_name": "Candidate Low",
                "ats_score": 25.0,
                "manual_review_required": False
            }
        ]
    }

    response = client.post(
        "/api/v1/shortlisting",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_candidates"] == 3
    candidates = data["candidates"]
    assert candidates[0]["candidate_name"] == "Candidate High"
    assert candidates[0]["recommendation"] == "shortlist"
    assert candidates[1]["candidate_name"] == "Candidate Mid"
    assert candidates[1]["recommendation"] == "review"
    assert candidates[2]["candidate_name"] == "Candidate Low"
    assert candidates[2]["recommendation"] == "reject_recommendation"


def test_shortlisting_empty_candidates():
    payload = {
        "candidate_reports": []
    }

    response = client.post(
        "/api/v1/shortlisting",
        json=payload
    )

    assert response.status_code == 200
    data = response.json()

    assert data["total_candidates"] == 0
    assert data["candidates"] == []
    assert "No candidates available." in data["report"]


def test_shortlisting_out_of_range_thresholds():
    # Shortlist threshold above 100
    res_high = client.post(
        "/api/v1/shortlisting",
        json={
            "candidate_reports": [{"candidate_name": "A", "ats_score": 80}],
            "thresholds": {"shortlist": 105, "review": 50}
        }
    )
    assert res_high.status_code == 422

    # Review threshold below 0
    res_low = client.post(
        "/api/v1/shortlisting",
        json={
            "candidate_reports": [{"candidate_name": "A", "ats_score": 80}],
            "thresholds": {"shortlist": 80, "review": -10}
        }
    )
    assert res_low.status_code == 422


def test_shortlisting_invalid_candidate_data():
    # ATS score exceeding 100
    res_over = client.post(
        "/api/v1/shortlisting",
        json={
            "candidate_reports": [{"candidate_name": "A", "ats_score": 101}]
        }
    )
    assert res_over.status_code == 422

    # ATS score below 0
    res_under = client.post(
        "/api/v1/shortlisting",
        json={
            "candidate_reports": [{"candidate_name": "A", "ats_score": -1}]
        }
    )
    assert res_under.status_code == 422

    # candidate_reports is not a list
    res_malformed = client.post(
        "/api/v1/shortlisting",
        json={
            "candidate_reports": "not-a-list"
        }
    )
    assert res_malformed.status_code == 422
