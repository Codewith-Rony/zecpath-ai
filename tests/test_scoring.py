from scoring.scoring_engine import calculate_overall_score


def test_calculate_overall_score():
    scores = [80, 70, 90]

    result = calculate_overall_score(scores)

    assert result == 80
