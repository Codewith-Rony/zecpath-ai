
import pytest

from scoring.candidate_ranker import rank_candidates


def test_candidates_are_sorted_by_score():
    candidates = [
        {"resume_file": "a.pdf", "ats_score": 60},
        {"resume_file": "b.pdf", "ats_score": 90},
        {"resume_file": "c.pdf", "ats_score": 75},
    ]

    ranked = rank_candidates(candidates)

    assert [item["ats_score"] for item in ranked] == [90, 75, 60]
    assert [item["rank"] for item in ranked] == [1, 2, 3]


def test_missing_scores_go_to_bottom():
    candidates = [
        {"resume_file": "a.pdf", "ats_score": None},
        {"resume_file": "b.pdf", "ats_score": 80},
    ]

    ranked = rank_candidates(candidates)

    assert ranked[0]["resume_file"] == "b.pdf"
    assert ranked[1]["resume_file"] == "a.pdf"


def test_ties_preserve_original_order():
    candidates = [
        {"resume_file": "first.pdf", "ats_score": 80},
        {"resume_file": "second.pdf", "ats_score": 80},
    ]

    ranked = rank_candidates(candidates)

    assert [item["resume_file"] for item in ranked] == [
        "first.pdf",
        "second.pdf",
    ]


@pytest.mark.parametrize("score", [-1, 101, "80", True])
def test_invalid_scores_are_rejected(score):
    with pytest.raises(ValueError):
        rank_candidates([{"ats_score": score}])


def test_input_must_be_a_list():
    with pytest.raises(ValueError):
        rank_candidates({"ats_score": 80})
