from pathlib import Path

from parsers.resume_extractor import extract_resume


def test_pdf_resume_extraction():
    pdf_path = Path("data/sample_resumes/sample_resume.pdf")

    result = extract_resume(pdf_path)

    assert result["file_name"] == "sample_resume.pdf"
    assert result["file_type"] == ".pdf"
    assert result["raw_text"].strip() != ""
    assert result["cleaned_text"].strip() != ""

    print(result)


def test_docx_resume_extraction():
    docx_path = Path("data/sample_resumes/sample_resume.docx")

    result = extract_resume(docx_path)

    assert result["file_name"] == "sample_resume.docx"
    assert result["file_type"] == ".docx"
    assert result["raw_text"].strip() != ""
    assert result["cleaned_text"].strip() != ""
    print(result)