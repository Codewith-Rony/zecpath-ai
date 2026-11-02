
from datetime import datetime, timezone
from uuid import uuid4


# Temporary in-memory job storage
jobs = {}


def create_job(resume_id: str):
    job_id = str(uuid4())

    jobs[job_id] = {
        "job_id": job_id,
        "resume_id": resume_id,
        "status": "queued",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "result": None,
        "error": None
    }

    return jobs[job_id]


def update_job(job_id: str, status: str, result=None, error=None):
    if job_id not in jobs:
        return None

    jobs[job_id]["status"] = status
    jobs[job_id]["result"] = result
    jobs[job_id]["error"] = error

    return jobs[job_id]


def get_job(job_id: str):
    return jobs.get(job_id)
