
import argparse
import json
from pathlib import Path

from parsers.resume_extractor import extract_resume
from parsers.education_parser import extract_academic_profile
from scoring.education_relevance import score_education_relevance


def main():
    parser = argparse.ArgumentParser(
        description="Extract education and certifications from a resume."
    )

    parser.add_argument(
        "resume_path",
        help="Path to the resume PDF or supported document."
    )

    parser.add_argument(
        "--role",
        default="Python Developer",
        help="Target job role (default: Python Developer)."
    )

    args = parser.parse_args()

    resume_path = Path(args.resume_path)

    if not resume_path.is_file():
        parser.error(f"Resume file not found: {resume_path}")

    resume_data = extract_resume(str(resume_path))
    resume_text = resume_data["cleaned_text"]

    academic_profile = extract_academic_profile(resume_text)

    education_relevance = score_education_relevance(
        academic_profile,
        args.role
    )

    result = {
        "file_name": resume_data["file_name"],
        "target_role": args.role,
        "academic_profile": academic_profile,
        "education_relevance": education_relevance
    }

    output_dir = Path("outputs") / "education"
    output_dir.mkdir(parents=True, exist_ok=True)

    output_path = output_dir / f"{resume_path.stem}_education.json"

    with output_path.open("w", encoding="utf-8") as file:
        json.dump(result, file, indent=4, ensure_ascii=False)

    print(json.dumps(result, indent=4, ensure_ascii=False))
    print(f"\nOutput saved to: {output_path}")


if __name__ == "__main__":
    main()
