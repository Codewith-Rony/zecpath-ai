from pathlib import Path
from main_ats_scorer import generate_candidate_report


def test_pipeline_generates_report_for_sample_files():
    root = Path(__file__).resolve().parents[1]
    resume = root / "data" / "sample_resumes" / "sample_resume.pdf"
    jd = root / "data" / "sample_jobs" / "python_developer_jd.txt"
    if not resume.is_file() or not jd.is_file():
        return
    report = generate_candidate_report(resume, jd)
    assert report["resume_file"] == resume.name
    assert report["job_description_file"] == jd.name
    assert set(report["component_scores"]) == {
        "skill_match", "experience_relevance", "education_alignment", "semantic_similarity"
    }
    assert 0 <= report["coverage_percentage"] <= 100
    for score in report["component_scores"].values():
        assert score is None or 0 <= score <= 100
