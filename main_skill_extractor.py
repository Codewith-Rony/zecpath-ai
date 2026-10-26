
import json
import sys
from pathlib import Path

from parsers.resume_extractor import extract_resume
from parsers.skill_extractor import extract_skills


PROJECT_ROOT = Path(__file__).resolve().parent
OUTPUT_DIR = PROJECT_ROOT / "outputs" / "extracted_skills"


def main():
    if len(sys.argv) < 2:
        print(
            "Usage: python main_skill_extractor.py "
            '"path/to/resume.pdf"'
        )
        return

    resume_path = Path(sys.argv[1])

    if not resume_path.is_absolute():
        resume_path = Path.cwd() / resume_path

    if not resume_path.exists():
        print(f"Error: Resume file not found: {resume_path}")
        return

    try:
        resume_data = extract_resume(str(resume_path))
        resume_text = resume_data.get("cleaned_text", "")

        if not resume_text.strip():
            print("Error: No readable text found in the resume.")
            return

        skill_result = extract_skills(resume_text)

        output = {
            "file_name": resume_path.name,
            "total_skills": skill_result["total_skills"],
            "skills": skill_result["skills"]
        }

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        output_path = OUTPUT_DIR / f"{resume_path.stem}_skills.json"

        with output_path.open("w", encoding="utf-8") as file:
            json.dump(output, file, indent=4, ensure_ascii=False)

        print(f"Skills extracted: {skill_result['total_skills']}")
        print(f"Structured output saved to: {output_path}")

    except Exception as error:
        print(f"Error processing resume: {error}")


if __name__ == "__main__":
    main()
