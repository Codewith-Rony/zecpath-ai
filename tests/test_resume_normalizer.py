
import pytest

from parsers.resume_normalizer import normalize_resume_text


def test_normalizes_whitespace():
    text = "Python    Developer   \n  SQL   "
    assert normalize_resume_text(text) == "Python Developer\nSQL"


def test_normalizes_line_endings():
    assert normalize_resume_text("Python\r\nSQL\rJava") == (
        "Python\nSQL\nJava"
    )


def test_preserves_section_boundaries():
    text = "SKILLS\n\n\nPython\n\n\nEXPERIENCE"
    assert normalize_resume_text(text) == (
        "SKILLS\n\nPython\n\nEXPERIENCE"
    )


def test_normalizes_unicode():
    assert normalize_resume_text("ＡＩ") == "AI"


def test_rejects_non_string_input():
    with pytest.raises(ValueError):
        normalize_resume_text(None)


def test_empty_text_returns_empty_string():
    assert normalize_resume_text(" \n  ") == ""
