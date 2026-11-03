"""Unit and regression tests for Day 17 ATS accuracy, reliability, and role adaptability."""

from datetime import date
from parsers.experience_parser import extract_experience, parse_date
from parsers.education_parser import extract_education, extract_academic_profile, normalize_degree
from parsers.jd_parser import extract_role, detect_sections, build_job_profile, ROLE_VARIATIONS
from scoring.education_relevance import score_education_relevance
from scoring.experience_relevance import score_experience_relevance
from scoring.skill_matcher import KNOWN_ROLES, score_skill_match
from main_ats_scorer import generate_candidate_report


def test_date_range_unicode_separators():
    """Verify that hyphen, en dash (\u2013), em dash (\u2014), and 'to' are parsed."""
    resume_en_dash = """
    EXPERIENCE
    Backend Engineer | Tech Corp | Jul 2021 \u2013 Present
    """
    entries = extract_experience(resume_en_dash, current_date=date(2026, 11, 1))
    assert len(entries) == 1
    assert entries[0]["job_title"] == "Backend Engineer"
    assert entries[0]["company"] == "Tech Corp"
    assert entries[0]["start_date"] == "2021-07-01"
    assert entries[0]["end_date"] == "2026-11-01"

    resume_em_dash = """
    EXPERIENCE
    Software Engineer | Data Systems | Jan 2020 \u2014 Dec 2022
    """
    entries_em = extract_experience(resume_em_dash)
    assert len(entries_em) == 1
    assert entries_em[0]["duration_months"] == 36

    resume_to = """
    EXPERIENCE
    Python Developer | Cloud Ltd | Jan 2022 to Jun 2023
    """
    entries_to = extract_experience(resume_to)
    assert len(entries_to) == 1
    assert entries_to[0]["duration_months"] == 18


def test_experience_pipe_delimiter_and_bullet_cleaning():
    """Verify pipe-delimited titles and companies with leading bullet points."""
    resume = """
    EXPERIENCE
    - HR Assistant Intern | PeopleBridge Services | Jan 2025 \u2013 Apr 2025
    - Coordinated interview calendars for 3 recruiters.
    """
    entries = extract_experience(resume)
    assert len(entries) == 1
    assert entries[0]["job_title"] == "HR Assistant Intern"
    assert entries[0]["company"] == "PeopleBridge Services"
    assert "Coordinated interview calendars" in entries[0]["responsibilities"]


def test_fresher_and_hr_employment_terms():
    """Verify non-technical and fresher terms (partner, executive, recruiter, trainee, assistant)."""
    resume = """
    EXPERIENCE
    Senior HR Business Partner | Global Corp | Feb 2020 \u2013 Present
    Marketing Coordinator | Media Hub | Jan 2018 \u2013 Jan 2020
    Software Engineering Trainee | Code Academy | Feb 2026 \u2013 May 2026
    """
    entries = extract_experience(resume, current_date=date(2026, 11, 1))
    titles = [e["job_title"] for e in entries]
    assert "Senior HR Business Partner" in titles
    assert "Marketing Coordinator" in titles
    assert "Software Engineering Trainee" in titles


def test_jd_role_detection_hr_roles():
    """Verify that HR roles and common variations are recognized correctly."""
    hr_cases = [
        ("JOB DESCRIPTION: Junior HR Executive\nWe need support...", "HR Executive"),
        ("Role: Human Resources Executive\nDepartment: HR", "HR Executive"),
        ("Title: HR Manager\nLooking for an experienced manager", "HR Manager"),
        ("Position: Senior HR Business Partner\nStrategy lead", "HR Business Partner"),
        ("JOB DESCRIPTION: Human Resources Business Partner", "HR Business Partner"),
        ("Job Title: Talent Acquisition Specialist\nHiring recruiter", "Talent Acquisition Specialist"),
        ("Role: Recruiter\nFocus on talent sourcing", "Recruiter"),
    ]

    for jd_text, expected_role in hr_cases:
        detected = extract_role(jd_text, KNOWN_ROLES)
        assert detected == expected_role, f"Expected {expected_role}, got {detected} for '{jd_text}'"


