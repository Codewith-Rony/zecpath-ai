import re

EMAIL_PATTERN = r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"

PHONE_PATTERN = r"(?:\+91[\s-]?)?[6-9]\d{9}"
SECTION_HEADINGS = {
    "skills": [
        "skills",
        "technical skills",
        "core skills",
        "core competencies",
        "technical competencies",
        "technologies",
        "additional skills",
    ],

    "work_experience": [
        "experience",
        "work experience",
        "professional experience",
        "employment history",
        "work history",
        "career history",
    ],

    "education": [
        "education",
        "educational background",
        "academic background",
        "academic qualifications",
    ],

    "certifications": [
        "certifications",
        "certificates",
        "professional certifications",
    ],

    "projects": [
        "projects",
        "project experience",
        "academic projects",
        "personal projects",
    ],
    "summary": [
    "summary",
    "professional summary",
    "profile",
    "career summary",
    "objective",
    "career objective",
],
"contact": [
    "contact",
    "contact information",
    "personal information",
],
}


def normalize_heading(text):
    """Normalize a possible resume heading."""

    text = text.strip().lower()

    # Remove punctuation at the beginning/end
    text = re.sub(r"^[^a-z0-9]+|[^a-z0-9]+$", "", text)

    # Convert multiple spaces into one
    text = re.sub(r"\s+", " ", text)

    return text


def classify_heading(text):
    """Return the section name if the heading is recognized."""

    heading = normalize_heading(text)

    for section, headings in SECTION_HEADINGS.items():
        if heading in headings:
            return section

    return None

def split_into_blocks(text):
    """
    Split resume text into logical blocks.
    """

    text = split_inline_headings(text)

    lines = text.splitlines()
    blocks = []
    current_block = []

    for line in lines:
        stripped = line.strip()

        if not stripped:
            if current_block:
                blocks.append("\n".join(current_block).strip())
                current_block = []
            continue

        heading_section = classify_heading(stripped)

        if heading_section and current_block:
            blocks.append("\n".join(current_block).strip())
            current_block = []

        current_block.append(stripped)

    if current_block:
        blocks.append("\n".join(current_block).strip())

    return blocks
    
def classify_block(block):
    """
    Identify the section of a resume block using its first line.

    Returns the section name if recognized.
    Otherwise returns None.
    """

    lines = block.splitlines()

    if not lines:
        return None

    # The first line is treated as the possible section heading
    heading = lines[0].strip()

    return classify_heading(heading)

def split_inline_headings(text):
    """
    Split text when a recognized section heading appears
    inside another line.
    """

    heading_patterns = []

    for headings in SECTION_HEADINGS.values():
        for heading in headings:
            heading_patterns.append(re.escape(heading))

    if not heading_patterns:
        return text

    pattern = r"\s*\|\s*(" + "|".join(heading_patterns) + r")\b"

    return re.sub(
        pattern,
        r"\n\1\n",
        text,
        flags=re.IGNORECASE
    )

def is_contact_block(block):
    """
    Detect whether a resume block contains contact information.
    """

    text = block.lower()

    has_email = re.search(EMAIL_PATTERN, text)
    has_phone = re.search(PHONE_PATTERN, text)

    contact_keywords = [
        "linkedin",
        "github",
        "portfolio",
        "email",
        "phone",
        "mobile",
    ]

    has_contact_keyword = any(
        keyword in text for keyword in contact_keywords
    )

    return bool(has_email or has_phone or has_contact_keyword)
CONTENT_KEYWORDS = {
    "skills": [
        "python",
        "java",
        "javascript",
        "typescript",
        "c",
        "c++",
        "c#",
        "html",
        "css",
        "react",
        "node.js",
        "nodejs",
        "django",
        "flask",
        "spring",
        "sql",
        "mysql",
        "mongodb",
        "git",
        "docker",
        "aws",
        "azure",
        "flutter",
    ],

    "education": [
        "b.tech",
        "btech",
        "b.e",
        "be ",
        "bachelor",
        "master",
        "m.tech",
        "mtech",
        "mca",
        "mba",
        "ph.d",
        "university",
        "college",
        "degree",
    ],

    "certifications": [
        "certified",
        "certification",
        "certificate",
        "coursera",
        "udemy",
        "aws certified",
        "microsoft certified",
    ],

    "work_experience": [
        "intern",
        "internship",
        "developer",
        "engineer",
        "manager",
        "analyst",
        "company",
        "responsibilities",
        "worked",
        "experience",
    ],

    "projects": [
        "project",
        "developed",
        "built",
        "implemented",
        "application",
        "website",
        "system",
    ],
    "contact": [
    "@",
    "linkedin",
    "github",
    "portfolio",
    "phone",
    "email",
    ],
}

PROJECT_INDICATORS = [
    "project",
    "website",
    "web app",
    "application",
    "platform",
    "portal",
    "mobile app",
    "system",
    "dashboard",
    "tool",
]
def is_project_block(block):
    lines = [line.strip() for line in block.splitlines() if line.strip()]
    text = " ".join(lines).lower()

    if len(lines) < 2:
        return False

    # Avoid misclassifying contact information
    if is_contact_block(block):
        return False

    # Avoid education/work-experience blocks
    excluded_terms = [
        "b.tech",
        "btech",
        "bachelor",
        "master",
        "university",
        "college",
        "intern",
        "internship",
        "company",
        "experience",
        "present",
    ]

    if any(term in text for term in excluded_terms):
        return False

    return any(term in text for term in PROJECT_INDICATORS)

def classify_block_by_content(block):
    """
    Classify a resume block based on keywords found in its content.

    Returns the section with the highest score.
    Returns None when no section has enough evidence.
    """

    text = block.lower()

    scores = {}

    for section, keywords in CONTENT_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if keyword in text:
                score += 1

        scores[section] = score

    best_section = max(scores, key=scores.get)
    best_score = scores[best_section]

    # Don't classify a block unless we have enough evidence
    if best_score < 2:
        return None

    return best_section

def classify_block_final(block):
    section = classify_block(block)

    if section:
        return section

    if is_contact_block(block):
        return "contact"

    text = block.lower()
    if "additional skills" in block.lower():
        return "skills"
    # Detect certification content even without a heading
    certification_terms = [
        "certificate",
        "certification",
        "certified",
        "issued:",
    ]

    if any(term in text for term in certification_terms):
        return "certifications"

    if is_project_block(block):
        return "projects"

    return classify_block_by_content(block)


def segment_resume(text):
    """
    Split a resume into blocks and classify each block.

    Returns a dictionary containing the detected sections
    and their corresponding text blocks.
    """

    blocks = split_into_blocks(text)

    sections = {
        "summary": [],
        "contact": [],
        "skills": [],
        "work_experience": [],
        "education": [],
        "certifications": [],
        "projects": [],
        "other": []
    }

    for block in blocks:
        section = classify_block_final(block)

        if section:
            sections[section].append(block)
        else:
            sections["other"].append(block)

    return sections

def segment_extracted_resume(extracted_resume):
    """
    Segment a resume using the cleaned text produced
    by the Day 5 resume extractor.
    """

    cleaned_text = extracted_resume.get("cleaned_text", "")

    if not cleaned_text:
        raise ValueError("Resume does not contain cleaned text.")

    sections = segment_resume(cleaned_text)

    return {
        "file_name": extracted_resume.get("file_name"),
        "file_type": extracted_resume.get("file_type"),
        "sections": sections
    }

