
"""
Run the Day 17 ATS evaluation matrix (12 resumes x 4 job descriptions).

Run from the repository root:
    python scripts/run_day17_evaluation.py

Expected test-data layout:
    data/testing/
        candidate_index.csv
        manual_evaluation_reference.csv
        resumes/...
        job_descriptions/JD01_....txt
        job_descriptions/JD02_....txt
        job_descriptions/JD03_....txt
        job_descriptions/JD04_....txt

Uses FastAPI TestClient. BackgroundTasks execute during
the test request, so a separate Uvicorn server is not required.
"""

import csv
import mimetypes
import sys
from pathlib import Path

from fastapi.testclient import TestClient

# Add repository root to Python path
ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from api.main import app


TESTING_DIR = ROOT / "data" / "testing"
CANDIDATE_INDEX = TESTING_DIR / "candidate_index.csv"
MANUAL_REFERENCE = TESTING_DIR / "manual_evaluation_reference.csv"
RESUME_DIR = TESTING_DIR / "resumes"
JD_DIR = TESTING_DIR / "job_descriptions"
OUTPUT_CSV = TESTING_DIR / "ats_evaluation_results.csv"


def read_csv(path: Path):
    if not path.is_file():
        raise FileNotFoundError(
            f"Required file not found: {path}"
        )

    with path.open(
        "r",
        newline="",
        encoding="utf-8-sig"
    ) as file:
        return list(csv.DictReader(file))


def find_job_description(job_id: str) -> Path:
    matches = sorted(JD_DIR.glob(f"{job_id}_*"))

    if not matches:
        raise FileNotFoundError(
            f"No job description found for {job_id} in {JD_DIR}"
        )

    return matches[0]


def upload_file(client, endpoint, field_name, path):
    mime_type = (
        mimetypes.guess_type(path.name)[0]
        or "application/octet-stream"
    )

    with path.open("rb") as file:
        response = client.post(
            endpoint,
            files={
                field_name: (
                    path.name,
                    file,
                    mime_type
                )
            },
        )

    response.raise_for_status()

    return response.json()


