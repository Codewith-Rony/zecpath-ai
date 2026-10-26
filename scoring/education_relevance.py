
def score_education_relevance(academic_profile, target_role):
    """Score academic profile relevance to a target job role."""
    target = target_role.lower()
    education_scores = []

    relevant_fields = {
        "python developer": ["computer science", "information technology",
                             "software engineering", "computer applications"],
        "data scientist": ["data science", "statistics", "mathematics",
                           "computer science"],
        "web developer": ["computer science", "information technology",
                          "software engineering", "web development"],
        "ai engineer": ["artificial intelligence", "machine learning",
                        "computer science", "data science"],
    }

    fields = relevant_fields.get(target, [])

    for item in academic_profile.get("education", []):
        field = (item.get("field_of_study") or "").lower()
        degree = (item.get("degree") or "").lower()

        score = 0

        if field and any(relevant in field for relevant in fields):
            score += 70

        if any(word in degree for word in ["bachelor", "master", "phd"]):
            score += 30

        education_scores.append({
            "degree": item.get("degree"),
            "field_of_study": item.get("field_of_study"),
            "relevance_score": min(score, 100),
        })

    return {
        "target_role": target_role,
        "education_scores": education_scores,
    }
