from pathlib import Path

from parsers.pdf_parser import extract_text_from_pdf
from parsers.text_cleaner import clean_resume_text


def test_pdf_text_extraction():
    pdf_path = Path("data/sample_resumes/sample_resume.pdf")

    raw_text = extract_text_from_pdf(pdf_path)

    cleaned_text = clean_resume_text(raw_text)

    print("\n========== RAW TEXT ==========")
    print(raw_text)

    print("\n========== CLEANED TEXT ==========")
    print(cleaned_text)

    assert raw_text.strip() != ""
    assert cleaned_text.strip() != ""