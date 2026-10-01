from pathlib import Path

from parsers.docx_parser import extract_text_from_docx
from parsers.text_cleaner import clean_resume_text


def test_docx_text_extraction():
    docx_path = Path("data/sample_resumes/sample_resume.docx")

    raw_text = extract_text_from_docx(docx_path)
    cleaned_text = clean_resume_text(raw_text)

    print("\n========== RAW DOCX TEXT ==========")
    print(raw_text)

    print("\n========== CLEANED DOCX TEXT ==========")
    print(cleaned_text)

    assert raw_text.strip() != ""
    assert cleaned_text.strip() != ""