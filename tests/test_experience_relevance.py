
from scoring.experience_relevance import (
    calculate_similarity,
    score_experience_relevance,
)


def test_identical_roles_have_high_similarity():
    score = calculate_similarity(
        "Python Developer", "Python Developer"
    )
    assert score >= 90


def test_unrelated_roles_have_lower_similarity():
    related = calculate_similarity(
        "Python Developer", "Python Software Developer"
    )
    unrelated = calculate_similarity(
        "Graphic Designer", "Python Developer"
    )
    assert related > unrelated


def test_relevance_scoring_returns_sorted_roles():
    entries = [
        {
            "company": "Design Co",
            "job_title": "Graphic Designer",
            "responsibilities": "Created visual designs",
        },
        {
            "company": "Tech Co",
            "job_title": "Python Developer",
            "responsibilities": "Built Python APIs and backend services",
        },
    ]

    result = score_experience_relevance(
        entries,
        "Python Developer",
        ["Python backend development", "REST APIs"],
    )

    scores = result["role_scores"]
    assert len(scores) == 2
    assert scores[0]["company"] == "Tech Co"
    assert scores[0]["relevance_score"] >= scores[1]["relevance_score"]


def test_empty_entries_return_empty_scores():
    result = score_experience_relevance([], "Python Developer")
    assert result["role_scores"] == []
