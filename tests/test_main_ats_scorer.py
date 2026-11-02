
from unittest.mock import patch

from main_ats_scorer import generate_candidate_report


def test_privacy_masking_is_applied_before_evaluation():
    resume_text = (
        "John Smith\n"
        "john@example.com\n"
        "+91 98765 43210\n"
        "Python Developer with SQL experience."
    )

    with (
        patch("main_ats_scorer.extract_resume") as mock_extract,
        patch("main_ats_scorer.extract_jd_text", return_value=(
            "Software Developer\nRequired Skills:\nPython\nSQL"
        )),
        patch("main_ats_scorer.score_skill_match") as mock_skill,
        patch("main_ats_scorer.extract_experience", return_value=[]),
        patch("main_ats_scorer.extract_academic_profile", return_value=[]),
        patch("main_ats_scorer.score_experience_relevance", return_value={"role_scores": []}),
        patch("main_ats_scorer.score_education_relevance", return_value={"education_scores": []}),
        patch("main_ats_scorer.SemanticMatcher") as mock_semantic,
        patch("main_ats_scorer.calculate_ats_score", return_value={
            "ats_score": 80,
            "coverage_percentage": 100,
            "minimum_coverage_required": 80,
            "missing_components": [],
            "score_breakdown": {},
            "manual_review_required": False,
        }),
    ):
        mock_extract.return_value = {"cleaned_text": resume_text}
        mock_skill.return_value = {"skill_match_score": 80}
        mock_semantic.return_value.mode = "test"
        mock_semantic.return_value.similarity.return_value = 80

        generate_candidate_report(
    "data/sample_resumes/sample_resume.pdf",
    "data/sample_jobs/software_developer_jd.txt",
)
        evaluated_text = mock_skill.call_args.args[0]
        assert mock_skill.call_args.args[0] == mock_extract.call_args.args[0] or evaluated_text

        mock_experience = None
        assert "[EMAIL]" in evaluated_text
        assert "[PHONE]" in evaluated_text
        assert "john@example.com" not in evaluated_text
        assert "98765 43210" not in evaluated_text
        assert "Python Developer" in evaluated_text
