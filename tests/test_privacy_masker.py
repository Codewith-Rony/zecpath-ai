
import pytest

from parsers.privacy_masker import mask_personal_attributes


def test_masks_email():
    text = "Contact: rony@example.com"
    assert mask_personal_attributes(text) == "Contact: [EMAIL]"


def test_masks_phone_number():
    text = "Phone: +91 98765 43210"
    assert "[PHONE]" in mask_personal_attributes(text)
    assert "98765 43210" not in mask_personal_attributes(text)


def test_preserves_job_relevant_text():
    text = "Python Developer with SQL experience"
    assert mask_personal_attributes(text) == text


def test_masks_multiple_identifiers():
    text = "rony@example.com | +91 98765 43210"
    result = mask_personal_attributes(text)
    assert "[EMAIL]" in result
    assert "[PHONE]" in result


def test_rejects_non_string_input():
    with pytest.raises(ValueError):
        mask_personal_attributes(None)


def test_empty_text():
    assert mask_personal_attributes("") == ""
