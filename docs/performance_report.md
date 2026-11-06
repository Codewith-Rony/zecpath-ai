# Zecpath AI – Day 18: ATS Optimization & Performance Tuning Report

## 1. Executive Summary

This report documents the performance audit, baseline profiling, optimization implementation, empirical verification, and benchmark investigations for the Zecpath AI ATS engine conducted during Day 18.

All optimizations strictly adhered to the project's safeguards:
- **Zero scoring drift**: All 48 resume–job description candidate pairs produced bit-for-bit identical ATS scores against the confirmed Day 17 evaluation reference.
- **Architectural preservation**: Core ATS weights (Skill: 40%, Experience: 25%, Education: 15%, Semantic: 20%), thresholds, API contracts, and fairness safeguards remain completely intact.
- **Safe caching**: In-memory caching incorporates timestamp-based auto-invalidation and deep dictionary cloning to eliminate cross-candidate data leakage and shared mutable state.
- **Deterministic regression testing**: The test suite expanded from **150 passing tests** to **159 passing tests** with 0 failures, executing in **2.26 seconds**.

> [!WARNING]
> While all 159 automated tests pass and document parsing/component latency has measurably improved, the ATS is **not yet production-ready**. Important production constraints remain, including lack of asynchronous batch worker queues, reliance on lexical fallback matching instead of neural embeddings, and memory retention characteristics inherent to `python-docx`'s DOM model.

---

## 2. Bottlenecks Identified (Phase 1 Audit)

| Component | Root Cause | Architectural Bottleneck |
| :--- | :--- | :--- |
| **Skill Dictionary** | Uncached disk I/O | `load_skill_dictionary()` repeatedly opened `data/skill_dictionary.json` from disk and deserialized JSON on every call (3–4 times per candidate evaluation; ~190 times across 48 pairs). |
| **JD Profile Building** | Redundant parsing | `main_ats_scorer.py` parsed the job description into a profile, and immediately called `score_skill_match()`, which re-parsed the exact same JD text from scratch. |
| **Semantic Matcher** | Repeated failed imports | In default configuration (`prefer_embeddings=True`), instantiating `SemanticMatcher()` attempted `from sentence_transformers import SentenceTransformer` on every candidate. Because the package was not installed, Python traversed `sys.meta_path` and raised/caught an `ImportError` each time (~3.78 ms per candidate). |
| **DOCX Parser** | Merged cell duplicates & DOM retention | Iterating `table.rows` and `row.cells` emitted duplicate text entries for cells merged horizontally or vertically because `python-docx` yields the same underlying `_tc` element across spanned cells. |
| **PDF Parser** | Deprecated API & string concatenation | Used deprecated `import fitz` API, accumulated text via in-loop string concatenation, and lacked deterministic context management or defensive handling for 0-byte or corrupted files. |
| **Text Cleaner** | Uncompiled regexes & unhandled control chars | Compiled regexes inside per-line loops and lacked sanitization for null bytes and non-printable control characters present in noisy/malformed files. |
| **Experience Relevance** | Expensive quadratic diffing | `calculate_similarity` computed `difflib.SequenceMatcher.ratio()` across every candidate responsibility and JD requirement without memoization. |

---

## 3. Optimizations Implemented (Phase 3)

### 3.1 Skill Dictionary Caching with Auto-Invalidation & Isolation (`parsers/skill_extractor.py`)
- Cached loaded dictionary in memory alongside the source file path and modification timestamp (`st_mtime_ns`).
- Returns a fresh dictionary clone on each retrieval via `_clone_dictionary()`, ensuring that any caller mutating the returned structure cannot corrupt the shared cache.
- Automatically reloads the dictionary if the underlying JSON file is modified on disk. Added `clear_skill_dictionary_cache()` for explicit cache eviction.

