from pathlib import Path
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx


def extract_jd_text(file_path):
    """
    Extract raw text from a JD file.
    Supports TXT, PDF, and DOCX.
    """

    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"Job description not found: {file_path}")

    file_extension = path.suffix.lower()

    if file_extension == ".pdf":
        return extract_text_from_pdf(path)

    elif file_extension == ".docx":
        return extract_text_from_docx(path)

    elif file_extension == ".txt":
        with open(path, "r", encoding="utf-8") as file:
            return file.read()

    else:
        raise ValueError(
            "Unsupported file type. Only TXT, PDF, and DOCX are supported."
        )