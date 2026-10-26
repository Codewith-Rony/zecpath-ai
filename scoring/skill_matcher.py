"""Explainable resume-to-job skill matching using existing Zecpath AI parsers."""

from parsers.jd_parser import build_job_profile
from parsers.skill_extractor import extract_skills, load_skill_dictionary


KNOWN_ROLES = [
    "Python Developer", "Python Engineer", "Java Developer", "Java Engineer",
    "Backend Developer", "Backend Engineer", "Frontend Developer",
    "Front End Developer", "Full Stack Developer", "Full-Stack Developer",
    "Software Engineer", "Software Developer", "Data Scientist",
    "Machine Learning Engineer", "DevOps Engineer", "AI Engineer",
]


def _known_skills(dictionary):
    """Return canonical skill names from the shared skill dictionary."""
    skills = []
    for category in ("technical", "business", "creative"):
        skills.extend(dictionary.get(category, {}).keys())
    return list(dict.fromkeys(skills))


def score_skill_match(resume_text, job_description_text):
    """Compare extracted resume skills with skills identified in a job description.

    Required skills account for 80% of the score and preferred skills for 20%.
    If only one category is available, that category is scored on its own.
    If no job skills can be identified, the score is None rather than a fabricated 0.
    """
    if not isinstance(resume_text, str) or not isinstance(job_description_text, str):
        raise ValueError("Resume text and job description text must be strings.")

    dictionary = load_skill_dictionary()
    known_skills = _known_skills(dictionary)

    resume_result = extract_skills(resume_text)
    resume_skills = sorted({item["name"] for item in resume_result["skills"]}, key=str.lower)
    resume_skill_set = {skill.casefold() for skill in resume_skills}

    job_profile = build_job_profile(
        job_description_text,
        known_skills=known_skills,
        known_roles=KNOWN_ROLES,
    )
    required_skills = list(dict.fromkeys(job_profile.get("required_skills", [])))
    preferred_skills = list(dict.fromkeys(job_profile.get("preferred_skills", [])))

    # Some JDs do not use recognizable requirement headings. In that case, use
    # skills found in the full JD as a transparent fallback requirement set.
    extraction_mode = "structured_sections"
    if not required_skills and not preferred_skills:
        required_skills = list(dict.fromkeys(
            item["name"] for item in extract_skills(job_description_text)["skills"]
        ))
        extraction_mode = "full_description_fallback"

    matched_required = [skill for skill in required_skills if skill.casefold() in resume_skill_set]
    missing_required = [skill for skill in required_skills if skill.casefold() not in resume_skill_set]
    matched_preferred = [skill for skill in preferred_skills if skill.casefold() in resume_skill_set]
    missing_preferred = [skill for skill in preferred_skills if skill.casefold() not in resume_skill_set]

    required_coverage = (
        len(matched_required) / len(required_skills) * 100 if required_skills else None
    )
    preferred_coverage = (
        len(matched_preferred) / len(preferred_skills) * 100 if preferred_skills else None
    )

    if required_coverage is None and preferred_coverage is None:
        score = None
    elif required_coverage is not None and preferred_coverage is not None:
        score = 0.8 * required_coverage + 0.2 * preferred_coverage
    elif required_coverage is not None:
        score = required_coverage
    else:
        score = preferred_coverage

    return {
        "skill_match_score": round(score, 2) if score is not None else None,
        "resume_skills": resume_skills,
        "required_skills": required_skills,
        "matched_required_skills": matched_required,
        "missing_required_skills": missing_required,
        "preferred_skills": preferred_skills,
        "matched_preferred_skills": matched_preferred,
        "missing_preferred_skills": missing_preferred,
        "required_coverage": round(required_coverage, 2) if required_coverage is not None else None,
        "preferred_coverage": round(preferred_coverage, 2) if preferred_coverage is not None else None,
        "extraction_mode": extraction_mode,
    }
