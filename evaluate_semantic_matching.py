import json
from pathlib import Path
from scoring.semantic_matcher import SemanticMatcher, evaluate_pairs

ROOT = Path(__file__).resolve().parent

def main():
    source = ROOT / "data" / "semantic_match_validation.json"
    pairs = json.loads(source.read_text(encoding="utf-8"))
    matcher = SemanticMatcher()
    report = evaluate_pairs(matcher, pairs, threshold=20.0)
    report["embedding_mode"] = matcher.mode
    output_dir = ROOT / "outputs" / "semantic_matching"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / "matching_accuracy_report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Mode: {matcher.mode}")
    print(f"Accuracy on {report['sample_count']} illustrative examples: {report['accuracy_percent']}%")
    print(f"Report saved to: {output}")
    print("Note: this small hand-labeled set is a smoke test, not production validation.")

if __name__ == "__main__":
    main()
