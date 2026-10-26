from scoring.skill_matcher import score_skill_match


def test_skill_matcher_scores_required_and_preferred_skills():
    resume = "I have experience with Python, PostgreSQL and Docker."
    jd = """
    Python Developer
    Required Skills:
    Python
    PostgreSQL
    MySQL

    Preferred Skills:
    Docker
    AWS
    """

    result = score_skill_match(resume, jd)

    assert result["skill_match_score"] == 63.33
    assert result["matched_required_skills"] == ["Python", "PostgreSQL"]
    assert result["missing_required_skills"] == ["MySQL"]
    assert result["matched_preferred_skills"] == ["Docker"]
    assert result["missing_preferred_skills"] == ["AWS"]


def test_skill_matcher_returns_none_when_no_jd_skills_are_detected():
    result = score_skill_match("General candidate profile", "A role with no listed skills.")
    assert result["skill_match_score"] is None


def test_skill_matcher_uses_full_description_fallback():
    result = score_skill_match(
        "Python and JavaScript developer",
        "We use Python and JavaScript to build our product.",
    )
    assert result["extraction_mode"] == "full_description_fallback"
    assert result["skill_match_score"] == 100.0
