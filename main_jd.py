from pathlib import Path

from parsers.jd_extractor import extract_jd_text
from parsers.jd_parser import build_job_profile, save_job_profile


def main():
    jd_path = input("Enter job description file path: ").strip()

    path = Path(jd_path)

    try:
        raw_text = extract_jd_text(path)

        known_skills = [
            "Python",
            "Java",
            "JavaScript",
            "TypeScript",
            "C",
            "C++",
            "C#",
            "HTML",
            "CSS",
            "React",
            "Node.js",
            "Express.js",
            "Django",
            "Flask",
            "FastAPI",
            "REST API",
            "PostgreSQL",
            "MySQL",
            "MongoDB",
            "Docker",
            "AWS",
            "Azure",
            "Git",
            "GitHub",
            "Flutter",
            "Machine Learning",
            "Deep Learning",
            "TensorFlow",
            "PyTorch"
        ]

        known_roles = [
            "Python Developer",
            "Python Engineer",
            "Java Developer",
            "Java Engineer",
            "Backend Developer",
            "Backend Engineer",
            "Frontend Developer",
            "Front End Developer",
            "Full Stack Developer",
            "Full-Stack Developer",
            "Software Engineer",
            "Software Developer",
            "Data Scientist",
            "Machine Learning Engineer",
            "DevOps Engineer"
        ]

        profile = build_job_profile(
            raw_text,
            known_skills,
            known_roles
        )

        output_directory = Path("outputs/jd")
        output_directory.mkdir(parents=True, exist_ok=True)

        output_path = output_directory / f"{path.stem}_structured.json"

        save_job_profile(profile, output_path)

        print("\nJD parsing completed successfully.")
        print(f"Input file:  {path}")
        print(f"Output file: {output_path}")

    except (FileNotFoundError, ValueError) as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()