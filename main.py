from pathlib import Path

from parsers.resume_extractor import extract_resume
from utils.file_handler import save_json


def main():
    resume_path = input("Enter resume file path: ").strip()

    result = extract_resume(resume_path)

    output_directory = Path("outputs")
    output_directory.mkdir(exist_ok=True)

    file_name = Path(resume_path).stem
    output_path = output_directory / f"{file_name}_extracted.json"

    save_json(result, output_path)

    print("\nResume extraction completed.")
    print(f"Input file: {resume_path}")
    print(f"Output file: {output_path}")


if __name__ == "__main__":
    main()