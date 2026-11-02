import logging
from pathlib import Path
from uuid import uuid4, UUID
from io import BytesIO
from zipfile import ZipFile, BadZipFile

from fastapi import (
    FastAPI,
    UploadFile,
    File,
    Form,
    HTTPException,
    BackgroundTasks,
    Request,
    status
)

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from api.schemas import ShortlistingRequest
from api.job_manager import create_job, update_job, get_job

from scoring.candidate_pipeline import process_candidates
from utils.logger import logger

app = FastAPI(
    title="Zecpath AI - ATS API",
    description="REST API for resume parsing, candidate scoring, and shortlisting.",
    version="1.0.0"
)

def get_error_code(status_code: int) -> str:
    error_codes = {
        400: "BAD_REQUEST",
        404: "RESOURCE_NOT_FOUND",
        413: "FILE_TOO_LARGE",
        422: "VALIDATION_ERROR",
        500: "INTERNAL_SERVER_ERROR"
    }

    return error_codes.get(status_code, "API_ERROR")


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):

    logger.warning(
        "HTTP error %s on %s: %s",
        exc.status_code,
        request.url.path,
        exc.detail
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": get_error_code(exc.status_code),
                "message": exc.detail
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError
):
    logger.warning(
        "Request validation failed on %s",
        request.url.path
    )

    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Invalid request data."
            }
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):

    logger.exception(
        "Unexpected API error on %s",
        request.url.path
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred."
            }
        }
    )

# Storage configuration
BASE_DIR = Path(__file__).resolve().parent.parent
RESUME_STORAGE = BASE_DIR / "storage" / "resumes"

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

ALLOWED_EXTENSIONS = {".pdf", ".docx"}

JD_STORAGE = BASE_DIR / "storage" / "job_descriptions"

ALLOWED_JD_EXTENSIONS = {".pdf", ".docx", ".txt"}

@app.get("/")
def root():
    return {
        "message": "Welcome to Zecpath AI ATS API",
        "status": "running",
        "version": "1.0.0"
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/api/v1/resumes", status_code=status.HTTP_201_CREATED)
async def upload_resume(file: UploadFile = File(...)):

    # Validate file extension
    original_filename = file.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF and DOCX files are allowed."
        )

    # Read file with a size limit
    contents = await file.read(MAX_FILE_SIZE + 1)
    await file.close()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="File size exceeds the 10 MB limit."
        )

    # Validate actual file format
    if extension == ".pdf":
        if not contents.startswith(b"%PDF-"):
            raise HTTPException(
                status_code=400,
                detail="Invalid PDF file."
            )

    elif extension == ".docx":
        try:
            with ZipFile(BytesIO(contents)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid DOCX file."
                    )
        except BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file."
            )

    # Generate a unique resume ID
    resume_id = str(uuid4())

    # Save using generated filename, not the original filename
    RESUME_STORAGE.mkdir(parents=True, exist_ok=True)

    saved_filename = f"{resume_id}{extension}"
    file_path = RESUME_STORAGE / saved_filename
    
    file_path.write_bytes(contents)
    logger.info(
    "Resume uploaded successfully: %s",
    resume_id
)
    return {
        "message": "Resume uploaded successfully.",
        "resume_id": resume_id,
        "original_filename": original_filename,
        "file_type": extension.lstrip("."),
        "status": "uploaded"
    }



def process_scoring_job(job_id: str, resume_path: Path, jd_path: Path):
    """Run ATS scoring in the background."""

    logger.info("Scoring job %s started", job_id)
    update_job(job_id, "processing")

    try:
        from main_ats_scorer import generate_candidate_report

        report = generate_candidate_report(
            str(resume_path),
            str(jd_path)
        )

        update_job(
            job_id,
            "completed",
            result=report
        )

        logger.info("Scoring job %s completed successfully", job_id)

    except Exception:
        update_job(
            job_id,
            "failed",
            error="Scoring failed. Check the server logs."
        )

        logger.exception("Scoring job %s failed", job_id)

@app.post("/api/v1/scoring/jobs", status_code=status.HTTP_202_ACCEPTED)
async def submit_scoring_job(
    background_tasks: BackgroundTasks,  
    resume_id: str = Form(...),
    job_description: UploadFile = File(...)
):
    # Validate resume ID
    try:
        resume_id = str(UUID(resume_id))
    except ValueError:
        raise HTTPException(
            status_code=400,
            detail="Invalid resume ID."
        )

    # Locate the previously uploaded resume
    resume_path = next(
        (
            RESUME_STORAGE / f"{resume_id}{ext}"
            for ext in {".pdf", ".docx"}
            if (RESUME_STORAGE / f"{resume_id}{ext}").is_file()
        ),
        None
    )

    if resume_path is None:
        raise HTTPException(
            status_code=404,
            detail="Resume not found. Upload the resume first."
        )

    # Validate job description extension
    original_filename = job_description.filename or ""
    extension = Path(original_filename).suffix.lower()

    if extension not in ALLOWED_JD_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail="Only PDF, DOCX and TXT job descriptions are allowed."
        )

    # Read and validate uploaded job description
    contents = await job_description.read(MAX_FILE_SIZE + 1)
    await job_description.close()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail="Job description is empty."
        )

    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Job description exceeds the 10 MB limit."
        )

    if extension == ".pdf" and not contents.startswith(b"%PDF-"):
        raise HTTPException(
            status_code=400,
            detail="Invalid PDF file."
        )

    if extension == ".docx":
        try:
            with ZipFile(BytesIO(contents)) as archive:
                if "word/document.xml" not in archive.namelist():
                    raise HTTPException(
                        status_code=400,
                        detail="Invalid DOCX file."
                    )
        except BadZipFile:
            raise HTTPException(
                status_code=400,
                detail="Invalid DOCX file."
            )

    # Create job and save JD
    job = create_job(resume_id)

    JD_STORAGE.mkdir(parents=True, exist_ok=True)

    jd_path = JD_STORAGE / f"{job['job_id']}{extension}"
    jd_path.write_bytes(contents)

    # Schedule background processing
    background_tasks.add_task(
        process_scoring_job,
        job["job_id"],
        resume_path,
        jd_path
    )
    logger.info(
    "ATS scoring job submitted: %s",
    job["job_id"]
    )
    return {
        "message": "ATS scoring job submitted successfully.",
        "job_id": job["job_id"],
        "resume_id": resume_id,
        "status": "queued"
    }

@app.get("/api/v1/jobs/{job_id}")
def check_job_status(job_id: str):

    job = get_job(job_id)

    if job is None:
        raise HTTPException(
            status_code=404,
            detail="Job not found."
        )

    return job



@app.post("/api/v1/shortlisting")
def shortlist_candidates_api(request: ShortlistingRequest):

    try:
        # Convert Pydantic models into dictionaries
        candidate_reports = [
            candidate.model_dump()
            for candidate in request.candidate_reports
        ]

        thresholds = request.thresholds.model_dump()

        # Reuse the existing candidate pipeline
        result = process_candidates(
            candidate_reports,
            thresholds=thresholds
        )
        logger.info    (
    "Candidate shortlisting completed. Total candidates: %s    ",
    result.get("total_candidates")
)
        return {
            "message": "Candidate shortlisting completed successfully.",
            "status": "completed",
            **result
        }

    except ValueError as error:
        logger.warning("Shortlisting validation failed: %s", error)
        raise HTTPException(
            status_code=422,
            detail=str(error)
        )
