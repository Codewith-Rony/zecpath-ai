
import json

import pytest

from main_candidate_ranking import load_candidate_reports


def test_load_candidate_report(tmp_path):
    report_path = tmp_path / "candidate.json"
    report_path.write_text(
        json.dumps({
            "resume_file": "resume.pdf",
            "job_description_file": "developer.txt",
            "ats_score": 82,
        }),
        encoding="utf-8",
    )

    candidates = load_candidate_reports([str(report_path)])

    assert len(candidates) == 1
    assert candidates[0]["ats_score"] == 82
    assert candidates[0]["resume_file"] == "resume.pdf"


def test_missing_report_raises_error(tmp_path):
    missing_path = tmp_path / "missing.json"

    with pytest.raises(FileNotFoundError):
        load_candidate_reports([str(missing_path)])


def test_invalid_json_raises_error(tmp_path):
    report_path = tmp_path / "invalid.json"
    report_path.write_text("{invalid json", encoding="utf-8")

    with pytest.raises(ValueError, match="Invalid JSON"):
        load_candidate_reports([str(report_path)])


def test_different_job_descriptions_are_rejected(tmp_path):
    reports = []

    for name, jd in [
        ("candidate_a.json", "python_jd.txt"),
        ("candidate_b.json", "java_jd.txt"),
    ]:
        path = tmp_path / name
        path.write_text(
            json.dumps({
                "resume_file": name,
                "job_description_file": jd,
                "ats_score": 80,
            }),
            encoding="utf-8",
        )
        reports.append(str(path))

    with pytest.raises(ValueError, match="different job descriptions"):
        load_candidate_reports(reports)


def test_report_without_score_is_rejected(tmp_path):
    report_path = tmp_path / "missing_score.json"
    report_path.write_text(
        json.dumps({"resume_file": "resume.pdf"}),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="ats_score"):
        load_candidate_reports([str(report_path)])
