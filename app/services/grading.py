from decimal import ROUND_HALF_UP, Decimal

# (minimum score, letter, grade points), highest first
SCALE = [
    (Decimal("70"), "A", 5),
    (Decimal("60"), "B", 4),
    (Decimal("50"), "C", 3),
    (Decimal("45"), "D", 2),
    (Decimal("40"), "E", 1),
    (Decimal("0"), "F", 0),
]


def score_to_grade(score: Decimal) -> tuple[str, int]:
    for minimum, letter, points in SCALE:
        if score >= minimum:
            return letter, points
    raise ValueError("score must be between 0 and 100")


def calculate_gpa(items: list[tuple[int, int]]) -> Decimal | None:
    """items: (credit_units, grade_points) for each graded course."""
    total_units = sum(units for units, _ in items)
    if total_units == 0:
        return None
    quality_points = sum(units * points for units, points in items)
    return (Decimal(quality_points) / Decimal(total_units)).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )