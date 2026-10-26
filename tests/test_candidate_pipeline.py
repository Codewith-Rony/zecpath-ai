
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

