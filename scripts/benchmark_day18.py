"""
Day 18 ATS Performance & Memory Benchmark Script.

Measures:
1. PDF text extraction (time + peak memory)
2. DOCX text extraction (time + peak memory)
3. End-to-end ATS scoring across 48 pairs (time + peak memory)
4. Micro-benchmarks for critical components (skill dictionary, SemanticMatcher init, JD parsing)

Usage:
    python scripts/benchmark_day18.py [--output-json <path>]
"""

import argparse
import gc
import json
import os
import sys
import time
import tracemalloc
from pathlib import Path

# Add project root to sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from parsers.skill_extractor import load_skill_dictionary
from parsers.jd_parser import build_job_profile
from parsers.jd_extractor import extract_jd_text
from scoring.semantic_matcher import SemanticMatcher
from scoring.skill_matcher import KNOWN_ROLES
from main_ats_scorer import generate_candidate_report, _known_skills


def discover_files():
    testing_dir = ROOT / "data" / "testing"
    resumes_dir = testing_dir / "resumes"
    jds_dir = testing_dir / "job_descriptions"

    pdf_resumes = sorted(resumes_dir.rglob("*.pdf"))
    docx_resumes = sorted(resumes_dir.rglob("*.docx"))
    all_resumes = sorted(pdf_resumes + docx_resumes)
    jds = sorted(jds_dir.glob("JD*.txt"))

    return {
        "pdf_resumes": pdf_resumes,
        "docx_resumes": docx_resumes,
        "all_resumes": all_resumes,
        "jds": jds,
    }


def benchmark_pdf_extraction(pdf_paths, runs=3):
    if not pdf_paths:
        return {"error": "No PDF resumes found"}

    gc.collect()
    tracemalloc.start()
    start_time = time.perf_counter()

    for _ in range(runs):
        for path in pdf_paths:
            _ = extract_text_from_pdf(str(path))

    duration = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_extractions = len(pdf_paths) * runs
    return {
        "files_count": len(pdf_paths),
        "runs": runs,
        "total_extractions": total_extractions,
        "total_time_seconds": round(duration, 4),
        "avg_time_per_file_ms": round((duration / total_extractions) * 1000, 2),
        "peak_memory_kb": round(peak_mem / 1024, 2),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
    }


def benchmark_docx_extraction(docx_paths, runs=3):
    if not docx_paths:
        return {"error": "No DOCX resumes found"}

    gc.collect()
    tracemalloc.start()
    start_time = time.perf_counter()

    for _ in range(runs):
        for path in docx_paths:
            _ = extract_text_from_docx(str(path))

    duration = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    total_extractions = len(docx_paths) * runs
    return {
        "files_count": len(docx_paths),
        "runs": runs,
        "total_extractions": total_extractions,
        "total_time_seconds": round(duration, 4),
        "avg_time_per_file_ms": round((duration / total_extractions) * 1000, 2),
        "peak_memory_kb": round(peak_mem / 1024, 2),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
    }


def benchmark_complete_ats_scoring(resumes, jds):
    if not resumes or not jds:
        return {"error": "Missing resumes or job descriptions"}

    gc.collect()
    tracemalloc.start()
    start_time = time.perf_counter()

    scored_count = 0
    for resume in resumes:
        for jd in jds:
            report = generate_candidate_report(resume, jd)
            assert report["ats_score"] is not None or "ats_score" in report
            scored_count += 1

    duration = time.perf_counter() - start_time
    current_mem, peak_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "candidate_pairs_count": scored_count,
        "total_time_seconds": round(duration, 4),
        "avg_time_per_pair_ms": round((duration / scored_count) * 1000, 2),
        "peak_memory_kb": round(peak_mem / 1024, 2),
        "peak_memory_mb": round(peak_mem / (1024 * 1024), 3),
    }


