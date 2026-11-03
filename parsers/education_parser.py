
import re


def normalize_degree(value):
    """Normalize common degree names."""
    value = re.sub(r"\s+", " ", value).strip()
    degree_map = {
        "b.tech": "Bachelor of Technology",
        "btech": "Bachelor of Technology",
        "b.e.": "Bachelor of Engineering",
        "b.e": "Bachelor of Engineering",
        "m.tech": "Master of Technology",
        "mtech": "Master of Technology",
        "b.sc": "Bachelor of Science",
        "b.sc.": "Bachelor of Science",
        "m.sc": "Master of Science",
        "m.sc.": "Master of Science",
        "bca": "Bachelor of Computer Applications",
        "mca": "Master of Computer Applications",
        "bba": "Bachelor of Business Administration",
        "mba": "Master of Business Administration",
        "b.com": "Bachelor of Commerce",
        "b.com.": "Bachelor of Commerce",
        "bcom": "Bachelor of Commerce",
        "m.com": "Master of Commerce",
        "m.com.": "Master of Commerce",
        "mcom": "Master of Commerce",
        "b.a": "Bachelor of Arts",
        "b.a.": "Bachelor of Arts",
        "ba": "Bachelor of Arts",
        "m.a": "Master of Arts",
        "m.a.": "Master of Arts",
        "ma": "Master of Arts",
        "pgdm": "Post Graduate Diploma in Management",
        "ph.d": "Doctor of Philosophy",
        "ph.d.": "Doctor of Philosophy",
        "phd": "Doctor of Philosophy",
    }

    return degree_map.get(value.lower(), value)


def extract_education(resume_text):
    """Extract basic academic details from resume text."""
    education = []

    degree_pattern = re.compile(
        r"\b("
        r"B\.?\s?Tech\.?|B\.?\s?E\.?|M\.?\s?Tech\.?|"
        r"B\.?\s?Sc\.?|M\.?\s?Sc\.?|BCA|MCA|"
        r"BBA|MBA|B\.?\s?Com\.?|M\.?\s?Com\.?|"
        r"B\.?\s?A\.?|M\.?\s?A\.?|PGDM|Ph\.?D\.?|"
        r"Bachelor of (?:Technology|Engineering|Science|Arts|Commerce|"
        r"Computer Applications|Business Administration)|"
        r"Master of (?:Technology|Engineering|Science|Arts|Commerce|"
        r"Computer Applications|Business Administration)"
        r")\b",
        re.IGNORECASE,
    )

    lines = [line.strip() for line in resume_text.splitlines() if line.strip()]
    current_institution = None

    for index, line in enumerate(lines):
        if re.search(r"\b(university|college|institute)\b", line, re.IGNORECASE):
            current_institution = line

        match = degree_pattern.search(line)
        if not match:
            continue

        degree = normalize_degree(match.group(0))

        # Try to identify the field of study.
        field_of_study = None
        field_match = re.search(
            r"\bin\s+([^|(]+)",
            line,
            re.IGNORECASE,
        )
        if field_match:
            field_of_study = field_match.group(1).strip(" .,-")
        else:
            after_degree = line[match.end():].strip(" .,-")
            if after_degree:
                first_seg = after_degree.split("|")[0].strip(" .,-")
                if first_seg and not any(term in first_seg.lower() for term in ["university", "college", "institute", "school", "cgpa", "gpa", "percentage", "19", "20"]):
                    field_of_study = first_seg

        # Find a graduation year on this line or nearby lines.
        graduation_year = None
        nearby_lines = lines[index:index + 3]

        for nearby_line in nearby_lines:
            year_match = re.search(r"\b(19|20)\d{2}\b", nearby_line)
            if year_match:
                graduation_year = int(year_match.group(0))

        education.append({
            "degree": degree,
            "field_of_study": field_of_study,
            "institution": current_institution,
            "graduation_year": graduation_year,
        })

    return education


def extract_certifications(resume_text):
    """Extract certification names from a resume."""
    certifications = []

    certification_keywords = (
        "certification",
        "certified",
        "certificate",
    )

    relevance_categories = {
        "python": "programming",
        "aws": "cloud",
        "azure": "cloud",
        "google cloud": "cloud",
        "machine learning": "ai_ml",
        "data science": "data",
        "cybersecurity": "security",
        "network": "networking",
    }

    for line in resume_text.splitlines():
        line = line.strip()

        if not line:
            continue
        if line.lower().strip(" :") in {
            "certification",
            "certifications",
            "professional certifications",
            "licenses and certifications",
        }:
            continue
        if not any(
            keyword in line.lower()
            for keyword in certification_keywords
        ):
            continue

        category = "general"
        for keyword, label in relevance_categories.items():
            if keyword in line.lower():
                category = label
                break

        certifications.append({
            "name": line,
            "relevance_category": category,
        })

    return certifications


def extract_academic_profile(resume_text):
    """Build a structured academic profile from resume text."""
    return {
        "education": extract_education(resume_text),
        "certifications": extract_certifications(resume_text),
    }
