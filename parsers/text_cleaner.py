import re
import unicodedata


SECTION_HEADINGS = {
    "summary": "SUMMARY",
    "education": "EDUCATION",
    "experience": "EXPERIENCE",
    "work experience": "EXPERIENCE",
    "professional experience": "EXPERIENCE",
    "projects": "PROJECTS",
    "skills": "SKILLS",
    "technical skills": "SKILLS",
    "certifications": "CERTIFICATIONS",
    "achievements": "ACHIEVEMENTS",
    "languages": "LANGUAGES",
}


def clean_line(line):
    """
    Clean spacing and normalize common Unicode characters
    from one line of extracted resume text.
    """

    line = unicodedata.normalize("NFKC", line)

    # Replace different bullet characters
    line = line.replace("•", "-")
    line = line.replace("●", "-")
    line = line.replace("▪", "-")

    # Replace tabs with spaces
    line = line.replace("\t", " ")

    # Remove excessive spaces
    line = re.sub(r" {2,}", " ", line)

    return line.strip()


def normalize_heading(line):
    """
    Convert known resume section headings
    into a consistent format.
    """

    key = line.lower().strip()

    return SECTION_HEADINGS.get(key, line)


def clean_resume_text(text):
    """
    Clean and normalize extracted resume text.
    """

    cleaned_lines = []

    for line in text.splitlines():

        line = clean_line(line)

        # Ignore completely empty lines for now
        if not line:
            continue

        # Normalize section headings
        line = normalize_heading(line)

        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)