def benchmark_micro():
    # 1. Skill dictionary loading (100 calls)
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    for _ in range(100):
        _ = load_skill_dictionary()
    skill_dict_time = time.perf_counter() - t0
    _, peak_skill = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 2. SemanticMatcher initialization (100 instances)
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    for _ in range(100):
        matcher = SemanticMatcher()
        _ = matcher.mode
    matcher_init_time = time.perf_counter() - t0
    _, peak_matcher = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    # 3. Job profile parsing (20 calls)
    jd_sample_path = ROOT / "data" / "testing" / "job_descriptions" / "JD01_junior_python_developer.txt"
    jd_sample_text = extract_jd_text(str(jd_sample_path)) if jd_sample_path.is_file() else ""
    gc.collect()
    tracemalloc.start()
    t0 = time.perf_counter()
    for _ in range(20):
        _ = build_job_profile(jd_sample_text, _known_skills(), KNOWN_ROLES)
    jd_parse_time = time.perf_counter() - t0
    _, peak_jd = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    return {
        "skill_dict_100_calls_seconds": round(skill_dict_time, 4),
        "skill_dict_peak_kb": round(peak_skill / 1024, 2),
        "matcher_init_100_calls_seconds": round(matcher_init_time, 4),
        "matcher_init_peak_kb": round(peak_matcher / 1024, 2),
        "jd_parse_20_calls_seconds": round(jd_parse_time, 4),
        "jd_parse_peak_kb": round(peak_jd / 1024, 2),
    }


def main():
    parser = argparse.ArgumentParser(description="Run Day 18 ATS performance benchmarks.")
    parser.add_argument("--output-json", help="Path to write JSON benchmark metrics", default=None)
    args = parser.parse_args()

    files = discover_files()
    print("=" * 60)
    print("Zecpath AI Day 18 Benchmark")
    print("=" * 60)
    print(f"Found {len(files['pdf_resumes'])} PDF resumes, {len(files['docx_resumes'])} DOCX resumes, {len(files['jds'])} JDs.")
    print(f"Total candidate pairs to score: {len(files['all_resumes']) * len(files['jds'])}")
    print("-" * 60)

    print("1. Benchmarking PDF Extraction...")
    pdf_results = benchmark_pdf_extraction(files["pdf_resumes"])
    print(f"   PDF Extractions: {pdf_results['total_extractions']} runs")
    print(f"   Total Time: {pdf_results['total_time_seconds']} s | Avg: {pdf_results['avg_time_per_file_ms']} ms/file")
    print(f"   Peak Traced Memory: {pdf_results['peak_memory_mb']} MB ({pdf_results['peak_memory_kb']} KB)")

    print("-" * 60)
    print("2. Benchmarking DOCX Extraction...")
    docx_results = benchmark_docx_extraction(files["docx_resumes"])
    print(f"   DOCX Extractions: {docx_results['total_extractions']} runs")
    print(f"   Total Time: {docx_results['total_time_seconds']} s | Avg: {docx_results['avg_time_per_file_ms']} ms/file")
    print(f"   Peak Traced Memory: {docx_results['peak_memory_mb']} MB ({docx_results['peak_memory_kb']} KB)")

    print("-" * 60)
    print("3. Benchmarking Complete ATS Scoring (48 pairs)...")
    scoring_results = benchmark_complete_ats_scoring(files["all_resumes"], files["jds"])
    print(f"   Total Pairs Scored: {scoring_results['candidate_pairs_count']}")
    print(f"   Total Time: {scoring_results['total_time_seconds']} s | Avg: {scoring_results['avg_time_per_pair_ms']} ms/pair")
    print(f"   Peak Traced Memory: {scoring_results['peak_memory_mb']} MB ({scoring_results['peak_memory_kb']} KB)")

    print("-" * 60)
    print("4. Benchmarking Component Micro-operations...")
    micro_results = benchmark_micro()
    print(f"   Skill Dict Load (100 calls): {micro_results['skill_dict_100_calls_seconds']} s (Peak: {micro_results['skill_dict_peak_kb']} KB)")
    print(f"   SemanticMatcher Init (100 calls): {micro_results['matcher_init_100_calls_seconds']} s (Peak: {micro_results['matcher_init_peak_kb']} KB)")
    print(f"   JD Profile Parse (20 calls): {micro_results['jd_parse_20_calls_seconds']} s (Peak: {micro_results['jd_parse_peak_kb']} KB)")
    print("=" * 60)

    all_metrics = {
        "pdf_extraction": pdf_results,
        "docx_extraction": docx_results,
        "complete_ats_scoring": scoring_results,
        "micro_benchmarks": micro_results,
    }

    if args.output_json:
        out_path = Path(args.output_json).resolve()
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(json.dumps(all_metrics, indent=2), encoding="utf-8")
        print(f"Benchmark results saved to: {out_path}")

    return all_metrics


if __name__ == "__main__":
    main()

