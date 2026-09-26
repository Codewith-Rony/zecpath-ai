def calculate_overall_score(scores):
    if not scores:
        return 0

    return sum(scores) / len(scores)
