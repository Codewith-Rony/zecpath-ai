import re
import unicodedata
from pathlib import Path
from utils.file_handler import save_json

def normalize_jd_text(text):
    """
    Normalize raw job description text.
    """

    # Normalize Unicode characters
    text = unicodedata.normalize("NFKC", text)

    # Normalize common bullet characters
    text = text.replace("•", "-")
    text = text.replace("●", "-")
    text = text.replace("▪", "-")

    # Normalize line endings
    text = text.replace("\r\n", "\n")
    text = text.replace("\r", "\n")

    # Remove excessive spaces
    text = re.sub(r"[ \t]+", " ", text)

    # Remove excessive blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()
SECTION_ALIASES = {
    "requirements": "requirements",
    "requirements & qualifications": "requirements",
    "qualifications": "requirements",
    "what we're looking for": "requirements",
    "what we are looking for": "requirements",
    "must have": "required",
    "required skills": "required",
    "required qualifications": "required",
    "preferred skills": "preferred",
    "preferred qualifications": "preferred",
    "nice to have": "preferred",
    "responsibilities": "responsibilities",
    "key responsibilities": "responsibilities",
    "your responsibilities": "responsibilities",
    "duties": "responsibilities",
    "what you'll build": "responsibilities",
    "what you will build": "responsibilities",
    "education": "education",
    "educational qualifications": "education",
    "experience": "experience",
    "your first 60 days": "milestones",
    "the strongest application": "application",
    "engineering perks": "benefits",
    "about our products": "about",
}

def detect_sections(text):
    """
    Split a job description into logical sections.
    """

    sections = {}
    current_section = "general"

    sections[current_section] = []

    for line in text.splitlines():
        line = line.strip()

        if not line:
            continue

        heading = line.rstrip(":").strip().lower()
        heading = heading.replace("’", "'")
        heading = heading.replace("–", "-")
        heading = heading.replace("—", "-")

        if heading in SECTION_ALIASES:
            current_section = SECTION_ALIASES[heading]
            sections.setdefault(current_section, [])
        else:
            sections.setdefault(current_section, [])
            sections[current_section].append(line)

    return {
        section: "\n".join(lines)
        for section, lines in sections.items()
    }


SKILL_SYNONYMS = {
    "js": "JavaScript",
    "javascript": "JavaScript",

    "react": "React",
    "reactjs": "React",
    "react.js": "React",

    "nodejs": "Node.js",
    "node.js": "Node.js",

    "postgres": "PostgreSQL",
    "postgresql": "PostgreSQL",

    "rest api": "REST API",
    "rest apis": "REST API",

    "django rest framework": "Django REST Framework",
    "drf": "Django REST Framework",
}


def normalize_skill(skill):
    """
    Convert a skill variation into a standard skill name.
    """

    key = skill.lower().strip()

    return SKILL_SYNONYMS.get(key, skill.strip())


def extract_skills(text, known_skills):
    text_lower = text.lower()
    extracted_skills = []

    for skill in known_skills:
        skill_lower = skill.lower()

        possible_matches = [skill_lower]

        for variation, normalized in SKILL_SYNONYMS.items():
            if normalized.lower() == skill_lower:
                possible_matches.append(variation)

        for match in possible_matches:
            pattern = r"\b" + re.escape(match) + r"\b"

            if re.search(pattern, text_lower):
                normalized = normalize_skill(skill)

                if normalized not in extracted_skills:
                    extracted_skills.append(normalized)

                break

    return extracted_skills
def extract_skills_from_section(section_text, known_skills):
    """
    Extract normalized skills from a specific JD section.
    """
    if not section_text:
        return []

    return extract_skills(section_text, known_skills)

ROLE_VARIATIONS = {
    "python developer": "Python Developer",
    "python engineer": "Python Developer",
    "backend developer": "Backend Developer",
    "backend engineer": "Backend Developer",
    "software engineer": "Software Engineer",
    "software developer": "Software Developer",
    "frontend developer": "Frontend Developer",
    "front end developer": "Frontend Developer",
    "full stack developer": "Full Stack Developer",
    "full-stack developer": "Full Stack Developer",
    "data scientist": "Data Scientist",
    "machine learning engineer": "Machine Learning Engineer",
}


def extract_role(text, known_roles):
    """
    Detect a job role from JD text and normalize common variations.
    """

    text_lower = text.lower()

    for role in known_roles:
        if role.lower() in text_lower:
            return ROLE_VARIATIONS.get(
                role.lower(),
                role
            )

    return None

