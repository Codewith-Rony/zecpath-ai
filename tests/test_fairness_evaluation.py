
from scoring.skill_matcher import score_skill_match
from scoring.ats_scorer import calculate_ats_score

def test_equivalent_resume_formatting_produces_consistent_scores():
    jd_text = """
    Required Skills:
    Python
    JavaScript
    Machine Learning
    PostgreSQL
    """

    resume_normal = """
    Skills:
    Python, JavaScript, Machine Learning, PostgreSQL

    Experience:
    Developed software applications using these technologies.
    """

    resume_different_format = """
    TECHNICAL SKILLS

    Python

    JavaScript

    Machine Learning

    PostgreSQL


    EXPERIENCE

    Developed software applications using these technologies.
    """

    normal_result = score_skill_match(resume_normal, jd_text)
    formatted_result = score_skill_match(resume_different_format, jd_text)

    assert normal_result["skill_match_score"] == formatted_result["skill_match_score"]


def test_equivalent_skill_aliases_produce_consistent_scores():
    jd_text = """
    Required Skills:
    JavaScript
    Machine Learning
    PostgreSQL
    """

    resume_full_names = """
    Skills: JavaScript, Machine Learning, PostgreSQL
    """

    resume_aliases = """
    Skills: JS, ML, Postgres
    """

    full_names_result = score_skill_match(resume_full_names, jd_text)
    aliases_result = score_skill_match(resume_aliases, jd_text)

    assert full_names_result["skill_match_score"] == aliases_result["skill_match_score"]

def test_combined_formatting_and_alias_variations():
    jd_text = """
    Required Skills:
    Python
    JavaScript
    Machine Learning
    PostgreSQL
    """

    original_resume = """
    Skills: Python, JavaScript, Machine Learning, PostgreSQL
    Experience: Developed software applications.
    """

    varied_resume = """
    TECHNICAL SKILLS

    Python
    JS
    ML
    Postgres

    PROFESSIONAL EXPERIENCE

    Developed software applications.
    """

    original_result = score_skill_match(original_resume, jd_text)
    varied_result = score_skill_match(varied_resume, jd_text)

    assert (
        original_result["skill_match_score"]
        == varied_result["skill_match_score"]
    )


def test_equivalent_resumes_produce_consistent_weighted_ats_scores():
    jd_text = """
    Required Skills:
    Python
    JavaScript
    Machine Learning
    PostgreSQL
    """

    resume_one = """
    Skills: Python, JavaScript, Machine Learning, PostgreSQL
    """

    resume_two = """
    TECHNICAL SKILLS

    Python
    JS
    ML
    Postgres
    """

    result_one = score_skill_match(resume_one, jd_text)
    result_two = score_skill_match(resume_two, jd_text)

    components_one = {
        "skill_match": result_one["skill_match_score"],
        "experience_relevance": 80,
        "education_alignment": 75,
        "semantic_similarity": 85,
    }

    components_two = {
        "skill_match": result_two["skill_match_score"],
        "experience_relevance": 80,
        "education_alignment": 75,
        "semantic_similarity": 85,
    }

    ats_one = calculate_ats_score(
        components_one, role="Software Developer"
    )

    ats_two = calculate_ats_score(
        components_two, role="Software Developer"
    )

    assert ats_one["ats_score"] == ats_two["ats_score"]
    assert ats_one["coverage_percentage"] == ats_two["coverage_percentage"]
