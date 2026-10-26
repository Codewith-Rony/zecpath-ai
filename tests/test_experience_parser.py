
from datetime import date
from parsers.experience_parser import analyze_experience_timeline
from parsers.experience_parser import (
    parse_date,
    duration_months,
    extract_experience,
)


def test_parse_month_and_year():
    assert parse_date("Jan 2023") == date(2023, 1, 1)


def test_parse_numeric_date():
    assert parse_date("06/2022") == date(2022, 6, 1)


def test_parse_present():
    assert parse_date(
        "Present", date(2026, 10, 1)
    ) == date(2026, 10, 1)


def test_duration_months():
    assert duration_months(
        date(2023, 1, 1), date(2023, 3, 1)
    ) == 3


def test_extract_experience():
    resume = """
    EXPERIENCE
    Python Developer at ABC Technologies
    Jan 2023 - Dec 2024
    """

    entries = extract_experience(
        resume, current_date=date(2026, 10, 1)
    )

    assert len(entries) == 1
    assert entries[0]["company"] == "ABC Technologies"
    assert entries[0]["job_title"] == "Python Developer"
    assert entries[0]["duration_months"] == 24


def test_timeline_total_experience():
    entries = [
        {
            "company": "A",
            "job_title": "Developer",
            "start_date": "2022-01-01",
            "end_date": "2022-12-01",
            "duration_months": 12,
        },
        {
            "company": "B",
            "job_title": "Engineer",
            "start_date": "2023-01-01",
            "end_date": "2023-12-01",
            "duration_months": 12,
        },
    ]

    result = analyze_experience_timeline(entries)
    assert result["total_experience_months"] == 24
    assert result["employment_gaps"] == []


def test_timeline_detects_gap():
    entries = [
        {
            "company": "A",
            "job_title": "Developer",
            "start_date": "2022-01-01",
            "end_date": "2022-06-01",
            "duration_months": 6,
        },
        {
            "company": "B",
            "job_title": "Engineer",
            "start_date": "2022-10-01",
            "end_date": "2022-12-01",
            "duration_months": 3,
        },
    ]

    result = analyze_experience_timeline(entries)
    assert result["employment_gaps"][0]["duration_months"] == 3


def test_timeline_detects_overlap_without_double_counting():
    entries = [
        {
            "company": "A",
            "job_title": "Developer",
            "start_date": "2022-01-01",
            "end_date": "2022-08-01",
            "duration_months": 8,
        },
        {
            "company": "B",
            "job_title": "Consultant",
            "start_date": "2022-06-01",
            "end_date": "2022-12-01",
            "duration_months": 7,
        },
    ]

    result = analyze_experience_timeline(entries)
    assert result["total_experience_months"] == 12
    assert len(result["overlapping_roles"]) == 1
    assert result["overlapping_roles"][0]["overlap_months"] == 3


def test_education_is_not_counted_as_employment():
    resume = """
    EDUCATION
    Bachelor of Technology (B.Tech) in Information Technology
    2022 - 2026
    CGPA: 7.3

    Higher Secondary Education
    2020 - 2022
    Percentage: 93.5%

    EXPERIENCE
    Web Developer Intern at Example Technologies
    Feb 2025 - Oct 2025
    """

    entries = extract_experience(resume)

    assert len(entries) == 1
    assert entries[0]["job_title"] == "Web Developer Intern"
    assert entries[0]["company"] == "Example Technologies"
