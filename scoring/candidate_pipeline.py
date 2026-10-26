
"""Combine candidate ranking, shortlisting, and report generation."""

from scoring.candidate_ranker import rank_candidates
from scoring.shortlisting import shortlist_candidates
from scoring.ranking_report import generate_ranking_report


def process_candidates(candidate_reports, thresholds=None):
    """Rank candidates, classify them, and generate a readable report."""
    ranked_candidates = rank_candidates(candidate_reports)

    classified_candidates = shortlist_candidates(
        ranked_candidates,
        thresholds,
    )

    report = generate_ranking_report(classified_candidates)

    return {
        "total_candidates": len(classified_candidates),
        "candidates": classified_candidates,
        "report": report,
    }
