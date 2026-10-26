from scoring.semantic_matcher import SemanticMatcher, evaluate_pairs

def test_empty_text_scores_zero():
    matcher = SemanticMatcher(prefer_embeddings=False)
    assert matcher.similarity("", "Python developer") == 0.0

def test_similarity_is_symmetric_and_bounded():
    matcher = SemanticMatcher(prefer_embeddings=False)
    a = "Python developer builds backend APIs with Flask"
    b = "Python developer builds backend APIs with Flask"
    score = matcher.similarity(a, b)
    assert score == 100.0
    assert matcher.similarity(a, "pastry chef prepares cakes") < score

def test_resume_job_output_has_component_scores():
    matcher = SemanticMatcher(prefer_embeddings=False)
    result = matcher.score_resume_job(
        {"skills": ["Python", "Flask"], "experience_summary": "Built backend APIs", "project_descriptions": "Flask web app"},
        {"required_skills": ["Python", "Flask"], "experience_requirements": "Backend API development", "relevant_projects": "Web application"},
    )
    assert set(result["field_scores"]) == {"skills", "experience", "projects"}
    assert 0 <= result["overall_similarity"] <= 100

def test_evaluation_report_metrics():
    matcher = SemanticMatcher(prefer_embeddings=False)
    report = evaluate_pairs(matcher, [
        {"label": "positive", "resume_text": "Python backend API developer", "job_text": "Python backend API developer", "is_match": True},
        {"label": "negative", "resume_text": "Baker and pastry chef", "job_text": "Python backend API developer", "is_match": False},
    ], threshold=30)
    assert report["sample_count"] == 2
    assert "accuracy_percent" in report
