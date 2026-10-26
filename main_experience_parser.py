
import json
import sys
from pathlib import Path

from parsers.resume_extractor import extract_resume
from parsers.experience_parser import (
    extract_experience,
    analyze_experience_timeline,
)
from scoring.experience_relevance import score_experience_relevance


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "experience"


def main():
    if len(sys.argv) < 3:
        print(
            'Usage: python main_experience_parser.py '
            '"path/to/resume.pdf" "Target Job Title"'
        )
        return

    resume_path = Path(sys.argv[1])
    target_role = sys.argv[2]

    if not resume_path.is_absolute():
        resume_path = Path.cwd() / resume_path

    if not resume_path.exists():
        print(f"Error: Resume not found: {resume_path}")
        return

    try:
        resume_data = extract_resume(str(resume_path))
        resume_text = resume_data.get("cleaned_text", "")

        if not resume_text.strip():
            print("Error: No readable text found in the resume.")
            return

        entries = extract_experience(resume_text)
        timeline = analyze_experience_timeline(entries)
        relevance = score_experience_relevance(
            entries, target_role
        )

        output = {
            "file_name": resume_path.name,
            "target_role": target_role,
            "experience_entries": entries,
            "timeline_analysis": timeline,
            "relevance_analysis": relevance,
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{resume_path.stem}_experience.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(output, file, indent=4, ensure_ascii=False)

        print(f"Experience entries extracted: {len(entries)}")
        print(
            "Total experience: "
            f"{timeline['total_experience_years']} years"
        )
        print(f"Structured output saved to: {output_path}")

    except Exception as error:
        print(f"Error processing resume: {error}")


if __name__ == "__main__":
    main()
