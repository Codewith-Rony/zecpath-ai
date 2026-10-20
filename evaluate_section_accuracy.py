from pathlib import Path

from parsers.resume_section_classifier import segment_resume


LABELED_RESUMES = {
    "resume_01.txt": {
        "summary": "summary",
        "contact": "contact",
        "skills": "skills",
        "work_experience": "work_experience",
        "education": "education",
        "projects": "projects",
        "certifications": "certifications",
    },

    "resume_02.txt": {
        "professional_summary": "summary",
        "contact": "contact",
        "core_skills": "skills",
        "experience": "work_experience",
        "educational_background": "education",
        "certificates": "certifications",
    },

    "resume_03.txt": {
        "contact": "contact",
        "skills": "skills",
        "work_experience": "work_experience",
        "education": "education",
        "projects": "projects",
    },
}


def evaluate_resume(file_name, expected_sections):
    file_path = Path("data/labeled_resumes") / file_name

    text = file_path.read_text(encoding="utf-8")

    result = segment_resume(text)

    predicted_sections = {
        section
        for section, blocks in result.items()
        if blocks
    }

    expected = set(expected_sections.values())

    true_positives = len(predicted_sections & expected)
    false_positives = len(predicted_sections - expected)
    false_negatives = len(expected - predicted_sections)

    total = true_positives + false_positives + false_negatives

    accuracy = (
        true_positives / total
        if total
        else 0
    )

    return {
        "expected": expected,
        "predicted": predicted_sections,
        "true_positives": true_positives,
        "false_positives": false_positives,
        "false_negatives": false_negatives,
        "accuracy": accuracy,
    }


def main():
    total_tp = 0
    total_fp = 0
    total_fn = 0

    print("=== Zecpath AI - Resume Section Detection Accuracy ===\n")

    for file_name, expected_sections in LABELED_RESUMES.items():

        result = evaluate_resume(
            file_name,
            expected_sections
        )

        total_tp += result["true_positives"]
        total_fp += result["false_positives"]
        total_fn += result["false_negatives"]

        print(f"Resume: {file_name}")
        print(f"Expected: {sorted(result['expected'])}")
        print(f"Predicted: {sorted(result['predicted'])}")
        print(f"True Positives: {result['true_positives']}")
        print(f"False Positives: {result['false_positives']}")
        print(f"False Negatives: {result['false_negatives']}")
        print(f"Accuracy: {result['accuracy'] * 100:.2f}%")
        print()

    total = total_tp + total_fp + total_fn

    overall_accuracy = (
        total_tp / total
        if total
        else 0
    )

    print("----------------------------------------")
    print(f"Overall Accuracy: {overall_accuracy * 100:.2f}%")
    print("----------------------------------------")


if __name__ == "__main__":
    main()