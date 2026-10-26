
import json
import re
from pathlib import Path
from difflib import SequenceMatcher


PROJECT_ROOT = Path(__file__).resolve().parent.parent
DICTIONARY_PATH = PROJECT_ROOT / "data" / "skill_dictionary.json"


def load_skill_dictionary():
    """Load the master skill dictionary from JSON."""
    with DICTIONARY_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def normalize_text(text):
    """Normalize text for case-insensitive matching."""
    text = text.lower()
    text = re.sub(r"[\u2010-\u2015]", "-", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def contains_skill(text, skill):
    """Match a skill without matching it inside unrelated words."""
    pattern = r"(?<!\w)" + re.escape(skill) + r"(?!\w)"
    return re.search(pattern, text, flags=re.IGNORECASE) is not None


def extract_skills(resume_text):
    """Extract, normalize, deduplicate, and score resume skills."""
    dictionary = load_skill_dictionary()
    text = normalize_text(resume_text)

    extracted = {}

    # Match individual skills and their synonyms.
    for category in ("technical", "business", "creative"):
        for canonical_name, synonyms in dictionary.get(category, {}).items():
            terms = set([canonical_name, *synonyms])
            matched_terms = [
                term for term in terms
                if term and contains_skill(text, normalize_text(term))
            ]

            if matched_terms:
                # Exact dictionary matches receive high confidence.
                confidence = 0.98 if any(
                    normalize_text(term) == normalize_text(canonical_name)
                    for term in matched_terms
                ) else 0.93

                extracted[canonical_name] = {
                    "name": canonical_name,
                    "category": category,
                    "confidence": confidence,
                    "matched_terms": sorted(matched_terms)
                }

    # Detect skill stacks and add their component skills.
    for stack_name, components in dictionary.get("skill_stacks", {}).items():
        if contains_skill(text, normalize_text(stack_name)):
            extracted[stack_name] = {
                "name": stack_name,
                "category": "skill_stack",
                "confidence": 0.98,
                "matched_terms": [stack_name]
            }

            # A stack implies familiarity with its listed components.
            for component in components:
                canonical_component = find_canonical_skill(
                    component, dictionary
                )


                if canonical_component:
                    if canonical_component not in extracted:
                        extracted[canonical_component] = {
                            "name": canonical_component,
                            "category": find_skill_category(
                                canonical_component, dictionary
                            ),
                            "confidence": 0.75,
                            "matched_terms": [stack_name],
                            "inferred_from": stack_name
                        }
                    elif stack_name not in extracted[canonical_component].get(
                        "inferred_from", ""
                    ):
                        extracted[canonical_component].setdefault(
                            "inferred_from", stack_name
                        )


    return {
        "skills": sorted(
            extracted.values(),
            key=lambda skill: (
                skill["category"],
                skill["name"].lower()
            )
        ),
        "total_skills": len(extracted)
    }


def find_canonical_skill(term, dictionary):
    """Find the canonical name associated with a dictionary term."""
    target = normalize_text(term)

    for category in ("technical", "business", "creative"):
        for canonical_name, synonyms in dictionary.get(category, {}).items():
            candidates = [canonical_name, *synonyms]
            if any(normalize_text(item) == target for item in candidates):
                return canonical_name

    return None


def find_skill_category(canonical_name, dictionary):
    """Return the category of a canonical skill."""
    for category in ("technical", "business", "creative"):
        if canonical_name in dictionary.get(category, {}):
            return category

    return "technical"


def find_spelling_variations(text, dictionary, threshold=0.80):
    """Suggest skills for likely misspellings using fuzzy matching."""
    normalized_text = normalize_text(text)
    words = re.findall(r"\b[a-z][a-z0-9+#.-]*\b", normalized_text)

    suggestions = []

    for category in ("technical", "business", "creative"):
        for canonical_name, synonyms in dictionary.get(category, {}).items():
            # Compare against individual words and known skill phrases.
            terms = set([canonical_name, *synonyms])

            for term in terms:
                normalized_term = normalize_text(term)

                # Skip multi-word phrases for this word-level matcher.
                if " " in normalized_term:
                    continue

                for word in words:
                    if word == normalized_term:
                        continue

                    # Avoid comparing words with very different lengths.
                    if abs(len(word) - len(normalized_term)) > 2:
                        continue

                    similarity = SequenceMatcher(
                        None, word, normalized_term
                    ).ratio()

                    if similarity >= threshold:
                        suggestions.append({
                            "text": word,
                            "suggested_skill": canonical_name,
                            "category": category,
                            "similarity": round(similarity, 2)
                        })

    # Keep only the strongest suggestion for each misspelled word.
    unique = {}

    for suggestion in suggestions:
        key = suggestion["text"]

        if (
            key not in unique
            or suggestion["similarity"] > unique[key]["similarity"]
        ):
            unique[key] = suggestion

    return list(unique.values())
