import json
import sys
from pathlib import Path
from parsers.resume_extractor import extract_resume
from parsers.skill_extractor import extract_skills
from scoring.semantic_matcher import SemanticMatcher

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "outputs" / "semantic_matching"

def main():
    if len(sys.argv) < 3:
        print('Usage: python main_semantic_matcher.py "path/to/resume.pdf" "path/to/job_description.txt"')
        return
    resume_path, jd_path = Path(sys.argv[1]), Path(sys.argv[2])
    if not resume_path.is_absolute():
        resume_path = Path.cwd() / resume_path
    if not jd_path.is_absolute():
        jd_path = Path.cwd() / jd_path
    if not resume_path.exists() or not jd_path.exists():
        raise FileNotFoundError("Resume or job description file not found.")
    resume_text = extract_resume(str(resume_path))["cleaned_text"]
    jd_text = jd_path.read_text(encoding="utf-8", errors="replace")
    resume_skills = [item["name"] for item in extract_skills(resume_text)["skills"]]
    # Transparent baseline: compare complete text, skills, experience and projects as sections.
    resume_payload = {
        "skills": resume_skills,
        "experience_summary": _section(resume_text, ("experience", "work experience", "professional experience"), ("projects", "education", "skills")),
        "project_descriptions": _section(resume_text, ("projects", "project"), ("education", "skills", "experience")),
    }
    jd_payload = {
        "required_skills": _section(jd_text, ("requirements", "skills", "technical skills"), ("responsibilities", "benefits")),
        "experience_requirements": _section(jd_text, ("experience", "responsibilities"), ("requirements", "benefits")),
        "relevant_projects": jd_text,
    }
    result = SemanticMatcher().score_resume_job(resume_payload, jd_payload)
    result.update({"resume_file": resume_path.name, "job_description_file": jd_path.name})
    OUT.mkdir(parents=True, exist_ok=True)
    output_path = OUT / f"{resume_path.stem}_vs_{jd_path.stem}_match.json"
    output_path.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Overall similarity: {result['overall_similarity']}")
    print(f"Mode: {result['embedding_mode']}")
    print(f"Output saved to: {output_path}")

def _section(text, headings, stop_headings):
    lines = text.splitlines()
    collecting = False
    result = []
    for line in lines:
        stripped = line.strip()
        lower = stripped.lower().strip(": ")
        if any(lower == h for h in headings):
            collecting = True
            continue
        if collecting and any(lower == h for h in stop_headings):
            break
        if collecting:
            result.append(stripped)
    return " ".join(result) if result else text

if __name__ == "__main__":
    main()
