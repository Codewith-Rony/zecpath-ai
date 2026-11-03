"""Day 18 Optimization & Robustness Regression Tests."""

import json
import os
from pathlib import Path
import pytest
from docx import Document

from parsers.skill_extractor import (
    load_skill_dictionary,
    clear_skill_dictionary_cache,
)
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.text_cleaner import clean_resume_text
from parsers.jd_parser import build_job_profile
from scoring.skill_matcher import score_skill_match, KNOWN_ROLES
from scoring.semantic_matcher import SemanticMatcher
from main_ats_scorer import generate_candidate_report, _known_skills

ROOT = Path(__file__).resolve().parents[1]


def test_skill_dict_cache_isolation():
    """Verify that mutating the dictionary returned by load_skill_dictionary does not leak into cache."""
    clear_skill_dictionary_cache()
    dict1 = load_skill_dictionary()
    assert "technical" in dict1
    assert "Python" in dict1["technical"]

    # Mutate dict1
    dict1["technical"]["Python"] = ["MUTATED_SYNONYM"]
    dict1["technical"]["__NEW_SKILL__"] = ["test"]

    # Load dict2 and verify it is untouched
    dict2 = load_skill_dictionary()
    assert dict2["technical"]["Python"] != ["MUTATED_SYNONYM"]
    assert "__NEW_SKILL__" not in dict2["technical"]


def test_skill_dict_cache_invalidation(tmp_path):
    """Verify that modifying the dictionary file on disk invalidates the cache and reloads deterministically."""
    clear_skill_dictionary_cache()
    temp_dict = tmp_path / "skills.json"
    temp_dict.write_text(json.dumps({"technical": {"Python": []}}), encoding="utf-8")

    loaded1 = load_skill_dictionary(temp_dict)
    assert "Python" in loaded1["technical"]
    assert "Rust" not in loaded1["technical"]

    # Deterministically advance mtime using os.utime to eliminate filesystem granularity dependency
    initial_mtime = temp_dict.stat().st_mtime
    new_mtime = initial_mtime + 10.0
    temp_dict.write_text(json.dumps({"technical": {"Rust": []}}), encoding="utf-8")
    os.utime(temp_dict, (new_mtime, new_mtime))

    loaded2 = load_skill_dictionary(temp_dict)
    assert "Rust" in loaded2["technical"]
    assert "Python" not in loaded2["technical"]

    clear_skill_dictionary_cache()


def test_docx_merged_cell_deduplication(tmp_path):
    """Verify that merged cells are deduplicated while separate cells with identical text are preserved."""
    doc = Document()

    # Table 1: Merged cells (Row 0: Cell 0 and Cell 1 merged)
    table_merged = doc.add_table(rows=1, cols=2)
    cell_a = table_merged.cell(0, 0)
    cell_b = table_merged.cell(0, 1)
    cell_a.merge(cell_b)
    cell_a.text = "Lead Architect"

    # Table 2: Separate distinct cells with identical text
    table_distinct = doc.add_table(rows=1, cols=2)
    table_distinct.cell(0, 0).text = "Python"
    table_distinct.cell(0, 1).text = "Python"

    doc_path = tmp_path / "test_tables.docx"
    doc.save(str(doc_path))

    extracted = extract_text_from_docx(doc_path)
    lines = extracted.splitlines()

    # In table 1, merged cell text should appear only once
    assert "Lead Architect" in lines[0]
    assert "Lead Architect | Lead Architect" not in lines[0]

    # In table 2, distinct cells with identical text must BOTH be preserved
    assert "Python | Python" in lines[1]


def test_empty_and_corrupt_pdf_handling(tmp_path):
    """Verify empty and corrupt PDFs are handled defensively with clear exceptions."""
    # 1. 0-byte PDF
    empty_pdf = tmp_path / "empty.pdf"
    empty_pdf.write_bytes(b"")
    assert extract_text_from_pdf(empty_pdf) == ""

    # 2. Corrupt PDF
    corrupt_pdf = tmp_path / "corrupt.pdf"
    corrupt_pdf.write_bytes(b"Not a valid PDF header at all")
    with pytest.raises(ValueError, match="Corrupt or invalid PDF"):
        extract_text_from_pdf(corrupt_pdf)

    # 3. Missing PDF
    with pytest.raises(FileNotFoundError):
        extract_text_from_pdf(tmp_path / "nonexistent.pdf")


