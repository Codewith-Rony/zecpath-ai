"""Generate a recruiter-friendly text report for ranked candidates."""


def generate_ranking_report(candidates):
    """Format ranked candidates as a readable text report."""
    lines = [
        "CANDIDATE RANKING REPORT",
        "=" * 60,
        f"Total candidates: {len(candidates)}",
        "",
    ]

    if not candidates:
        lines.append("No candidates available.")
        return "\n".join(lines)

    for candidate in candidates:
        name = (
            candidate.get("candidate_name")
            or candidate.get("resume_file")
            or "Unknown candidate"
        )
        score = candidate.get("ats_score")
        score_text = f"{score:.2f}/100" if score is not None else "N/A"
        rank = candidate.get("rank", "N/A")
        recommendation = candidate.get(
            "recommendation", "not classified"
        ).replace("_", " ").title()

        lines.extend([
            f"Rank: {rank}",
            f"Candidate: {name}",
            f"ATS Score: {score_text}",
            f"Recommendation: {recommendation}",
            "-" * 60,
        ])

    return "\n".join(lines)
    