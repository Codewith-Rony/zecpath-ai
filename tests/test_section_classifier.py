from parsers.resume_section_classifier import (
    normalize_heading,
    classify_heading,
)


def test_normalize_heading():
    assert normalize_heading("  TECHNICAL SKILLS:  ") == "technical skills"


def test_skills_heading():
    assert classify_heading("Technical Skills") == "skills"


def test_experience_heading():
    assert classify_heading("Professional Experience") == "work_experience"


def test_education_heading():
    assert classify_heading("Academic Background") == "education"


def test_unknown_heading():
    assert classify_heading("Web Developer") is None

def test_split_into_blocks():
    from parsers.resume_section_classifier import split_into_blocks

    text = """
    SKILLS
    Python
    Java
    MongoDB

    PROFESSIONAL EXPERIENCE
    Web Developer
    ABC Company

    EDUCATION
    B.Tech Information Technology
    XYZ College
    """

    blocks = split_into_blocks(text)

    assert len(blocks) == 3
    assert "SKILLS" in blocks[0]
    assert "Python" in blocks[0]

    assert "PROFESSIONAL EXPERIENCE" in blocks[1]
    assert "Web Developer" in blocks[1]

    assert "EDUCATION" in blocks[2]
    assert "B.Tech Information Technology" in blocks[2]

def test_classify_block():
    from parsers.resume_section_classifier import classify_block

    skills_block = """TECHNICAL SKILLS
    Python
    Java
    MongoDB"""

    experience_block = """PROFESSIONAL EXPERIENCE
    Web Developer
    ABC Company"""

    unknown_block = """Python
    Java
    MongoDB"""

    assert classify_block(skills_block) == "skills"
    assert classify_block(experience_block) == "work_experience"
    assert classify_block(unknown_block) is None

def test_classify_block_by_content():
    from parsers.resume_section_classifier import classify_block_by_content

    skills_block = """
    Python
    Java
    MongoDB
    Git
    Docker
    """

    education_block = """
    B.Tech Information Technology
    Amal Jyothi College of Engineering
    2022 - 2026
    """

    unknown_block = """
    Rony Thomas
    Kerala
    """

    assert classify_block_by_content(skills_block) == "skills"
    assert classify_block_by_content(education_block) == "education"
    assert classify_block_by_content(unknown_block) is None

def test_classify_block_final():
    from parsers.resume_section_classifier import classify_block_final

    heading_block = """TECHNICAL SKILLS
    Python
    Java"""

    no_heading_block = """
    Python
    Java
    MongoDB
    Git
    """

    unknown_block = """
    Rony Thomas
    Kerala
    """

    assert classify_block_final(heading_block) == "skills"
    assert classify_block_final(no_heading_block) == "skills"
    assert classify_block_final(unknown_block) is None

def test_segment_resume():
    from parsers.resume_section_classifier import segment_resume

    resume = """
    TECHNICAL SKILLS
    Python
    Java
    MongoDB

    PROFESSIONAL EXPERIENCE
    Web Developer
    ABC Technologies

    EDUCATION
    B.Tech Information Technology
    XYZ College

    PROJECTS
    Zecpath AI
    """

    result = segment_resume(resume)

    assert len(result["skills"]) == 1
    assert len(result["work_experience"]) == 1
    assert len(result["education"]) == 1
    assert len(result["projects"]) == 1

    assert "Python" in result["skills"][0]
    assert "Web Developer" in result["work_experience"][0]
    assert "B.Tech" in result["education"][0]
    assert "Zecpath AI" in result["projects"][0]

def test_segment_extracted_resume():
    from parsers.resume_section_classifier import segment_extracted_resume

    extracted_resume = {
        "file_name": "resume.pdf",
        "file_type": ".pdf",
        "cleaned_text": """
        TECHNICAL SKILLS
        Python
        Java

        EDUCATION
        B.Tech Information Technology
        """,
    }

    result = segment_extracted_resume(extracted_resume)

    assert result["file_name"] == "resume.pdf"
    assert result["file_type"] == ".pdf"

    sections = result["sections"]

    assert len(sections["skills"]) == 1
    assert "Python" in sections["skills"][0]

    assert len(sections["education"]) == 1
    assert "B.Tech" in sections["education"][0]

    assert len(sections["work_experience"]) == 0

def test_segment_extracted_resume():
    from parsers.resume_section_classifier import segment_extracted_resume

    extracted_resume = {
        "file_name": "sample.pdf",
        "file_type": ".pdf",
        "raw_text": "raw resume text",
        "cleaned_text": """
        TECHNICAL SKILLS
        Python
        Java
        MongoDB

        EDUCATION
        B.Tech Information Technology
        XYZ College
        """
    }

    result = segment_extracted_resume(extracted_resume)

    assert result["file_name"] == "sample.pdf"
    assert result["file_type"] == ".pdf"

    assert len(result["sections"]["skills"]) == 1
    assert len(result["sections"]["education"]) == 1

def test_contact_block_detection():
    from parsers.resume_section_classifier import is_contact_block

    contact_block = """
    BIBIN V S
    Marine Structural Designer
    Trivandrum, Kerala
    +91 9633771476
    bibinvs16061998@gmail.com
    """

    non_contact_block = """
    Python
    Java
    MongoDB
    Git
    """

    assert is_contact_block(contact_block) is True
    assert is_contact_block(non_contact_block) is False

def test_missing_headings():
    from parsers.resume_section_classifier import segment_resume

    resume = """
    Python
    Java
    MongoDB
    Git
    Docker

    B.Tech Information Technology
    Amal Jyothi College of Engineering
    2022 - 2026
    """

    result = segment_resume(resume)

    assert len(result["skills"]) == 1
    assert len(result["education"]) == 1

    assert "Python" in result["skills"][0]
    assert "B.Tech" in result["education"][0]