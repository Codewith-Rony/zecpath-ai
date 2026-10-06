# Day 6 – Job Description Parsing System

## Objective

The Job Description Parsing System converts unstructured job descriptions into structured, AI-readable job requirement objects.

The parser extracts important hiring information such as job roles, skills, experience requirements, education requirements, and responsibilities.

## Processing Pipeline

Raw Job Description
        ↓
Text Normalization
        ↓
Skill Extraction
        ↓
Role Detection
        ↓
Experience Extraction
        ↓
Education Extraction
        ↓
Required / Preferred Skill Classification
        ↓
Responsibility Extraction
        ↓
Structured Job Profile
        ↓
JSON Output

## Implemented Components

### 1. JD Text Normalization

The parser normalizes raw job description text by:

- Normalizing Unicode characters
- Converting different bullet characters
- Normalizing line endings
- Removing excessive spaces
- Reducing excessive blank lines

Function:

`normalize_jd_text()`

### 2. Skill Extraction

The parser identifies skills from a predefined list of known skills.

Common skill variations are normalized.

Examples:

- JS → JavaScript
- ReactJS → React
- NodeJS → Node.js
- Postgres → PostgreSQL
- DRF → Django REST Framework

Function:

`extract_skills()`

### 3. Role Detection

The parser detects job roles and normalizes common role variations.

Examples:

- Python Engineer → Python Developer
- Backend Engineer → Backend Developer
- Software Engineer → Software Engineer
- Full Stack Developer → Full Stack Developer

Function:

`extract_role()`

### 4. Experience Extraction

The parser identifies common experience formats such as:

- 2+ years
- 3–5 years
- 3 to 5 years
- Minimum 3 years
- Freshers

The result is converted into minimum and maximum experience values.

Function:

`extract_experience()`

### 5. Education Extraction

The parser identifies common education requirements and normalizes them.

Examples:

- Bachelor's degree
- B.Tech
- B.E.
- Master's degree
- M.Tech
- MCA
- MBA
- Computer Science

Function:

`extract_education()`

### 6. Required and Preferred Skills

The parser separates skills into:

- Required skills
- Preferred skills

Section boundaries are used to prevent skills from unrelated sections being incorrectly classified.

Function:

`extract_skill_requirements()`

### 7. Responsibility Extraction

The parser extracts individual responsibilities from the Responsibilities section.

Function:

`extract_responsibilities()`

### 8. Structured Job Profile

All extracted information is combined into a structured job profile.

Function:

`build_job_profile()`

The structured output contains:

- Job ID
- Job title
- Description
- Experience requirements
- Required skills
- Preferred skills
- Education requirements
- Responsibilities
- Qualifications
- Certifications
- Employment information

### 9. JSON Output

Structured job profiles are stored as JSON using the existing file handling utility.

Function:

`save_job_profile()`

## Example Output

```json
{
    "job_id": "JOB-001",
    "title": "Python Developer",
    "experience_requirement": {
        "minimum_years": 2,
        "maximum_years": null
    },
    "required_skills": [
        "Python",
        "Django",
        "REST API",
        "PostgreSQL"
    ],
    "preferred_skills": [
        "Docker",
        "AWS"
    ],
    "education_requirements": [
        "Bachelor's Degree",
        "MCA",
        "Computer Science"
    ],
    "responsibilities": [
        "Develop and maintain backend applications.",
        "Build REST APIs.",
        "Work with databases and development teams."
    ]
}