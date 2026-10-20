from pathlib import Path

from parsers.resume_extractor import extract_resume
from parsers.resume_section_classifier import segment_extracted_resume
from utils.file_handler import save_json


def main():
    print("=== Zecpath AI - Resume Section Segmentation ===")

    file_path = input("Enter resume file path: ").strip()

    try:
        # Step 1: Extract and clean the resume
        extracted_resume = extract_resume(Path(file_path))

        # Step 2: Segment the extracted resume into sections
        segmented_resume = segment_extracted_resume(extracted_resume)

        # Step 3: Create output directory
        output_dir = Path("outputs/sectioned_resumes")
        output_dir.mkdir(parents=True, exist_ok=True)

        # Step 4: Create output file name
        file_name = Path(file_path).stem
        output_path = output_dir / f"{file_name}_sections.json"

        # Step 5: Save structured result
        save_json(segmented_resume, output_path)

        print("\nResume successfully segmented.")
        print(f"Output saved to: {output_path}")

    except Exception as error:
        print(f"\nError: {error}")


if __name__ == "__main__":
    main()