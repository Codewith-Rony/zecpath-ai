
from scoring.education_relevance import score_education_relevance


def test_relevant_education_for_python_developer():
    profile = {
        "education": [
            {
                "degree": "Bachelor of Technology",
                "field_of_study": "Information Technology",
            }
        ],
        "certifications": [],
    }

    result = score_education_relevance(profile, "Python Developer")

    assert result["target_role"] == "Python Developer"
    assert result["education_scores"][0]["relevance_score"] == 100