def test_empty_and_corrupt_docx_handling(tmp_path):
    """Verify empty and corrupt DOCX files are handled defensively with clear exceptions."""
    # 1. 0-byte DOCX
    empty_docx = tmp_path / "empty.docx"
    empty_docx.write_bytes(b"")
    assert extract_text_from_docx(empty_docx) == ""

    # 2. Corrupt DOCX
    corrupt_docx = tmp_path / "corrupt.docx"
    corrupt_docx.write_bytes(b"PK\x03\x04 corrupt zip archive data")
    with pytest.raises(ValueError, match="Corrupt or invalid DOCX"):
        extract_text_from_docx(corrupt_docx)

    # 3. Missing DOCX
    with pytest.raises(FileNotFoundError):
        extract_text_from_docx(tmp_path / "nonexistent.docx")


def test_noisy_text_cleaning():
    """Verify that text cleaning handles non-printable control characters, null bytes, and excessive spaces."""
    noisy = "John\x00 Doe\x0c\n• Experience\x08 in Python    and   Django\x0b.\n● Lead Developer"
    cleaned = clean_resume_text(noisy)

    assert "\x00" not in cleaned
    assert "\x0c" not in cleaned
    assert "\x08" not in cleaned
    assert "John Doe" in cleaned
    assert "Experience in Python and Django." in cleaned
    assert "- Lead Developer" in cleaned


def test_score_skill_match_backward_compatibility():
    """Verify score_skill_match produces identical results whether job_profile is passed or inferred."""
    resume_text = "Software engineer skilled in Python, Flask, Docker, and PostgreSQL with 3 years experience."
    jd_text = "Role: Python Developer\nRequirements:\n- Python\n- Flask\n- PostgreSQL\nPreferred:\n- Docker"

    # Call 1: Without job_profile
    res1 = score_skill_match(resume_text, jd_text)

    # Call 2: With precomputed job_profile
    profile = build_job_profile(jd_text, _known_skills(), KNOWN_ROLES)
    res2 = score_skill_match(resume_text, jd_text, job_profile=profile)

    assert res1["skill_match_score"] == res2["skill_match_score"]
    assert res1["required_skills"] == res2["required_skills"]
    assert res1["matched_required_skills"] == res2["matched_required_skills"]
    assert res1["preferred_skills"] == res2["preferred_skills"]
    assert res1["matched_preferred_skills"] == res2["matched_preferred_skills"]


def test_semantic_matcher_caching_and_idempotence():
    """Verify SemanticMatcher caching is deterministic and reproducible."""
    matcher = SemanticMatcher()
    t1 = "Backend developer working with Python, Django, REST APIs, and PostgreSQL database."
    t2 = "Looking for Senior Python Developer with strong Django, API development, and PostgreSQL skills."

    score1 = matcher.similarity(t1, t2)
    score2 = matcher.similarity(t1, t2)

    assert score1 == score2
    assert score1 > 0.0


def test_repeated_candidate_scoring_idempotence():
    """Verify that scoring the same candidate multiple times produces identical reports without silent skips."""
    resume_path = ROOT / "data" / "testing" / "resumes" / "tech_fresher" / "T-F01_aarav_menon.pdf"
    jd_path = ROOT / "data" / "testing" / "job_descriptions" / "JD01_junior_python_developer.txt"

    # Explicit assertions ensure test files are present and cannot silently pass
    assert resume_path.is_file(), f"Required test resume file missing: {resume_path}"
    assert jd_path.is_file(), f"Required test job description file missing: {jd_path}"

    report1 = generate_candidate_report(resume_path, jd_path)
    report2 = generate_candidate_report(resume_path, jd_path)

    assert report1["ats_score"] == report2["ats_score"]
    assert report1["coverage_percentage"] == report2["coverage_percentage"]
    assert report1["component_scores"] == report2["component_scores"]
    assert report1["missing_components"] == report2["missing_components"]
