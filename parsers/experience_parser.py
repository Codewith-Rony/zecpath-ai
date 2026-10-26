
from operator import index
import re
from datetime import date


MONTHS = {
    "jan": 1, "january": 1,
    "feb": 2, "february": 2,
    "mar": 3, "march": 3,
    "apr": 4, "april": 4,
    "may": 5,
    "jun": 6, "june": 6,
    "jul": 7, "july": 7,
    "aug": 8, "august": 8,
    "sep": 9, "sept": 9, "september": 9,
    "oct": 10, "october": 10,
    "nov": 11, "november": 11,
    "dec": 12, "december": 12,
}


def parse_date(value, current_date=None):
    """Parse common resume dates, including Present."""
    value = value.strip()

    if value.lower() in {"present", "current", "currently"}:
        current_date = current_date or date.today()
        return date(current_date.year, current_date.month, 1)

    match = re.fullmatch(r"(\d{4})", value)
    if match:
        return date(int(match.group(1)), 1, 1)

    match = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{1,2}),?\s+(\d{4})",
        value,
    )
    if match:
        month_name, day, year = match.groups()
        month = MONTHS.get(month_name.lower())
        if month:
            return date(int(year), month, int(day))

    match = re.fullmatch(r"(\d{1,2})/(\d{4})", value)
    if match:
        month, year = map(int, match.groups())
        if 1 <= month <= 12:
            return date(year, month, 1)

    match = re.fullmatch(
        r"([A-Za-z]+)\s+(\d{4})", value
    )
    if match:
        month_name, year = match.groups()
        month = MONTHS.get(month_name.lower())
        if month:
            return date(int(year), month, 1)

    return None


def duration_months(start_date, end_date):
    """Calculate calendar-month duration, inclusive of both months."""
    return (
        (end_date.year - start_date.year) * 12
        + end_date.month - start_date.month
        + 1
    )





def extract_experience(resume_text, current_date=None):
    """Extract employment entries from common resume layouts."""
    lines = [
        re.sub(r"\s+", " ", line).strip()
        for line in resume_text.splitlines()
        if line.strip()
    ]

    date_pattern = re.compile(
        r"(?P<start>"
        r"(?:[A-Za-z]+\s+\d{1,2},?\s+\d{4}|"
        r"[A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|\d{4})"
        r")\s*(?:-|â€“|â€”|to)\s*"
        r"(?P<end>"
        r"(?:[A-Za-z]+\s+\d{1,2},?\s+\d{4}|"
        r"[A-Za-z]+\s+\d{4}|\d{1,2}/\d{4}|\d{4}|"
        r"Present|Current|Currently)"
        r")",
        re.IGNORECASE,
    )

    education_terms = (
        "education", "b.tech", "bachelor", "master",
        "higher secondary", "high school", "school",
        "university", "college", "cgpa", "gpa:",
        "percentage:", "graduation",
    )
    employment_terms = (
        "intern", "developer", "engineer", "manager",
        "analyst", "designer", "consultant", "architect",
        "administrator", "scientist", "specialist", "lead",
        "programmer", "tester", "technician",
    )
    experience_headings = {
        "experience", "work experience", "professional experience",
        "employment history", "work history", "internship experience",
    }
    education_headings = {
        "education", "academic background", "educational qualifications",
    }
    other_section_headings = {
        "projects", "personal projects", "technical skills", "skills",
        "certifications", "certificates", "achievements", "awards",
        "publications", "languages", "interests", "summary",
        "professional summary", "profile",
    }
    title_company_split = re.compile(r"\s+(?:at|@)\s+", re.IGNORECASE)

    def is_job_title(value):
        lower = value.lower()
        return (
            any(term in lower for term in employment_terms)
            and not any(term in lower for term in education_terms)
            and not date_pattern.search(value)
        )

    def is_location(value):
        lower = value.lower()
        return (
            "," in value
            or lower in {"remote", "hybrid", "on-site", "onsite"}
            or re.fullmatch(r"[A-Z][A-Za-z .'-]+,\s*[A-Z][A-Za-z .'-]+", value) is not None
        )

    current_section = ""
    entries = []

    for index, line in enumerate(lines):
        heading = line.strip(" :|-").lower()

        if heading in education_headings:
            current_section = "education"
            continue
        if heading in experience_headings:
            current_section = "experience"
            continue
        if heading in other_section_headings:
            current_section = "other"
            continue

        match = date_pattern.search(line)
        if not match or current_section in {"education", "other"}:
            continue

        start_date = parse_date(match.group("start"), current_date)
        end_date = parse_date(match.group("end"), current_date)
        if not start_date or not end_date or end_date < start_date:
            continue

        description = line[:match.start()].strip(" ,-â€“â€”|")
        title = ""
        company = "Unknown"

        # Layout 1: "Job Title at Company" on the date line.
        if description:
            parts = title_company_split.split(description, maxsplit=1)
            if len(parts) == 2:
                title, company = parts[0].strip(), parts[1].strip()
            elif is_job_title(description):
                title = description

        # Layout 2: job title and company are on the line before the dates.
        if not title and index > 0:
            previous = lines[index - 1]
            parts = title_company_split.split(previous, maxsplit=1)
            if len(parts) == 2 and is_job_title(parts[0].strip()):
                title, company = parts[0].strip(), parts[1].strip()
            elif is_job_title(previous):
                title = previous

        # Layout 3: company, date range, job title (e.g. this sample PDF).
        if not title and index + 1 < len(lines):
            next_line = lines[index + 1]
            if is_job_title(next_line):
                title = next_line
                # The company is usually immediately before the date line.
                if index > 0:
                    candidate = lines[index - 1]
                    if not is_location(candidate) and candidate.lower() not in experience_headings:
                        company = candidate
                # If the preceding line is a location, look one more line up.
                if company == "Unknown" and index > 1:
                    candidate = lines[index - 2]
                    if not is_location(candidate) and candidate.lower() not in experience_headings:
                        company = candidate

        # Layout 4: company, location, title, date range.
        if not title and not description and index > 0:
            candidate_title = lines[index - 1]
            if is_job_title(candidate_title):
                title = candidate_title
                for candidate_index in range(index - 2, max(-1, index - 5), -1):
                    candidate = lines[candidate_index]
                    candidate_lower = candidate.lower()
                    if (
                        candidate_lower in experience_headings
                        or candidate_lower in education_headings
                        or candidate_lower in other_section_headings
                        or date_pattern.search(candidate)
                    ):
                        break
                    if is_location(candidate) or candidate.startswith(("-", "â€¢", "|")):
                        continue
                    if any(term in candidate_lower for term in education_terms):
                        continue
                    company = candidate
                    break

        if not title or not is_job_title(title):
            continue

        entries.append({
            "company": company,
            "job_title": title,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_months": duration_months(start_date, end_date),
        })

    # Remove duplicate entries while preserving order.
    unique_entries = {}
    for entry in entries:
        key = (
            entry["company"].lower(), entry["job_title"].lower(),
            entry["start_date"], entry["end_date"],
        )
        unique_entries[key] = entry
    return list(unique_entries.values())