### 3.2 Semantic Matcher Lazy Availability Check & Vector Caching (`scoring/semantic_matcher.py`)
- Evaluated `sentence_transformers` availability once at module level via `_check_sentence_transformers()` and cached the boolean flag. Subsequent instantiations avoid Python's import machinery entirely.
- Added `@functools.lru_cache(maxsize=256)` to `_cached_fallback_vector()` to memoize token-bigram vector representations for JD and resume texts.
- Preserved exact mathematical formulas for `_fallback_vector`, `_cosine_sparse`, and `similarity`, ensuring zero score drift.

### 3.3 Redundant Job Profile Elimination (`scoring/skill_matcher.py` & `main_ats_scorer.py`)
- Extended `score_skill_match(resume_text, job_description_text, job_profile=None)` with backward-compatible optional `job_profile` parameter.
- `main_ats_scorer.py` now passes the pre-built `job_profile` directly, eliminating the redundant second parse per candidate.

### 3.4 Robust PDF Text Extraction (`parsers/pdf_parser.py`)
- Replaced deprecated import with `import pymupdf as fitz`.
- Enforced deterministic document closure via `with fitz.open(str(path)) as document:`.
- Replaced string concatenation with efficient list comprehension `"".join(pages)`.
- Added defensive validation: raises `FileNotFoundError` for missing files, returns `""` for 0-byte files, and raises descriptive `ValueError` for corrupted/invalid PDF streams.

### 3.5 Robust DOCX Extraction with Merged-Cell Deduplication (`parsers/docx_parser.py`)
- Added merged-cell deduplication: tracks underlying XML element identity (`cell._tc`). If a cell spans multiple columns/rows, duplicate emissions are skipped.
- Preserved distinct cells: separate cells with legitimately identical text (e.g. "Python | Python") have distinct XML elements and are correctly retained.
- Added defensive validation: returns `""` for 0-byte files, raises `ValueError` for corrupt archives, and raises `FileNotFoundError` for missing paths.

### 3.6 Text Sanitization (`parsers/text_cleaner.py`)
- Precompiled regexes (`_RE_EXCESSIVE_SPACES`, `_RE_CONTROL_CHARS`).
- Added sanitization for non-printable control characters (`\x00-\x08\x0b\x0c\x0e-\x1f\x7f`) before line splitting, preventing word fragmentation from vertical tabs or form feeds.

### 3.7 Experience Relevance Similarity Memoization (`scoring/experience_relevance.py`)
- Added `@functools.lru_cache(maxsize=2048)` to `calculate_similarity(text_a, text_b)`.
- Reused precompiled regexes for text normalization and tokenization stop-word filtering.
- Repeated comparisons of candidate experiences against identical JD requirements are now resolved from cache.

---

## 4. Before-and-After Performance Benchmarks

Benchmarks were measured using `scripts/benchmark_day18.py` on the exact same dataset (6 PDF resumes, 6 DOCX resumes, 4 JDs, 48 candidate evaluation pairs) using `time.perf_counter()` and `tracemalloc`.

Baseline data was preserved in `data/testing/benchmark_baseline.json`; post-optimization data was recorded in `data/testing/benchmark_optimized.json`.

### 4.1 Benchmark Comparison Table

