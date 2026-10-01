from pathlib import Path

from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.text_cleaner import clean_resume_text


def extract_resume(file_path):
    """
    Extract and clean text from a PDF or DOCX resume.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Resume not found: {file_path}")

    file_extension = path.suffix.lower()

    if file_extension == ".pdf":
        raw_text = extract_text_from_pdf(path)

    elif file_extension == ".docx":
        raw_text = extract_text_from_docx(path)

    else:
        raise ValueError(
            "Unsupported file type. Only PDF and DOCX are supported."
        )

    cleaned_text = clean_resume_text(raw_text)

    return {
        "file_name": path.name,
        "file_type": file_extension,
        "raw_text": raw_text,
        "cleaned_text": cleaned_text
    }