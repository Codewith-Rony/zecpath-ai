
import re
from difflib import SequenceMatcher


def normalize_text(text):
    """Normalize text for role comparison."""
    text = (text or "").lower()
    return re.sub(r"[^a-z0-9+#.]+", " ", text).strip()


def tokenize(text):
    """Convert text into a set of meaningful tokens."""
    stop_words = {
        "a", "an", "and", "at", "for", "in", "of",
        "the", "to", "with", "on"
    }
    return {
        word for word in normalize_text(text).split()
        if word not in stop_words
    }


def calculate_similarity(text_a, text_b):
    """Calculate similarity using token overlap and string similarity."""
    tokens_a = tokenize(text_a)
    tokens_b = tokenize(text_b)

    if not tokens_a or not tokens_b:
        return 0.0

    overlap = len(tokens_a & tokens_b) / len(tokens_a | tokens_b)
    sequence = SequenceMatcher(
        None, normalize_text(text_a), normalize_text(text_b)
    ).ratio()

    return round((0.7 * overlap + 0.3 * sequence) * 100, 2)


def score_experience_relevance(entries, target_role, target_requirements=None):
    """
    Score each previous role against the target role and requirements.

    Responsibilities and requirements are compared as text.
    Scores are heuristic similarity indicators, not probabilities.
    """
    target_requirements = target_requirements or []
    results = []

    for entry in entries:
        job_title = entry.get("job_title", "")
        responsibilities = entry.get("responsibilities", "")

        title_score = calculate_similarity(job_title, target_role)

        combined_text = f"{job_title} {responsibilities}"
        requirement_scores = [
            calculate_similarity(combined_text, requirement)
            for requirement in target_requirements
            if requirement.strip()
        ]

        requirements_score = (
            round(sum(requirement_scores) / len(requirement_scores), 2)
            if requirement_scores
            else None
        )

        if requirements_score is None:
            final_score = title_score
        else:
            final_score = round(
                0.6 * title_score + 0.4 * requirements_score, 2
            )

        results.append({
            "company": entry.get("company", "Unknown"),
            "job_title": job_title or "Unknown",
            "target_role": target_role,
            "title_similarity": title_score,
            "requirements_similarity": requirements_score,
            "relevance_score": final_score,
        })

    results.sort(
        key=lambda item: item["relevance_score"],
        reverse=True,
    )

    return {
        "target_role": target_role,
        "role_scores": results,
    }
