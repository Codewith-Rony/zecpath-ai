
import pytest

from scoring.ats_scorer import (
    calculate_ats_score,
    DEFAULT_WEIGHTS,
    ROLE_WEIGHTS,
)


def test_default_scoring():
    scores = {
        "skill_match": 80,
        "experience_relevance": 70,
        "education_alignment": 90,
        "semantic_similarity": 75,
    }

    result = calculate_ats_score(scores)

    assert result["ats_score"] == 78.0
    assert result["coverage_percentage"] == 100.0


def test_role_specific_weights():
    scores = {
        "skill_match": 80,
        "experience_relevance": 70,
        "education_alignment": 90,
        "semantic_similarity": 75,
    }

    result = calculate_ats_score(scores, role="Software Developer")

    assert result["ats_score"] == 77.5


def test_missing_component():
    scores = {
        "skill_match": 80,
        "experience_relevance": 70,
        "education_alignment": None,
        "semantic_similarity": 75,
    }

    result = calculate_ats_score(scores)

    assert result["missing_components"] == ["education_alignment"]
    assert result["coverage_percentage"] == 85.0
    assert result["ats_score"] == 75.88


def test_invalid_component_score():
    with pytest.raises(ValueError):
        calculate_ats_score({
            "skill_match": 120,
        })


def test_weight_totals():
    assert sum(DEFAULT_WEIGHTS.values()) == 100

    for weights in ROLE_WEIGHTS.values():
        assert sum(weights.values()) == 100