def analyze_experience_timeline(entries):
    """Calculate total experience, employment gaps, and overlaps."""
    if not entries:
        return {
            "total_experience_months": 0,
            "total_experience_years": 0.0,
            "employment_gaps": [],
            "overlapping_roles": [],
        }

    def month_index(iso_date):
        parsed = date.fromisoformat(iso_date)
        return parsed.year * 12 + parsed.month - 1

    normalized = sorted(
        entries,
        key=lambda entry: month_index(entry["start_date"])
    )

    periods = []
    for entry in normalized:
        start = month_index(entry["start_date"])
        end = month_index(entry["end_date"])
        if end < start:
            continue
        periods.append((start, end, entry))

    if not periods:
        return {
            "total_experience_months": 0,
            "total_experience_years": 0.0,
            "employment_gaps": [],
            "overlapping_roles": [],
        }

    # Merge employment periods so overlapping jobs are not double-counted.
    merged = []
    for start, end, entry in periods:
        if not merged or start > merged[-1][1] + 1:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    total_months = sum(
        end - start + 1 for start, end in merged
    )

    gaps = []
    for previous, following in zip(merged, merged[1:]):
        gap_start = previous[1] + 1
        gap_end = following[0] - 1

        if gap_start <= gap_end:
            gaps.append({
                "start_date": date(
                    gap_start // 12, gap_start % 12 + 1, 1
                ).isoformat(),
                "end_date": date(
                    gap_end // 12, gap_end % 12 + 1, 1
                ).isoformat(),
                "duration_months": gap_end - gap_start + 1,
                })

    overlaps = []
    for index, (start, end, entry) in enumerate(periods):
        for other_start, other_end, other_entry in periods[index + 1:]:
            if other_start > end:
                break

            overlap_start = max(start, other_start)
            overlap_end = min(end, other_end)

            if overlap_start <= overlap_end:
                overlaps.append({
                    "role_1": entry["job_title"],
                    "company_1": entry["company"],
                    "role_2": other_entry["job_title"],
                    "company_2": other_entry["company"],
                    "overlap_months": overlap_end - overlap_start + 1,
                })

    return {
        "total_experience_months": total_months,
        "total_experience_years": round(total_months / 12, 2),
        "employment_gaps": gaps,
        "overlapping_roles": overlaps,
    }
