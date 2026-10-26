
"""Rank candidate reports using their existing ATS scores."""


def rank_candidates(candidate_reports):
    """Return candidate reports sorted by ATS score, highest first.

    Candidates without a valid ATS score are placed at the bottom.
    Original order is preserved when scores are equal.
    """
    if not isinstance(candidate_reports, list):
        raise ValueError("candidate_reports must be a list.")

    for candidate in candidate_reports:
        if not isinstance(candidate, dict):
            raise ValueError("Each candidate report must be a dictionary.")

        score = candidate.get("ats_score")
        if score is not None:
            if (
                not isinstance(score, (int, float))
                or isinstance(score, bool)
                or not 0 <= score <= 100
            ):
                raise ValueError(
                    "Candidate ATS scores must be between 0 and 100."
                )

    # Python sorting is stable, so ties retain their original order.
    ranked = sorted(
        candidate_reports,
        key=lambda candidate: (
            candidate.get("ats_score") is None,
            -(candidate.get("ats_score") or 0)
            if candidate.get("ats_score") is not None
            else 0,
        ),
    )

    for position, candidate in enumerate(ranked, start=1):
        candidate["rank"] = position

    return ranked

