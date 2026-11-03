from pathlib import Path

try:
    import pymupdf as fitz
except ImportError:
    import fitz


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file with resource cleanup and safety checks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"PDF file not found: {file_path}")
    if path.stat().st_size == 0:
        return ""

    try:
        with fitz.open(str(path)) as document:
            pages = [page.get_text() for page in document]
            return "".join(pages)
    except Exception as exc:
        raise ValueError(f"Corrupt or invalid PDF file ({path.name}): {exc}") from exc
