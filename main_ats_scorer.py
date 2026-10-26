"""Interactive CLI that connects existing Zecpath AI parsers and scorers."""
import argparse
import json
from pathlib import Path

from parsers.resume_extractor import extract_resume
from parsers.jd_extractor import extract_jd_text
from parsers.jd_parser import build_job_profile
from parsers.experience_parser import extract_experience
from parsers.education_parser import extract_academic_profile
from parsers.skill_extractor import load_skill_dictionary
from scoring.skill_matcher import score_skill_match, KNOWN_ROLES
from scoring.experience_relevance import score_experience_relevance
from scoring.education_relevance import score_education_relevance
from scoring.semantic_matcher import SemanticMatcher
from scoring.ats_scorer import calculate_ats_score


def _known_skills():
    dictionary = load_skill_dictionary()
    skills = []
    for category in ("technical", "business", "creative"):
        skills.extend(dictionary.get(category, {}).keys())
    return list(dict.fromkeys(skills))


def _mean_or_none(values):
    valid = [value for value in values if isinstance(value, (int, float)) and not isinstance(value, bool)]
    return round(sum(valid) / len(valid), 2) if valid else None


def _education_role(role):
    """Map common software job titles to education scorer's supported categories."""
    normalized = (role or "").strip().casefold()
    if normalized in {"software developer", "software engineer", "backend developer", "backend engineer", "frontend developer", "front end developer", "full stack developer", "full-stack developer", "java developer", "java engineer"}:
        return "web developer"
    if normalized in {"python engineer", "backend python developer"}:
        return "python developer"
    return normalized


def generate_candidate_report(resume_path, jd_path, role_override=None):
    """Read input files and return an explainable candidate scoring report."""
    resume_path = Path(resume_path).expanduser().resolve()
    jd_path = Path(jd_path).expanduser().resolve()
    if not resume_path.is_file():
        raise FileNotFoundError(f"Resume not found: {resume_path}")
    if not jd_path.is_file():
        raise FileNotFoundError(f"Job description not found: {jd_path}")

    resume_data = extract_resume(str(resume_path))
    resume_text = resume_data.get("cleaned_text", "")
    jd_text = extract_jd_text(str(jd_path))
    if not resume_text or not resume_text.strip():
        raise ValueError("No readable text found in the resume.")
    if not jd_text or not jd_text.strip():
        raise ValueError("No readable text found in the job description.")

    job_profile = build_job_profile(jd_text, _known_skills(), KNOWN_ROLES)
    role = role_override or job_profile.get("title") or "Software Developer"

    # 1) Skill match: actual resume and JD text.
    skill_result = score_skill_match(resume_text, jd_text)
    skill_score = skill_result.get("skill_match_score")

    # 2) Experience relevance: average scores across parsed work entries.
    experience_entries = extract_experience(resume_text)
    requirements = list(job_profile.get("responsibilities") or [])
    experience_requirement = job_profile.get("experience_requirement")
    if isinstance(experience_requirement, str) and experience_requirement.strip():
        requirements.append(experience_requirement.strip())
    experience_result = score_experience_relevance(experience_entries, role, requirements)
    experience_score = _mean_or_none([
        item.get("relevance_score") for item in experience_result.get("role_scores", [])
    ])

    # 3) Education alignment: average scores for extracted education entries.
    academic_profile = extract_academic_profile(resume_text)
    education_result = score_education_relevance(academic_profile, _education_role(role))
    education_score = _mean_or_none([
        item.get("relevance_score") for item in education_result.get("education_scores", [])
    ])

    # 4) Semantic similarity: compare the complete resume and JD texts.
    semantic_matcher = SemanticMatcher()
    semantic_score = semantic_matcher.similarity(resume_text, jd_text)
    if not resume_text.strip() or not jd_text.strip():
        semantic_score = None

    component_scores = {
        "skill_match": skill_score,
        "experience_relevance": experience_score,
        "education_alignment": education_score,
        "semantic_similarity": semantic_score,
    }
    ats_result = calculate_ats_score(component_scores, role=role)
    return {
        "resume_file": resume_path.name,
        "job_description_file": jd_path.name,
        "job_role": role,
        "ats_score": ats_result["ats_score"],
        "coverage_percentage": ats_result["coverage_percentage"],
        "missing_components": ats_result["missing_components"],
        "component_scores": component_scores,
        "score_breakdown": ats_result["score_breakdown"],
        "skill_analysis": skill_result,
        "experience_analysis": experience_result,
        "experience_entries_found": len(experience_entries),
        "education_analysis": education_result,
        "semantic_analysis": {
            "similarity": semantic_score,
            "mode": semantic_matcher.mode,
            "interpretation": "Similarity indicator, not probability or hiring decision.",
        },
        "scoring_note": "This is a heuristic decision-support score. Missing components are excluded and available weights are renormalized; coverage should be considered when comparing candidates.",
    }


def main():
    parser = argparse.ArgumentParser(description="Generate an explainable Zecpath AI ATS score from a resume and job description.")
    parser.add_argument("--resume", required=True, help="Resume PDF/DOCX path")
    parser.add_argument("--job-description", required=True, help="Job description TXT/PDF/DOCX path")
    parser.add_argument("--role", help="Optional job role override; otherwise inferred from the JD")
    args = parser.parse_args()
    try:
        report = generate_candidate_report(args.resume, args.job_description, args.role)
    except (FileNotFoundError, ValueError) as error:
        parser.error(str(error))

    output_dir = Path(__file__).resolve().parent / "outputs" / "ats_scoring"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{Path(args.resume).stem}_vs_{Path(args.job_description).stem}_ats_report.json"
    output_path.write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")

    print("=== Zecpath AI: ATS Candidate Score Report ===")
    print(f"Resume: {report['resume_file']}")
    print(f"Job Description: {report['job_description_file']}")
    print(f"Job Role: {report['job_role']}")
    score = report['ats_score']
    print(f"ATS Score: {score}/100" if score is not None else "ATS Score: unavailable (no components could be scored)")
    print(f"Data Coverage: {report['coverage_percentage']}%")
    print("\nComponent Breakdown:")
    for component, details in report["score_breakdown"].items():
        print(f"\n{component.replace('_', ' ').title()}")
        print(f"  Score: {details['score']}")
        print(f"  Weight: {details['weight']}%")
        print(f"  Contribution: {details['weighted_contribution']}")
        print(f"  Status: {details['status']}")
    if report["missing_components"]:
        print("\nMissing components: " + ", ".join(report["missing_components"]))
    print(f"\nSemantic mode: {report['semantic_analysis']['mode']}")
    print(f"Report saved to: {output_path}")
    print("Note: This is a heuristic similarity score, not a probability or hiring decision.")


if __name__ == "__main__":
    main()