def test_jd_role_detection_prioritizes_explicit_title_over_body_mentions():
    """Verify that explicit header titles take precedence over body mentions."""
    jd_text = """
    JOB DESCRIPTION: Senior Backend Engineer
    We are seeking a Senior Backend Engineer.
    The engineer will collaborate with our Recruiter and HR Manager during hiring.
    """
    detected = extract_role(jd_text, KNOWN_ROLES)
    assert detected == "Backend Developer"


def test_jd_role_detection_unknown_role():
    """Verify that unrecognized roles return None rather than defaulting to Software Developer."""
    jd_text = """
    JOB DESCRIPTION: Chief Financial Officer
    Looking for a CFO with finance leadership experience.
    """
    detected = extract_role(jd_text, KNOWN_ROLES)
    assert detected is None


def test_jd_section_detection_criteria_aliases():
    """Verify that REQUIRED CRITERIA and PREFERRED CRITERIA are mapped properly."""
    jd_text = """
    JOB DESCRIPTION: Junior Python Developer
    REQUIRED CRITERIA
    - Python programming
    - Basic SQL
    PREFERRED CRITERIA
    - Docker
    - PostgreSQL
    """
    sections = detect_sections(jd_text)
    assert "required" in sections
    assert "preferred" in sections
    assert "Python programming" in sections["required"]
    assert "Docker" in sections["preferred"]


def test_non_technical_degree_extraction():
    """Verify extraction of BBA, MBA, B.Com, M.Com, and PGDM degrees."""
    resume = """
    EDUCATION
    BBA, Human Resource Management | Greenfield College | 2025
    MBA, Finance | Coastal Business School | 2017
    B.Com, Marketing | Malabar College | 2026
    """
    edu = extract_education(resume)
    degrees = [item["degree"] for item in edu]
    fields = [item["field_of_study"] for item in edu]

    assert "Bachelor of Business Administration" in degrees
    assert "Master of Business Administration" in degrees
    assert "Bachelor of Commerce" in degrees
    assert "Human Resource Management" in fields
    assert "Finance" in fields
    assert "Marketing" in fields


def test_flexible_hr_education_relevance():
    """Verify HR education scoring recognizes both direct HR and transferable business/commerce degrees."""
    hr_profile = {
        "education": [
            {"degree": "Bachelor of Business Administration", "field_of_study": "Human Resource Management"},
        ]
    }
    result = score_education_relevance(hr_profile, "HR Executive")
    assert result["education_scores"][0]["relevance_score"] == 100

    commerce_profile = {
        "education": [
            {"degree": "Bachelor of Commerce", "field_of_study": "Marketing"},
        ]
    }
    result_comm = score_education_relevance(commerce_profile, "HR Executive")
    assert result_comm["education_scores"][0]["relevance_score"] == 100

    tech_profile = {
        "education": [
            {"degree": "Bachelor of Technology", "field_of_study": "Computer Science"},
        ]
    }
    result_tech = score_education_relevance(tech_profile, "HR Executive")
    assert result_tech["education_scores"][0]["relevance_score"] == 30  # Has degree but field is not HR-related


def test_structured_experience_requirement_integration():
    """Verify structured experience requirements are retained without arbitrary text conversion."""
    entries = [
        {
            "company": "Northstar",
            "job_title": "Senior Backend Engineer",
            "responsibilities": "Designed FastAPI services and Redis caching.",
        }
    ]
    exp_req = {"minimum_years": 6, "maximum_years": None}
    res = score_experience_relevance(entries, "Backend Developer", ["FastAPI services", "REST APIs"], experience_requirement=exp_req)

    assert res["experience_requirement_assessment"]["minimum_years_required"] == 6
    assert res["experience_requirement_assessment"]["maximum_years_required"] is None
    assert len(res["role_scores"]) == 1
    assert res["role_scores"][0]["relevance_score"] > 20


def test_main_ats_scorer_unrecognized_role_not_defaulted():
    """Verify main_ats_scorer uses Undetected Role rather than Software Developer when role is unknown."""
    from main_ats_scorer import generate_candidate_report
    report = generate_candidate_report(
        "data/testing/resumes/tech_fresher/T-F01_aarav_menon.pdf",
        "data/testing/job_descriptions/JD03_junior_hr_executive.txt",
    )
    assert report["job_role"] == "HR Executive"
