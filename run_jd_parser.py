from pathlib import Path

from parsers.jd_parser import build_job_profile, save_job_profile


def main():
    jd_path = Path("data/sample_jobs/python_developer_jd.txt")

    with open(jd_path, "r", encoding="utf-8") as file:
        jd_text = file.read()

    known_skills = [
        "Python",
        "Django",
        "REST API",
        "PostgreSQL",
        "Docker",
        "AWS"
    ]

    known_roles = [
        "Python Developer",
        "Python Engineer",
        "Backend Developer",
        "Software Engineer"
    ]

    profile = build_job_profile(
        jd_text,
        known_skills,
        known_roles,
        job_id="JOB-001"
    )

    output_path = Path("data/sample_jobs/python_developer_jd.json")

    save_job_profile(profile, output_path)

    print("\nJD parsing completed.")
    print(f"Input: {jd_path}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()