def extract_experience(text):
    """
    Extract minimum and maximum years of experience
    from a job description.
    """

    text_lower = text.lower()

    # Fresh graduate / fresher
    if "fresh graduate" in text_lower or "fresh graduates" in text_lower:
        match = re.search(
            r"up\s+to\s+(\d+)\s*years?",
            text_lower
        )
        if match:
            return {
                "minimum_years": 0,
                "maximum_years": int(match.group(1))
            }
        return {
            "minimum_years": 0,
            "maximum_years": 0
        }

    if "fresher" in text_lower or "freshers" in text_lower:
        return {
            "minimum_years": 0,
            "maximum_years": 0
        }

    # Pattern: 2+ years
    match = re.search(
        r"(\d+)\s*\+\s*years?",
        text_lower
    )

    if match:
        return {
            "minimum_years": int(match.group(1)),
            "maximum_years": None
        }

    # Pattern: 2-4 years / 2 to 4 years
    match = re.search(
        r"(\d+)\s*(?:-|to)\s*(\d+)\s*years?",
        text_lower
    )

    if match:
        return {
            "minimum_years": int(match.group(1)),
            "maximum_years": int(match.group(2))
        }

    # Pattern: up to 2 years
    match = re.search(
        r"up\s+to\s+(\d+)\s*years?",
        text_lower
    )

    if match:
        return {
            "minimum_years": 0,
            "maximum_years": int(match.group(1))
        }

    # Pattern: minimum 2 years
    match = re.search(
        r"(?:minimum|min\.?)\s*(?:of\s*)?(\d+)\s*years?",
        text_lower
    )

    if match:
        return {
            "minimum_years": int(match.group(1)),
            "maximum_years": None
        }

    return {
        "minimum_years": None,
        "maximum_years": None
    }
EDUCATION_VARIATIONS = {
    "bachelor's degree": "Bachelor's Degree",
    "bachelor degree": "Bachelor's Degree",
    "b.tech": "B.Tech",
    "btech": "B.Tech",
    "b.e": "B.E.",
    "be": "B.E.",
    "master's degree": "Master's Degree",
    "master degree": "Master's Degree",
    "m.tech": "M.Tech",
    "mtech": "M.Tech",
    "mca": "MCA",
    "mba": "MBA",
    "computer science": "Computer Science"
}


def extract_education(text):
    """
    Extract education requirements from relevant JD sections.
    """

    sections = detect_sections(text)

    education_text = ""

    if "education" in sections:
        education_text += sections["education"] + "\n"

    if "requirements" in sections:
        education_text += sections["requirements"] + "\n"

    if not education_text:
        education_text = text

    text_lower = education_text.lower()

    education_requirements = []

    for education, normalized in EDUCATION_VARIATIONS.items():
        if education in {"be", "b.e"}:
            pattern = r"(?<![a-z])" + re.escape(education) + r"(?![a-z])"
        else:
            pattern = r"\b" + re.escape(education) + r"\b"

        if re.search(pattern, text_lower):
            if normalized not in education_requirements:
                education_requirements.append(normalized)

    return education_requirements
def extract_skill_requirements(text, known_skills):
    """
    Extract required and preferred skills using detected JD sections.
    """

    sections = detect_sections(text)

    required_skills = []
    preferred_skills = []

    required_text = ""

    if "required" in sections:
        required_text += sections["required"] + "\n"

    if "requirements" in sections:
        required_text += sections["requirements"] + "\n"

    preferred_text = sections.get("preferred", "")

    required_skills = extract_skills_from_section(
        required_text,
        known_skills
    )

    preferred_skills = extract_skills_from_section(
        preferred_text,
        known_skills
    )

    return {
        "required_skills": required_skills,
        "preferred_skills": preferred_skills
    }
def build_job_profile(
    text,
    known_skills,
    known_roles,
    job_id="JOB-001"
):
    """
    Convert a raw job description into a structured job profile.
    """

    normalized_text = normalize_jd_text(text)

    role = extract_role(normalized_text, known_roles)
    experience = extract_experience(normalized_text)
    education = extract_education(normalized_text)
    skill_requirements = extract_skill_requirements(
        normalized_text,
        known_skills
    )
    optional_skills = extract_optional_skills(
    normalized_text,
    known_skills
    )
    responsibilities = extract_responsibilities(normalized_text)
    employment = extract_employment(normalized_text)
    return {
        "job_id": job_id,
        "title": role,
        "description": normalized_text,
        "experience_requirement": experience,
        "required_skills": skill_requirements["required_skills"],
        "preferred_skills": list(
            dict.fromkeys(
                skill_requirements["preferred_skills"] + optional_skills
            )
        ),
        "education_requirements": education,
        "responsibilities": responsibilities,
        "qualifications": [],
        "certifications": [],
        "employment": employment
    }
       

