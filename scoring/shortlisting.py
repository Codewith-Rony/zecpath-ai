
"""Classify ranked candidates using configurable ATS score thresholds."""

DEFAULT_THRESHOLDS = {
    "shortlist": 70,
    "review": 40,
}


def classify_candidate(score, thresholds=None):
    """Return a recommendation based on the candidate's ATS score."""
    selected = thresholds or DEFAULT_THRESHOLDS

    shortlist_threshold = selected["shortlist"]
    review_threshold = selected["review"]

    if shortlist_threshold > 100 or shortlist_threshold < 0:
        raise ValueError("Shortlist threshold must be between 0 and 100.")

    if review_threshold > 100 or review_threshold < 0:
        raise ValueError("Review threshold must be between 0 and 100.")

    if review_threshold > shortlist_threshold:
        raise ValueError(
            "Review threshold cannot exceed shortlist threshold."
        )

    if score is None:
        return "manual_review"

    if (
        not isinstance(score, (int, float))
        or isinstance(score, bool)
        or not 0 <= score <= 100
    ):
        raise ValueError("Score must be between 0 and 100, or None.")

    if score >= shortlist_threshold:
        return "shortlist"

    if score >= review_threshold:
        return "review"

    return "reject_recommendation"


def shortlist_candidates(ranked_candidates, thresholds=None):
    """Add a recommendation to each ranked candidate."""
    results = []

    for candidate in ranked_candidates:
        item = candidate.copy()
        item["recommendation"] = classify_candidate(
            item.get("ats_score"),
            thresholds,
        )
        results.append(item)

    return results