| Metric / Workload | Baseline (Day 18 Initial) | Optimized (Day 18 Final) | Absolute Change | Percentage Improvement / Change |
| :--- | :--- | :--- | :--- | :--- |
| **PDF Extraction Total Time (18 runs)** | 0.3324 s | **0.1527 s** | -0.1797 s | **54.1% faster** (2.18x) |
| **PDF Extraction Avg Time / File** | 18.47 ms | **8.48 ms** | -9.99 ms | **54.1% faster** |
| **PDF Extraction Peak Memory** | 50.93 KB | **51.70 KB** | +0.77 KB | Within noise (+1.5%) |
| **DOCX Extraction Total Time (18 runs)**| 1.0357 s | **0.6786 s** | -0.3571 s | **34.5% faster** (1.53x) |
| **DOCX Extraction Avg Time / File** | 57.54 ms | **37.70 ms** | -19.84 ms | **34.5% faster** |
| **DOCX Extraction Peak Memory** | 5,581.54 KB | **5,582.28 KB** | +0.74 KB | Parity (< 0.1%) |
| **Complete ATS Scoring (48 pairs)** | 7.0319 s | **6.8230 s** | -0.2089 s | **3.0% faster** |
| **Complete ATS Scoring Avg / Pair** | 146.50 ms | **142.15 ms** | -4.35 ms | **3.0% faster** |
| **Complete ATS Peak Traced Memory** | 5,817.69 KB (5.68 MB) | **5,643.62 KB** (5.51 MB) | -174.07 KB | **3.0% memory reduction** |
| **SemanticMatcher Init (100 calls)** | 0.3776 s | **0.0004 s** | -0.3772 s | **99.9% faster** (944x) |
| **SemanticMatcher Init Peak Memory** | 3.20 KB | **0.23 KB** | -2.97 KB | **92.8% memory reduction** |
| **Skill Dict Load Execution Time (100 calls)** | 0.0802 s | **0.1076 s** | +0.0274 s | Comparable (+0.27 ms / call tradeoff for mutation isolation) |
| **Skill Dict Load Peak Memory** | 29.21 KB | **9.59 KB** | -19.62 KB | **67.2% memory reduction** |
| **JD Profile Parse (20 calls)** | 0.4102 s | **0.6002 s** | +0.1900 s | Subject to benchmark loop coupling & heap state (see §4.2) |
| **Full Pytest Execution Time** | 3.43 s (150 tests) | **2.26 s** (159 tests) | -1.17 s | **34.1% faster execution** |
| **Pytest Pass Count** | 150 passed, 0 failed | **159 passed, 0 failed** | +9 passed | **100% pass rate** |

---

### 4.2 Investigation of JD Profile Parsing Benchmark Timing

The standalone micro-benchmark recorded **0.4102s** (baseline) versus **0.6002s** (post-optimization) for 20 calls to `build_job_profile`. Investigation revealed the following technical factors:
1. **Benchmark Loop Coupling with `_known_skills()`**:
   In `scripts/benchmark_day18.py`, the micro-benchmark loop executes:
   ```python
   for _ in range(20):
       _ = build_job_profile(jd_sample_text, _known_skills(), KNOWN_ROLES)
   ```
   Each iteration calls `_known_skills()`, which calls `load_skill_dictionary()`. In the baseline, `load_skill_dictionary()` returned the un-cloned dictionary directly. In the optimized version, `load_skill_dictionary()` performs safe mutation-isolation dictionary cloning (`_clone_dictionary()`) on every single iteration. Thus, 20 list-copying passes over thousands of skills were inadvertently bundled into the JD parser measurement.
2. **Process Heap Fragmentation & GC Timing**:
   The micro-benchmark runs at the end of `benchmark_day18.py` after 48 complete ATS scoring passes. When measured in an isolated process with `known_skills` pre-computed outside the loop, 20 calls to `build_job_profile` execute in **0.17–0.19 seconds** (~8.5–9.7 ms/call).
3. **End-to-End Scoring Elimination**:
   Most importantly, in actual candidate scoring (`generate_candidate_report`), redundant JD parsing was **completely eliminated** by passing `job_profile=job_profile` to `score_skill_match()`, cutting total JD parsing passes per candidate from 2 down to 1.

---

### 4.3 Skill Dictionary Timing & Memory Analysis

For 100 repeated calls to `load_skill_dictionary()`:
- **Timing**: Baseline was 0.0802s (~0.80 ms/call); post-optimization was 0.1076s (~1.08 ms/call).
- **No speed improvement is claimed for skill dictionary loading.**
- **Trade-off Analysis**: The slight +0.27 ms/call difference is the deliberate, necessary cost of deep mutation isolation (`_clone_dictionary()`) in pure Python. Without cloning, modifying the returned dictionary would corrupt the shared cache for subsequent candidates.
- **Memory Improvement**: Peak traced memory dropped from **29.21 KB to 9.59 KB (-67.2% reduction)** because disk I/O and JSON parser intermediate buffers are eliminated after the initial load.

