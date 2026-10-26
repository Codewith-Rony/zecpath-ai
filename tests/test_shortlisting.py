
import pytest

from scoring.shortlisting import (
    classify_candidate,
    shortlist_candidates,
)


def test_shortlist_zone():
    assert classify_candidate(85) == "shortlist"
    assert classify_candidate(70) == "shortlist"


def test_review_zone():
    assert classify_candidate(55) == "review"
    assert classify_candidate(40) == "review"


def test_reject_recommendation_zone():
    assert classify_candidate(39.99) == "reject_recommendation"
    assert classify_candidate(0) == "reject_recommendation"


def test_missing_score_needs_manual_review():
    assert classify_candidate(None) == "manual_review"


def test_custom_thresholds():
    thresholds = {"shortlist": 80, "review": 50}
    assert classify_candidate(80, thresholds) == "shortlist"
    assert classify_candidate(65, thresholds) == "review"
    assert classify_candidate(30, thresholds) == "reject_recommendation"


def test_invalid_score_is_rejected():
    with pytest.raises(ValueError):
        classify_candidate(101)


def test_invalid_threshold_order_is_rejected():
    with pytest.raises(ValueError):
        classify_candidate(
            60, {"shortlist": 50, "review": 70}
        )


def test_shortlisting_does_not_modify_original():
    candidates = [{"rank": 1, "ats_score": 90}]
    results = shortlist_candidates(candidates)

    assert "recommendation" not in candidates[0]
    assert results[0]["recommendation"] == "shortlist"

