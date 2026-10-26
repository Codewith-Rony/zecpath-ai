from parsers.education_parser import extract_education
from parsers.education_parser import extract_certifications
from parsers.education_parser import extract_academic_profile

def test_extract_education():
    sample = """
    Bachelor of Technology (B.Tech) in Information Technology
    """

    result = extract_education(sample)

    assert len(result) >= 1
    assert result[0]["degree"] == "Bachelor of Technology"


from parsers.education_parser import extract_education


def test_extract_education_details():
    sample = """
    EDUCATION
    Imperial College London
    Bachelor of Science in Computer Science
    Expected: June 2025
    """

    result = extract_education(sample)

    assert len(result) == 1
    assert result[0]["degree"] == "Bachelor of Science"
    assert result[0]["field_of_study"] == "Computer Science"
    assert result[0]["institution"] == "Imperial College London"
    assert result[0]["graduation_year"] == 2025


def test_extract_btech_degree():
    sample = """
    EDUCATION
    Amal Jyothi College of Engineering
    Bachelor of Technology (B.Tech) in Information Technology
    2026
    """

    result = extract_education(sample)

    assert len(result) >= 1
    assert result[0]["degree"] == "Bachelor of Technology"
    assert result[0]["field_of_study"] == "Information Technology"
    assert result[0]["graduation_year"] == 2026


def test_extract_certifications():
    sample = """
    CERTIFICATIONS
    AWS Certified Cloud Practitioner
    Python Programming Certification
    """

    result = extract_certifications(sample)

    assert len(result) == 2
    assert result[0]["relevance_category"] == "cloud"
    assert result[1]["relevance_category"] == "programming"


def test_extract_academic_profile():
    sample = """
    EDUCATION
    Imperial College London
    Bachelor of Science in Computer Science
    Expected: June 2025

    CERTIFICATIONS
    AWS Certified Cloud Practitioner
    """

    result = extract_academic_profile(sample)

    assert "education" in result
    assert "certifications" in result
    assert len(result["education"]) == 1
    assert len(result["certifications"]) == 1