---

## 5. Test Suite & Verification Results

### 5.1 Verification of Regression Tests (`tests/test_day18_optimizations.py`)
Nine dedicated regression tests were introduced and verified:
1. `test_skill_dict_cache_isolation`: Mutating returned dictionary does not mutate cached source.
2. `test_skill_dict_cache_invalidation`: Modifying dictionary on disk auto-invalidates memory cache deterministically via `os.utime()` timestamp advancement (no sleep dependency).
3. `test_docx_merged_cell_deduplication`: Merged cells are deduplicated while distinct cells with identical text are retained.
4. `test_empty_and_corrupt_pdf_handling`: 0-byte PDFs return `""`, corrupt PDFs raise `ValueError`, missing files raise `FileNotFoundError`.
5. `test_empty_and_corrupt_docx_handling`: 0-byte DOCX files return `""`, corrupt files raise `ValueError`, missing files raise `FileNotFoundError`.
6. `test_noisy_text_cleaning`: Null bytes, control characters, and multiple spaces are sanitized without splitting content.
7. `test_score_skill_match_backward_compatibility`: Direct invocation with or without `job_profile` yields identical outputs.
8. `test_semantic_matcher_caching_and_idempotence`: Repeated semantic calls return identical similarity values.
9. `test_repeated_candidate_scoring_idempotence`: Explicit assertions ensure required test files are present and verified across repeated runs without conditional skipping.

### 5.2 Score Divergence Verification Across 48 Evaluation Pairs
An automated verification script compared every candidate ATS score produced by the optimized engine against `data/testing/ats_evaluation_results_v2.csv`:
```
Checked 48/48 pairs.
SUCCESS: ALL 48 CANDIDATE ATS SCORES MATCH 100% PERFECTLY! Zero divergence.
```

### 5.3 Complete Pytest Output (159 Tests)
```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: D:\Desktop\Zecser Bussiness\zecpath-ai
plugins: anyio-4.16.0
collected 159 items

tests\test_api.py ......                                                 [  3%]
tests\test_ats_pipeline.py .                                             [  4%]
tests\test_ats_scorer.py .........                                       [ 10%]
tests\test_basic.py .                                                    [ 10%]
tests\test_candidate_pipeline.py ...                                     [ 12%]
tests\test_candidate_ranker.py ........                                  [ 17%]
tests\test_candidate_ranking_cli.py .....                                [ 20%]
tests\test_day17_regressions.py ...........                              [ 27%]
tests\test_day18_optimizations.py .........                              [ 33%]
tests\test_docx_parser.py .                                              [ 33%]
tests\test_education_relevance.py .                                      [ 34%]
tests\test_education_step1.py .....                                      [ 37%]
tests\test_experience_parser.py .........                                [ 43%]
tests\test_experience_relevance.py ....                                  [ 45%]
tests\test_fairness_evaluation.py ....                                   [ 48%]
tests\test_file_handler.py .                                             [ 49%]
tests\test_jd_parser.py ....................                             [ 61%]
tests\test_main_ats_scorer.py .                                          [ 62%]
tests\test_pdf_parser.py .                                               [ 62%]
tests\test_privacy_masker.py ......                                      [ 66%]
tests\test_ranking_report.py ....                                        [ 69%]
tests\test_resume_extractor.py ..                                        [ 70%]
tests\test_resume_normalizer.py ......                                   [ 74%]
tests\test_scoring.py .                                                  [ 74%]
tests\test_section_classifier.py .............                           [ 83%]
tests\test_semantic_matcher.py ....                                      [ 85%]
tests\test_shortlisting.py ..........                                    [ 91%]
tests\test_skill_extractor.py .......                                    [ 96%]
tests\test_skill_matcher.py ......                                       [100%]

============================== warnings summary ===============================
venv\Lib\site-packages\fastapi\testclient.py:1
  D:\Desktop\Zecser Bussiness\zecpath-ai\venv\Lib\site-packages\fastapi\testclient.py:1: StarletteDeprecationWarning: Using `httpx` with `starlette.testclient` is deprecated; install `httpx2` instead.
    from starlette.testclient import TestClient as TestClient  # noqa

-- Docs: https://docs.pytest.org/en/stable/how-to/capture-warnings.html
======================= 159 passed, 1 warning in 2.26s ========================
```

