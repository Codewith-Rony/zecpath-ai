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

_RE_EXCESSIVE_SPACES = re.compile(r" {2,}")
_RE_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")


def clean_line(line):
    """
    Clean spacing and normalize common Unicode characters
    from one line of extracted resume text.
    """

    line = unicodedata.normalize("NFKC", line)

    # Strip unprintable control characters that may occur in noisy/corrupt files
    line = _RE_CONTROL_CHARS.sub("", line)

    # Replace different bullet characters
    line = line.replace("•", "-")
    line = line.replace("●", "-")
    line = line.replace("▪", "-")

    # Replace tabs with spaces
    line = line.replace("\t", " ")

    # Remove excessive spaces using precompiled regex
    line = _RE_EXCESSIVE_SPACES.sub(" ", line)

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
    if not text:
        return ""

    # Strip unprintable control characters (including VT, FF) before line splitting
    text = _RE_CONTROL_CHARS.sub("", text)

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
