
"""CLI for ranking and shortlisting existing Zecpath AI ATS reports."""

import argparse
import json
from pathlib import Path

from scoring.candidate_pipeline import process_candidates


def load_candidate_reports(report_paths):
    """Load existing ATS JSON reports."""
    candidates = []

    for report_path in report_paths:
        path = Path(report_path).expanduser().resolve()

        if not path.is_file():
            raise FileNotFoundError(f"Report not found: {path}")

        try:
            report = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as error:
            raise ValueError(
                f"Invalid JSON report: {path}"
            ) from error

        if not isinstance(report, dict):
            raise ValueError(f"Report must contain a JSON object: {path}")

        if "ats_score" not in report:
            raise ValueError(f"Missing ats_score in report: {path}")

        report.setdefault("resume_file", path.stem)
        candidates.append(report)

    # Avoid comparing reports generated for different job descriptions.
    job_descriptions = {
        candidate.get("job_description_file")
        for candidate in candidates
    }

    if len(candidates) > 1 and len(job_descriptions) > 1:
        raise ValueError(
            "Reports refer to different job descriptions. "
            "Rank candidates for the same job description together."
        )

    return candidates


def main():
    parser = argparse.ArgumentParser(
        description="Rank candidates using existing Zecpath AI ATS reports."
    )
    parser.add_argument(
        "--reports",
        nargs="+",
        required=True,
        help="Paths to one or more existing ATS JSON reports.",
    )
    parser.add_argument(
        "--output-dir",
        default="outputs/candidate_ranking",
        help="Directory for the ranked output files.",
    )
    parser.add_argument(
        "--shortlist-threshold",
        type=float,
        default=70,
        help="Minimum ATS score for a shortlist recommendation.",
    )
    parser.add_argument(
        "--review-threshold",
        type=float,
        default=40,
        help="Minimum ATS score for a review recommendation.",
    )

    args = parser.parse_args()

    try:
        candidates = load_candidate_reports(args.reports)

        result = process_candidates(
            candidates,
            thresholds={
                "shortlist": args.shortlist_threshold,
                "review": args.review_threshold,
            },
        )

    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    output_dir = Path(args.output_dir).expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)

    json_path = output_dir / "ranked_candidates.json"
    text_path = output_dir / "ranking_report.txt"

    json_path.write_text(
        json.dumps(result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    text_path.write_text(result["report"], encoding="utf-8")

    print("\n=== Zecpath AI: Candidate Ranking ===")
    print(f"Candidates processed: {result['total_candidates']}")
    print()

    for candidate in result["candidates"]:
        name = candidate.get("resume_file", "Unknown candidate")
        score = candidate.get("ats_score")
        recommendation = candidate["recommendation"].replace("_", " ")

        score_text = f"{score:.2f}/100" if score is not None else "N/A"

        print(
            f"Rank {candidate['rank']}: {name} | "
            f"Score: {score_text} | "
            f"Recommendation: {recommendation.title()}"
        )

    print(f"\nJSON results saved to: {json_path}")
    print(f"Text report saved to: {text_path}")
    print(
        "\nNote: These are heuristic recommendations, "
        "not final hiring decisions."
    )


if __name__ == "__main__":
    main()