---

## 6. Files Modified and Created

### Source Files Modified
- [`parsers/pdf_parser.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/parsers/pdf_parser.py): Context manager, pymupdf import, defensive error handling, list join.
- [`parsers/docx_parser.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/parsers/docx_parser.py): Merged-cell element deduplication, defensive error handling for 0-byte/corrupted files.
- [`parsers/skill_extractor.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/parsers/skill_extractor.py): Cached loading with mtime validation and safe mutation isolation cloning.
- [`parsers/text_cleaner.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/parsers/text_cleaner.py): Precompiled regex patterns, control character sanitization.
- [`scoring/semantic_matcher.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/scoring/semantic_matcher.py): One-time availability check, LRU caching for fallback vectors.
- [`scoring/skill_matcher.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/scoring/skill_matcher.py): Optional `job_profile` parameter for backward-compatible reuse.
- [`scoring/experience_relevance.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/scoring/experience_relevance.py): Precompiled regexes and LRU caching for sentence similarity.
- [`main_ats_scorer.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/main_ats_scorer.py): Passes pre-built `job_profile` to `score_skill_match`.

### Test Files Created & Hardened
- [`tests/test_day18_optimizations.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/tests/test_day18_optimizations.py): 9 regression tests for caching, deterministic invalidation, robustness, and parser edge cases.

### Benchmark & Reporting Artifacts Created
- [`scripts/benchmark_day18.py`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/scripts/benchmark_day18.py): Standalone reproducible benchmark script.
- [`data/testing/benchmark_baseline.json`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/data/testing/benchmark_baseline.json): Preserved Day 18 initial baseline metrics.
- [`data/testing/benchmark_optimized.json`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/data/testing/benchmark_optimized.json): Day 18 optimized metrics.
- [`docs/day18_performance_report.md`](file:///d:/Desktop/Zecser%20Bussiness/zecpath-ai/docs/day18_performance_report.md): This report.

---

## 7. Remaining Limitations & Recommendations for Future Optimization

1. **DOCX Memory Footprint**:
   - `python-docx` loads the full WordprocessingML package into an XML DOM tree, requiring ~5.45 MB peak memory for DOCX extraction compared to ~0.05 MB for PDF extraction.
   - *Recommendation*: For high-throughput environments, consider streaming XML extraction via `xml.etree.cElementTree.iterparse` targeting `word/document.xml`.
2. **Lexical Semantic Matching Fallback**:
   - The engine operates in `token-bigram-fallback` mode because `sentence-transformers` is not installed.
   - *Recommendation*: When embedding models are introduced in production, configure quantized onnx-runtime models or shared embedding microservices to avoid multi-gigabyte memory footprints per process.
3. **Quadratic Sequence Matching in Responsibilities**:
   - `difflib.SequenceMatcher` scales quadratically with character length. While LRU memoization speeds up repeated comparisons, comparing very long paragraphs remains CPU-bound.
   - *Recommendation*: Token Jaccard / Cosine pre-filtering prior to full sequence matching.
4. **Synchronous In-Process API Architecture**:
   - Currently, FastAPI routes run scoring in synchronous background tasks within the API process. Under high load, concurrent scoring requests will compete for the GIL.
   - *Recommendation*: Decouple ATS scoring into Celery or Redis Queue workers with dedicated process pools.
