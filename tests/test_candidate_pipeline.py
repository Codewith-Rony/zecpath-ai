
from scoring.candidate_pipeline import process_candidates


def test_pipeline_ranks_and_classifies_candidates():
    candidates = [
        {"candidate_name": "Alex", "ats_score": 55},
        {"candidate_name": "Sam", "ats_score": 85},
        {"candidate_name": "Jordan", "ats_score": 30},
    ]

    result = process_candidates(candidates)

    ranked = result["candidates"]

    assert result["total_candidates"] == 3
    assert ranked[0]["candidate_name"] == "Sam"
    assert ranked[0]["rank"] == 1
    assert ranked[0]["recommendation"] == "shortlist"

    assert ranked[1]["candidate_name"] == "Alex"
    assert ranked[1]["recommendation"] == "review"

    assert ranked[2]["candidate_name"] == "Jordan"
    assert ranked[2]["recommendation"] == "reject_recommendation"

    assert "CANDIDATE RANKING REPORT" in result["report"]


def test_pipeline_handles_empty_input():
    result = process_candidates([])

    assert result["total_candidates"] == 0
    assert result["candidates"] == []
    assert "No candidates available." in result["report"]


import json

from main_candidate_ranking import main


def test_cli_ranks_multiple_candidates_for_same_job(
    tmp_path, monkeypatch
):
    reports_dir = tmp_path / "reports"
    reports_dir.mkdir()

    reports = [
        {
            "resume_file": "candidate_a.pdf",
            "job_description_file": "python_developer_jd.txt",
            "ats_score": 45,
        },
        {
            "resume_file": "candidate_b.pdf",
            "job_description_file": "python_developer_jd.txt",
            "ats_score": 85,
        },
    ]

    report_paths = []

    for index, report in enumerate(reports):
        path = reports_dir / f"candidate_{index}.json"
        path.write_text(
            json.dumps(report),
            encoding="utf-8",
        )
        report_paths.append(str(path))

    output_dir = tmp_path / "ranking_output"

    monkeypatch.setattr(
        "sys.argv",
        [
            "main_candidate_ranking.py",
            "--reports",
            *report_paths,
            "--output-dir",
            str(output_dir),
        ],
    )

    main()

    result = json.loads(
        (output_dir / "ranked_candidates.json").read_text(
            encoding="utf-8"
        )
    )

    assert result["total_candidates"] == 2
    assert result["candidates"][0]["resume_file"] == "candidate_b.pdf"
    assert result["candidates"][0]["rank"] == 1
    assert result["candidates"][0]["recommendation"] == "shortlist"
    assert result["candidates"][1]["resume_file"] == "candidate_a.pdf"
    assert result["candidates"][1]["recommendation"] == "review"

    assert (output_dir / "ranking_report.txt").is_file()
