
from fastapi.testclient import TestClient

from api.main import app

client = TestClient(app)


def test_health_check():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_root_endpoint():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


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
