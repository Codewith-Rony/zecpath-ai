from parsers.jd_parser import extract_optional_skills
from parsers.jd_parser import normalize_jd_text
from parsers.jd_parser import extract_skills
from parsers.jd_parser import extract_role
from parsers.jd_parser import extract_experience
from parsers.jd_parser import extract_education
from parsers.jd_parser import build_job_profile
import json
from parsers.jd_parser import save_job_profile
def test_jd_text_normalization():
    raw_text = """
    REQUIRED SKILLS:

    • Python
    • Django

    Experience:    2+ years
    """

    cleaned_text = normalize_jd_text(raw_text)

    print("\n========== NORMALIZED JD ==========")
    print(cleaned_text)
    print("===================================")

    assert "•" not in cleaned_text
    assert "- Python" in cleaned_text
    assert "- Django" in cleaned_text
    assert "Experience: 2+ years" in cleaned_text

def test_skill_extraction_and_normalization():
    jd_text = """
    We are looking for a backend developer with experience in
    Python, JS, Django and Postgres.
    """

    known_skills = [
        "Python",
        "JavaScript",
        "JS",
        "Django",
        "PostgreSQL",
        "Postgres"
    ]

    skills = extract_skills(jd_text, known_skills)

    print("\n========== EXTRACTED SKILLS ==========")
    print(skills)
    print("=======================================")

    assert "Python" in skills
    assert "JavaScript" in skills
    assert "Django" in skills
    assert "PostgreSQL" in skills

def test_role_extraction_and_normalization():
    jd_text = """
    We are looking for a Python Engineer to join our backend team.
    """

    known_roles = [
        "Python Engineer",
        "Python Developer",
        "Backend Developer",
        "Software Engineer"
    ]

    role = extract_role(jd_text, known_roles)

    print("\n========== EXTRACTED ROLE ==========")
    print(role)
    print("====================================")

    assert role == "Python Developer"


def test_experience_extraction():
    jd_text = """
    We are looking for a Python Developer with 2+ years of experience.
    """

    experience = extract_experience(jd_text)

    print("\n========== EXTRACTED EXPERIENCE ==========")
    print(experience)
    print("===========================================")

    assert experience["minimum_years"] == 2
    assert experience["maximum_years"] is None



def test_education_extraction():
    jd_text = """
    Bachelor's degree in Computer Science or MCA is preferred.
    """

    education = extract_education(jd_text)

    print("\n========== EXTRACTED EDUCATION ==========")
    print(education)
    print("=========================================")

    assert "Bachelor's Degree" in education
    assert "Computer Science" in education
    assert "MCA" in education

from parsers.jd_parser import extract_skill_requirements


def test_required_and_preferred_skills():
    jd_text = """
    Required Skills:
    Python
    Django
    PostgreSQL

    Preferred Skills:
    Docker
    AWS
    """

    known_skills = [
        "Python",
        "Django",
        "PostgreSQL",
        "Docker",
        "AWS"
    ]

    result = extract_skill_requirements(jd_text, known_skills)

    print("\n========== SKILL REQUIREMENTS ==========")
    print(result)
    print("========================================")

    assert "Python" in result["required_skills"]
    assert "Django" in result["required_skills"]
    assert "PostgreSQL" in result["required_skills"]

    assert "Docker" in result["preferred_skills"]
    assert "AWS" in result["preferred_skills"]



def test_build_job_profile():
    jd_text = """
    Python Engineer

    Required Skills:
    Python
    Django
    PostgreSQL

    Preferred Skills:
    Docker
    AWS

    Experience: 2+ years

    Bachelor's degree in Computer Science or MCA is preferred.
    """

    known_skills = [
        "Python",
        "Django",
        "PostgreSQL",
        "Docker",
        "AWS"
    ]

    known_roles = [
        "Python Engineer",
        "Python Developer",
        "Backend Developer"
    ]

    profile = build_job_profile(
        jd_text,
        known_skills,
        known_roles
    )

    print("\n========== STRUCTURED JOB PROFILE ==========")
    print(profile)
    print("============================================")

    assert profile["job_id"] == "JOB-001"
    assert profile["title"] == "Python Developer"
    assert profile["experience_requirement"]["minimum_years"] == 2
    assert "Python" in profile["required_skills"]
    assert "Django" in profile["required_skills"]
    assert "Docker" in profile["preferred_skills"]
    assert "AWS" in profile["preferred_skills"]
    assert "Bachelor's Degree" in profile["education_requirements"]

def test_java_and_javascript_are_distinguished():
    jd_text = """
    Required Skills:
    JavaScript
    """

    known_skills = [
        "Java",
        "JavaScript"
    ]

    skills = extract_skills(jd_text, known_skills)

    print("\n========== JAVA MATCH TEST ==========")
    print(skills)
    print("=====================================")

    assert "JavaScript" in skills
    assert "Java" not in skills



def test_save_job_profile(tmp_path):
    profile = {
        "job_id": "JOB-001",
        "title": "Python Developer",
        "required_skills": ["Python", "Django"]
    }

    output_file = tmp_path / "job_profile.json"

    save_job_profile(profile, output_file)

    assert output_file.exists()

    with open(output_file, "r", encoding="utf-8") as file:
        saved_profile = json.load(file)

    assert saved_profile == profile
from parsers.jd_parser import extract_responsibilities