def save_job_profile(profile, output_path):
    """
    Save a structured job profile as a JSON file.
    """
    save_json(profile, Path(output_path))
def extract_responsibilities(text):
    """
    Extract responsibilities from responsibility-related JD sections.
    """

    sections = detect_sections(text)

    responsibilities = []

    responsibility_text = sections.get("responsibilities", "")

    for line in responsibility_text.splitlines():
        line = line.strip()
        line = re.sub(r"^[-•●▪]\s*", "", line)

        if line:
            responsibilities.append(line)

    return responsibilities
EMPLOYMENT_TYPES = {
    "full-time": "full-time",
    "full time": "full-time",
    "part-time": "part-time",
    "part time": "part-time",
    "contract": "contract",
    "internship": "internship",
}

WORK_MODES = {
    "remote": "remote",
    "work from home": "remote",
    "wfh": "remote",
    "hybrid": "hybrid",
    "work from office": "work from office",
    "on-site": "work from office",
    "onsite": "work from office",
}

LOCATION_VARIATIONS = {
    "bengaluru": "Bengaluru",
    "bangalore": "Bengaluru",
    "mumbai": "Mumbai",
    "delhi": "Delhi",
    "new delhi": "New Delhi",
    "hyderabad": "Hyderabad",
    "pune": "Pune",
    "chennai": "Chennai",
    "kochi": "Kochi",
    "kottayam": "Kottayam",
}

def extract_employment(text):
    """
    Extract employment type, work mode, and location.
    """

    text_lower = text.lower()

    employment_type = None
    work_mode = None
    city = None

    for value, normalized in EMPLOYMENT_TYPES.items():
        if re.search(r"\b" + re.escape(value) + r"\b", text_lower):
            employment_type = normalized
            break

    for value, normalized in WORK_MODES.items():
        if re.search(r"\b" + re.escape(value) + r"\b", text_lower):
            work_mode = normalized
            break

    for value, normalized in LOCATION_VARIATIONS.items():
        if re.search(r"\b" + re.escape(value) + r"\b", text_lower):
            city = normalized
            break

    return {
        "type": employment_type,
        "work_mode": work_mode,
        "location": {
            "city": city,
            "country": "India" if city else None
        }
    }

OPTIONAL_INDICATORS = [
    "optional",
    "preferred",
    "nice to have",
    "good to have",
    "bonus",
    "plus"
]

def extract_optional_skills(text, known_skills):
    """
    Extract skills that are explicitly described as optional or preferred.
    """

    text_lower = text.lower()
    optional_skills = []

    for skill in known_skills:
        skill_lower = skill.lower()

        possible_matches = [skill_lower]

        for variation, normalized in SKILL_SYNONYMS.items():
            if normalized.lower() == skill_lower:
                possible_matches.append(variation)

        for skill_match in possible_matches:
            escaped_skill = re.escape(skill_match)

            # Skill followed by optional/preferred indicator
            after_pattern = (
                rf"\b{escaped_skill}\b"
                rf".{{0,40}}"
                rf"\b(?:optional|preferred|bonus|plus)\b"
            )

            # Optional/preferred indicator followed by skill
            before_pattern = (
                rf"\b(?:optional|preferred|bonus|plus)\b"
                rf".{{0,40}}"
                rf"\b{escaped_skill}\b"
            )

            if (
                re.search(after_pattern, text_lower)
                or re.search(before_pattern, text_lower)
            ):
                normalized = normalize_skill(skill)

                if normalized not in optional_skills:
                    optional_skills.append(normalized)

                break

    return optional_skills
    """
    Extract skills that are explicitly described as optional or preferred.
    """

    text_lower = text.lower()
    optional_skills = []

    for indicator in OPTIONAL_INDICATORS:
        pattern = rf"{re.escape(indicator)}[^.\n]*"

        matches = re.findall(pattern, text_lower)

        for match in matches:
            for skill in known_skills:
                skill_lower = skill.lower()

                possible_matches = [skill_lower]

                for variation, normalized in SKILL_SYNONYMS.items():
                    if normalized.lower() == skill_lower:
                        possible_matches.append(variation)

                for skill_match in possible_matches:
                    skill_pattern = r"\b" + re.escape(skill_match) + r"\b"

                    if re.search(skill_pattern, match):
                        normalized = normalize_skill(skill)

                        if normalized not in optional_skills:
                            optional_skills.append(normalized)

                        break

    return optional_skills