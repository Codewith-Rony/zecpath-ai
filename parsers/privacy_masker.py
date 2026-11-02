
"""Mask common personal identifiers in text before appropriate evaluation."""

import re


EMAIL_PATTERN = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+?\d[\d\s().-]{7,}\d)(?!\w)"
)


def mask_personal_attributes(text):
    """Mask common email and phone identifiers while preserving other text."""
    if not isinstance(text, str):
        raise ValueError("Text must be a string.")

    text = EMAIL_PATTERN.sub("[EMAIL]", text)
    text = PHONE_PATTERN.sub("[PHONE]", text)

    return text
