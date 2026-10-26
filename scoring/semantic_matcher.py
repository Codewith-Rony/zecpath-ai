"""Resume-to-job semantic matching.

Uses SentenceTransformer embeddings when sentence-transformers is installed.
A transparent token/bigram vector fallback keeps the module runnable offline,
but is lexical rather than truly semantic. Scores are similarity indicators,
not probabilities or hiring decisions.
"""
import math
import re
from collections import Counter

DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"

def _tokens(text):
    return re.findall(r"[a-z0-9+#.]+", (text or "").lower())

def _fallback_vector(text):
    tokens = _tokens(text)
    features = Counter(tokens)
    features.update(f"{a}_{b}" for a, b in zip(tokens, tokens[1:]))
    norm = math.sqrt(sum(value * value for value in features.values()))
    if norm:
        return {key: value / norm for key, value in features.items()}
    return {}

def _cosine_sparse(a, b):
    if not a or not b:
        return 0.0
    return max(0.0, min(1.0, sum(value * b.get(key, 0.0) for key, value in a.items())))

class SemanticMatcher:
    def __init__(self, model_name=DEFAULT_MODEL, prefer_embeddings=True):
        self.model_name = model_name
        self.model = None
        if prefer_embeddings:
            try:
                from sentence_transformers import SentenceTransformer
                self.model = SentenceTransformer(model_name)
            except (ImportError, OSError, RuntimeError):
                self.model = None
        self.mode = "sentence-transformers" if self.model is not None else "token-bigram-fallback"

    def similarity(self, text_a, text_b):
        if not (text_a or "").strip() or not (text_b or "").strip():
            return 0.0
        if self.model is not None:
            vectors = self.model.encode([text_a, text_b], normalize_embeddings=True)
            score = float(sum(x * y for x, y in zip(vectors[0], vectors[1])))
            return round(max(0.0, min(1.0, score)) * 100, 2)
        return round(_cosine_sparse(_fallback_vector(text_a), _fallback_vector(text_b)) * 100, 2)

    def score_resume_job(self, resume, job_description, threshold=55.0):
        """Compare skills, experience summaries, and project descriptions."""
        fields = {
            "skills": ("skills", "required_skills"),
            "experience": ("experience_summary", "experience_requirements"),
            "projects": ("project_descriptions", "relevant_projects"),
        }
        field_scores = {}
        for name, (resume_key, job_key) in fields.items():
            left = resume.get(resume_key, "")
            right = job_description.get(job_key, "")
            if isinstance(left, list):
                left = " ".join(str(x) for x in left)
            if isinstance(right, list):
                right = " ".join(str(x) for x in right)
            field_scores[name] = self.similarity(str(left), str(right))
        available = [score for score in field_scores.values() if score > 0]
        overall = round(sum(available) / len(available), 2) if available else 0.0
        return {
            "overall_similarity": overall,
            "field_scores": field_scores,
            "threshold": threshold,
            "is_match": overall >= threshold,
            "embedding_mode": self.mode,
            "interpretation": "similarity score, not probability",
        }

def evaluate_pairs(matcher, labeled_pairs, threshold=55.0):
    """Evaluate labeled examples; labels should be 1 for match and 0 for non-match."""
    rows = []
    tp = tn = fp = fn = 0
    for pair in labeled_pairs:
        score = matcher.similarity(pair["resume_text"], pair["job_text"])
        predicted = int(score >= threshold)
        actual = int(bool(pair["is_match"]))
        tp += predicted == 1 and actual == 1
        tn += predicted == 0 and actual == 0
        fp += predicted == 1 and actual == 0
        fn += predicted == 0 and actual == 1
        rows.append({"label": pair.get("label", ""), "score": score, "expected_match": bool(actual), "predicted_match": bool(predicted)})
    total = len(rows)
    return {
        "threshold": threshold,
        "sample_count": total,
        "correct": tp + tn,
        "accuracy_percent": round((tp + tn) / total * 100, 2) if total else 0.0,
        "precision_percent": round(tp / (tp + fp) * 100, 2) if tp + fp else 0.0,
        "recall_percent": round(tp / (tp + fn) * 100, 2) if tp + fn else 0.0,
        "confusion_matrix": {"true_positive": tp, "true_negative": tn, "false_positive": fp, "false_negative": fn},
        "results": rows,
        "note": "Accuracy is only meaningful when labels are reliable and examples represent real resumes/JDs.",
    }
