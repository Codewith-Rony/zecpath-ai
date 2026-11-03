
def score_education_relevance(academic_profile, target_role):
    """Score academic profile relevance to a target job role."""
    target = target_role.lower().strip()
    education_scores = []

    relevant_fields = {
        "python developer": ["computer science", "information technology",
                             "software engineering", "computer applications", "software systems"],
        "data scientist": ["data science", "statistics", "mathematics",
                           "computer science"],
        "web developer": ["computer science", "information technology",
                          "software engineering", "web development"],
        "ai engineer": ["artificial intelligence", "machine learning",
                        "computer science", "data science"],
        "backend developer": ["computer science", "information technology",
                              "software engineering", "computer applications", "software systems"],
        "software developer": ["computer science", "information technology",
                               "software engineering", "computer applications", "software systems"],
        "software engineer": ["computer science", "information technology",
                              "software engineering", "computer applications", "software systems"],
    }

    hr_fields = [
        "human resources", "human resource", "hr",
        "business administration", "management", "business",
        "psychology", "personnel", "organizational",
        "labor relations", "social work", "commerce",
        "communications", "public administration",
    ]

    if any(term in target for term in ["hr", "human resource", "recruiter", "talent acquisition"]):
        fields = hr_fields
    elif target in relevant_fields:
        fields = relevant_fields[target]
    else:
        # Default fallback: check if any software/engineering keyword matches
        if any(term in target for term in ["developer", "engineer", "software"]):
            fields = relevant_fields["software developer"]
        else:
            fields = []

    for item in academic_profile.get("education", []):
        field = (item.get("field_of_study") or "").lower()
        degree = (item.get("degree") or "").lower()
        combined = f"{degree} {field}".strip()

        score = 0

        if fields and any(relevant in combined for relevant in fields):
            score += 70

        if any(word in degree for word in ["bachelor", "master", "phd", "diploma", "post graduate"]):
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
