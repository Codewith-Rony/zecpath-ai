
"""Normalize resume text into a consistent, privacy-conscious format."""

import re
import unicodedata


def normalize_resume_text(text):
    """Standardize whitespace and Unicode while preserving meaningful content."""
    if not isinstance(text, str):
        raise ValueError("Resume text must be a string.")

    # Normalize equivalent Unicode representations.
    text = unicodedata.normalize("NFKC", text)

    # Standardize line endings and remove invisible control characters.
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = "".join(
        char for char in text
        if char in "\n\t" or unicodedata.category(char) != "Cc"
    )

    # Normalize horizontal whitespace without flattening sections.
    lines = [
        re.sub(r"[^\S\n]+", " ", line).strip()
        for line in text.split("\n")
    ]

    # Preserve section boundaries while removing excessive blank lines.
    normalized = "\n".join(lines)
    normalized = re.sub(r"\n{3,}", "\n\n", normalized)

    return normalized.strip()
