from decimal import Decimal

import pytest

from app.services.grading import calculate_gpa, score_to_grade


@pytest.mark.parametrize(
    "score,letter,points",
    [
        ("100", "A", 5), ("70", "A", 5), ("69.99", "B", 4), ("60", "B", 4),
        ("59.99", "C", 3), ("50", "C", 3), ("49.99", "D", 2), ("45", "D", 2),
        ("44.99", "E", 1), ("40", "E", 1), ("39.99", "F", 0), ("0", "F", 0),
    ],
)
def test_score_to_grade_boundaries(score, letter, points):
    assert score_to_grade(Decimal(score)) == (letter, points)


def test_gpa_is_weighted_by_credit_units():
    # (3*5 + 2*3) / 5 = 4.20
    assert calculate_gpa([(3, 5), (2, 3)]) == Decimal("4.20")


def test_gpa_rounds_half_up():
    # (3*5 + 3*4 + 3*3) / 9 = 4.00 ; (2*5 + 1*4) / 3 = 4.666...
    assert calculate_gpa([(3, 5), (3, 4), (3, 3)]) == Decimal("4.00")
    assert calculate_gpa([(2, 5), (1, 4)]) == Decimal("4.67")


def test_gpa_is_none_without_graded_courses():
    assert calculate_gpa([]) is None