
# Default weights for the ATS scoring components

DEFAULT_WEIGHTS = {
    "skill_match": 40,
    "experience_relevance": 25,
    "education_alignment": 15,
    "semantic_similarity": 20,
}

ROLE_WEIGHTS = {
    "Software Developer": {
        "skill_match": 45,
        "experience_relevance": 25,
        "education_alignment": 10,
        "semantic_similarity": 20,
    },
    "AI Engineer": {
        "skill_match": 35,
        "experience_relevance": 25,
        "education_alignment": 10,
        "semantic_similarity": 30,
    },
}


def validate_component_scores(component_scores):
    for component, score in component_scores.items():
        if score is None:
            continue

        if not isinstance(score, (int, float)) or isinstance(score, bool):
            raise ValueError(
                f"{component} must be a number between 0 and 100."
            )

        if not 0 <= score <= 100:
            raise ValueError(
                f"{component} must be between 0 and 100."
            )


def validate_weights(weights):
    if not weights:
        raise ValueError("Weights cannot be empty.")

    for component, weight in weights.items():
        if not isinstance(weight, (int, float)) or isinstance(weight, bool):
            raise ValueError(f"Weight for {component} must be numeric.")

        if weight < 0:
            raise ValueError(f"Weight for {component} cannot be negative.")

    if not all(isinstance(weight, (int, float)) and not isinstance(weight, bool) for weight in weights.values()):
        raise ValueError("All weights must be numeric.")

    if sum(weights.values()) != 100:
        raise ValueError("Weights must total 100.")

def calculate_ats_score(component_scores, role=None, weights=None):
    validate_component_scores(component_scores)
    if weights is not None:
        selected_weights = weights
    elif role in ROLE_WEIGHTS:
        selected_weights = ROLE_WEIGHTS[role]
    else:
        selected_weights = DEFAULT_WEIGHTS
    validate_weights(selected_weights)
    total_weight = sum(selected_weights.values())
    weighted_total = 0
    available_weight = 0
    missing_components = []
    breakdown = {}

    for component, weight in selected_weights.items():
        score = component_scores.get(component)

        if score is None:
            missing_components.append(component)
            breakdown[component] = {
                "score": None,
                "weight": weight,
                "weighted_contribution": None,
                "status": "missing",
            }
            continue

        contribution = score * weight
        weighted_total += contribution
        available_weight += weight

        breakdown[component] = {
            "score": score,
            "weight": weight,
            "weighted_contribution": round(contribution / 100, 2),
            "status": "available",
        }

    if available_weight == 0:
        ats_score = None
    else:
        ats_score = round(weighted_total / available_weight, 2)

    coverage = (
        round((available_weight / total_weight) * 100, 2)
        if total_weight > 0 else 0
    )

    return {
        "ats_score": ats_score,
        "missing_components": missing_components,
        "coverage_percentage": coverage,
        "score_breakdown": breakdown,
    }
