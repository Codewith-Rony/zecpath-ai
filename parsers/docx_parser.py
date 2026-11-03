from pathlib import Path
from docx import Document


def extract_text_from_docx(file_path):
    """Extract text from a DOCX file with merged-cell deduplication and safety checks."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"DOCX file not found: {file_path}")
    if path.stat().st_size == 0:
        return ""

    try:
        document = Document(str(path))
    except Exception as exc:
        raise ValueError(f"Corrupt or invalid DOCX file ({path.name}): {exc}") from exc

    text_parts = []

    # Extract normal paragraphs
    for paragraph in document.paragraphs:
        if paragraph.text.strip():
            text_parts.append(paragraph.text)

    # Extract text from tables with merged-cell deduplication
    for table in document.tables:
        seen_cells = set()
        for row in table.rows:
            row_text = []
            for cell in row.cells:
                # Deduplicate merged cells sharing the same underlying XML element
                tc = getattr(cell, "_tc", None)
                if tc is not None:
                    if tc in seen_cells:
                        continue
                    seen_cells.add(tc)

                cell_text = cell.text.strip()
                if cell_text:
                    row_text.append(cell_text)

            if row_text:
                text_parts.append(" | ".join(row_text))

    return "\n".join(text_parts)
