from scoring.ranking_report import generate_ranking_report


def test_report_contains_candidate_details():
    candidates = [
        {
            "rank": 1,
            "candidate_name": "Alex",
            "ats_score": 85.5,
            "recommendation": "shortlist",
        }
    ]

    report = generate_ranking_report(candidates)

    assert "CANDIDATE RANKING REPORT" in report
    assert "Alex" in report
    assert "85.50/100" in report
    assert "Shortlist" in report


def test_report_uses_resume_filename_if_name_missing():
    candidates = [
        {
            "rank": 1,
            "resume_file": "resume.pdf",
            "ats_score": 65,
            "recommendation": "review",
        }
    ]

    report = generate_ranking_report(candidates)

    assert "resume.pdf" in report
    assert "Review" in report


def test_report_handles_missing_score():
    candidates = [
        {
            "rank": 1,
            "candidate_name": "Sam",
            "ats_score": None,
            "recommendation": "manual_review",
        }
    ]

    report = generate_ranking_report(candidates)

    assert "N/A" in report
    assert "Manual Review" in report


def test_report_handles_empty_candidate_list():
    report = generate_ranking_report([])

    assert "Total candidates: 0" in report
    assert "No candidates available." in report
    