def test_responsibility_extraction():
    jd_text = """
    Responsibilities:
    Develop and maintain backend applications.
    Build REST APIs.
    Work with databases and development teams.

    Education:
    Bachelor's degree in Computer Science.
    """

    responsibilities = extract_responsibilities(jd_text)

    print("\n========== RESPONSIBILITIES ==========")
    print(responsibilities)
    print("======================================")

    assert "Develop and maintain backend applications." in responsibilities
    assert "Build REST APIs." in responsibilities
    assert "Work with databases and development teams." in responsibilities

from parsers.jd_parser import detect_sections


def test_section_detection():
    jd_text = """
    Software Engineer

    What We're Looking For:
    Fresh graduate or up to 2 years of experience.
    Familiarity with Python, JavaScript, Docker, Azure, or AWS.

    What You'll Build:
    AI agents and software products.
    Build end-to-end applications.

    Education:
    Bachelor's degree in Computer Science.
    """

    sections = detect_sections(jd_text)

    print("\n========== DETECTED SECTIONS ==========")
    print(sections)
    print("=======================================")

    assert "requirements" in sections
    assert "responsibilities" in sections
    assert "education" in sections

    assert "Python" in sections["requirements"]
    assert "AI agents" in sections["responsibilities"]
    assert "Bachelor's degree" in sections["education"]
def test_fresh_graduate_and_up_to_experience():
    jd_text = """
    What We're Looking For:
    Fresh graduate or up to 2 years of
    software-development experience.
    """

    experience = extract_experience(jd_text)

    print("\n========== FRESH GRADUATE EXPERIENCE ==========")
    print(experience)
    print("================================================")

    assert experience["minimum_years"] == 0
    assert experience["maximum_years"] == 2

def test_skills_from_requirements_section():
    jd_text = """
    What We're Looking For:
    Fresh graduate or up to 2 years of software-development experience.
    Strong software-engineering fundamentals.
    Experience building full-stack projects.
    Familiarity with Python, JavaScript, Docker, Azure, or AWS.
    """

    known_skills = [
        "Python",
        "JavaScript",
        "Docker",
        "Azure",
        "AWS"
    ]

    result = extract_skill_requirements(
        jd_text,
        known_skills
    )

    print("\n========== REQUIREMENT SECTION SKILLS ==========")
    print(result)
    print("================================================")

    assert "Python" in result["required_skills"]
    assert "JavaScript" in result["required_skills"]
    assert "Docker" in result["required_skills"]
    assert "Azure" in result["required_skills"]
    assert "AWS" in result["required_skills"]

def test_education_does_not_match_unrelated_text():
    jd_text = """
    About Our Company:
    We work with engineers and graduates from many backgrounds.

    What We're Looking For:
    Fresh graduate or up to 2 years of experience.
    Strong software-engineering fundamentals.
    Familiarity with Python and JavaScript.
    """

    education = extract_education(jd_text)

    print("\n========== EDUCATION FALSE POSITIVE TEST ==========")
    print(education)
    print("===================================================")

    assert education == []

def test_curly_apostrophe_section_heading():
    jd_text = """
    What We’re Looking For:
    Python
    JavaScript
    """

    sections = detect_sections(jd_text)

    assert "requirements" in sections
    assert "Python" in sections["requirements"]
    assert "JavaScript" in sections["requirements"]

from parsers.jd_parser import extract_employment


def test_employment_extraction():
    jd_text = """
    Location: Bengaluru

    Work arrangement: Full-time, work from office
    """

    employment = extract_employment(jd_text)

    print("\n========== EMPLOYMENT ==========")
    print(employment)
    print("================================")

    assert employment["type"] == "full-time"
    assert employment["work_mode"] == "work from office"
    assert employment["location"]["city"] == "Bengaluru"
    assert employment["location"]["country"] == "India"

def test_what_you_build_is_responsibilities():
    jd_text = """
    What You’ll Build:
    AI agents and harnesses for software-development.
    End-to-end products across frontend, backend, APIs, and infrastructure.

    Engineering Perks:
    Access to the latest AI models.
    """

    responsibilities = extract_responsibilities(jd_text)

    assert "AI agents and harnesses for software-development." in responsibilities
    assert "End-to-end products across frontend, backend, APIs, and infrastructure." in responsibilities
    assert "Access to the latest AI models." not in responsibilities

def test_skill_variations_are_normalized():
    jd_text = """
    Strong experience with React.js, REST APIs, Node.js and Postgres.
    """

    known_skills = [
        "React",
        "REST API",
        "Node.js",
        "PostgreSQL"
    ]

    skills = extract_skills(jd_text, known_skills)

    print("\n========== SKILL VARIATION TEST ==========")
    print(skills)
    print("==========================================")

    assert "React" in skills
    assert "REST API" in skills
    assert "Node.js" in skills
    assert "PostgreSQL" in skills

def test_be_is_detected_when_it_is_an_actual_requirement():
    jd_text = """
    Education:
    B.E. / B.Tech in Computer Science or related field.
    """

    education = extract_education(jd_text)

    print("\n========== B.E. POSITIVE TEST ==========")
    print(education)
    print("========================================")

    assert "B.E." in education
    assert "B.Tech" in education
    assert "Computer Science" in education

def test_optional_skill_extraction():
    jd_text = """
    React.js and Node.js are required.
    PostgreSQL is optional.
    """

    known_skills = [
        "React",
        "Node.js",
        "PostgreSQL"
    ]

    optional_skills = extract_optional_skills(
        jd_text,
        known_skills
    )

    print("\n========== OPTIONAL SKILLS ==========")
    print(optional_skills)
    print("=====================================")

    assert "PostgreSQL" in optional_skills
    assert "React" not in optional_skills
    assert "Node.js" not in optional_skills