def score_one_pair(client, resume_id, jd_path):
    mime_type = (
        mimetypes.guess_type(jd_path.name)[0]
        or "text/plain"
    )

    with jd_path.open("rb") as jd_file:
        submit_response = client.post(
            "/api/v1/scoring/jobs",
            data={
                "resume_id": resume_id
            },
            files={
                "job_description": (
                    jd_path.name,
                    jd_file,
                    mime_type,
                )
            },
        )

    submit_response.raise_for_status()

    submitted = submit_response.json()
    job_id = submitted["job_id"]

    status_response = client.get(
        f"/api/v1/jobs/{job_id}"
    )

    status_response.raise_for_status()

    job = status_response.json()

    if job.get("status") != "completed":
        raise RuntimeError(
            f"Scoring job {job_id} ended with status "
            f"{job.get('status')}: {job.get('error')}"
        )

    return job.get("result") or {}


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run Day 17 evaluation matrix")
    parser.add_argument("--output", default=str(OUTPUT_CSV), help="Output CSV path")
    args, _ = parser.parse_known_args()
    output_csv = Path(args.output).resolve()

    candidates = read_csv(CANDIDATE_INDEX)
    manual_rows = read_csv(MANUAL_REFERENCE)

    if len(candidates) != 12:
        raise ValueError(
            f"Expected 12 candidate rows, found {len(candidates)}."
        )

    # Validate manual evaluation reference
    manual_lookup = {}

    for row in manual_rows:

        candidate_id = row.get(
            "candidate_id", ""
        ).strip()

        jd_id = row.get(
            "job_description_id", ""
        ).strip()

        decision = row.get(
            "reviewer_decision", ""
        ).strip().lower()

        review_status = row.get(
            "review_status", ""
        ).strip().upper()

        if (
            not candidate_id
            or not jd_id
            or decision not in {
                "suitable",
                "not_suitable",
                "borderline"
            }
        ):
            raise ValueError(
                "Manual reference contains a missing ID "
                f"or invalid reviewer_decision: {row}"
            )

        if review_status and review_status != "CONFIRMED":
            raise ValueError(
                f"Manual review for {candidate_id}/{jd_id} "
                "is not CONFIRMED. Update review_status "
                "after reviewing the label."
            )

        key = (candidate_id, jd_id)

        if key in manual_lookup:
            raise ValueError(
                f"Duplicate manual evaluation row: {key}"
            )

        manual_lookup[key] = decision

    job_ids = [
        "JD01",
        "JD02",
        "JD03",
        "JD04"
    ]

    expected_pairs = {
        (candidate["candidate_id"], jd_id)
        for candidate in candidates
        for jd_id in job_ids
    }

    missing = expected_pairs - set(manual_lookup)

    if missing:
        raise ValueError(
            "Manual reference is missing candidate/JD pairs: "
            + ", ".join(
                f"{c}/{j}"
                for c, j in sorted(missing)
            )
        )

    output_rows = []
    failures = []

    print(
        f"Starting ATS evaluation for "
        f"{len(expected_pairs)} pairs..."
    )

    with TestClient(app) as client:

        for candidate in candidates:

            candidate_id = candidate["candidate_id"]

            relative_resume = candidate["resume_file"]

            resume_path = TESTING_DIR / relative_resume

            if not resume_path.is_file():
                raise FileNotFoundError(
                    f"Resume for {candidate_id} not found: "
                    f"{resume_path}"
                )

            print(
                f"\nUploading {candidate_id}: "
                f"{resume_path.name}"
            )

            uploaded = upload_file(
                client,
                "/api/v1/resumes",
                "file",
                resume_path,
            )

            resume_id = uploaded["resume_id"]

            for jd_id in job_ids:

                jd_path = find_job_description(jd_id)

                print(
                    f"  Scoring {candidate_id} "
                    f"against {jd_id}..."
                )

                try:

                    report = score_one_pair(
                        client,
                        resume_id,
                        jd_path
                    )

                    row = {
                        "candidate_id": candidate_id,

                        "candidate_name": candidate.get(
                            "candidate_name", ""
                        ),

                        "job_description_id": jd_id,

                        "manual_decision": manual_lookup[
                            (candidate_id, jd_id)
                        ],

                        "ats_score": report.get(
                            "ats_score"
                        ),

                        "coverage_percentage": report.get(
                            "coverage_percentage"
                        ),

                        "manual_review_required": report.get(
                            "manual_review_required"
                        ),

                        "minimum_coverage_required": report.get(
                            "minimum_coverage_required"
                        ),

                        "missing_components": "; ".join(
                            report.get("missing_components") or []
                        ),

                        "job_role": report.get(
                            "job_role", ""
                        ),

                        "ats_job_status": "completed",

                        "error": "",
                    }

                    output_rows.append(row)

                    print(
                        f"    score={row['ats_score']}, "
                        f"coverage={row['coverage_percentage']}, "
                        f"manual_review={row['manual_review_required']}"
                    )

                except Exception as error:

                    failures.append({
                        "candidate_id": candidate_id,
                        "job_description_id": jd_id,
                        "error": str(error),
                    })

                    output_rows.append({

                        "candidate_id": candidate_id,

                        "candidate_name": candidate.get(
                            "candidate_name", ""
                        ),

                        "job_description_id": jd_id,

                        "manual_decision": manual_lookup[
                            (candidate_id, jd_id)
                        ],

                        "ats_job_status": "failed",

                        "error": str(error),
                    })

                    print(
                        f"    FAILED: {error}"
                    )

    fieldnames = [
        "candidate_id",
        "candidate_name",
        "job_description_id",
        "manual_decision",
        "ats_score",
        "coverage_percentage",
        "manual_review_required",
        "minimum_coverage_required",
        "missing_components",
        "job_role",
        "ats_job_status",
        "error",
    ]

    TESTING_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    with output_csv.open(
        "w",
        newline="",
        encoding="utf-8-sig"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(output_rows)

    print("\nEvaluation run finished.")

    print(
        f"Rows written: {len(output_rows)}"
    )

    print(
        f"Successful: {len(output_rows) - len(failures)}"
    )

    print(
        f"Failed: {len(failures)}"
    )

    print(
        f"Results: {output_csv}"
    )

    if failures:
        print(
            "\nPlease resolve the failed pairs "
            "before calculating metrics."
        )

        raise SystemExit(1)


if __name__ == "__main__":
    main()
