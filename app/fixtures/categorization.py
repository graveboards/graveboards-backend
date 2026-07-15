"""Categorization logic for fixture data classification.

Provides a reusable Categorizer class for mapping numeric values to buckets
using half-open intervals. Used across fetcher types for difficulty, playcount,
bpm, accuracy, and other range-based classifications.
"""

from typing import Callable


class Categorizer:
    """Categorize numeric values into buckets using half-open intervals.

    All ranges except the last are [lo, hi). The last range is [lo, hi] to catch edge values.

    Example:
        categorizer = Categorizer({
            "easy": (0, 2.0),
            "medium": (2.0, 5.0),
            "hard": (5.0, 7.0),
            "expert": (7.0, 999.0),
        })
        categorizer.categorize(3.5)  # Returns "medium"
    """

    def __init__(self, ranges: dict[str, tuple[float, float]]):
        self.ranges = ranges

    def categorize(self, value: float) -> str | None:
        """Categorize a value into a bucket.

        Args:
            value: Numeric value to categorize

        Returns:
            Bucket name if value falls in a range, None otherwise
        """
        items = list(self.ranges.items())
        for i, (category, (lo, hi)) in enumerate(items):
            if i == len(items) - 1:
                if lo <= value <= hi:
                    return category
            else:
                if lo <= value < hi:
                    return category
        return None


# Pre-built categorizers for common use cases
DIFFICULTY_CATEGORIZER = Categorizer(
    {
        "easy": (0, 2.0),
        "medium": (2.0, 5.0),
        "hard": (5.0, 7.0),
        "expert": (7.0, 999.0),
    }
)

PLAYCOUNT_CATEGORIZER = Categorizer(
    {
        "low": (0, 100),
        "medium": (100, 1000),
        "high": (1000, 999999999),
    }
)

BPM_CATEGORIZER = Categorizer(
    {
        "low": (0, 90),
        "medium": (90, 150),
        "high": (150, 9999),
    }
)

ACCURACY_CATEGORIZER = Categorizer(
    {
        "low": (0, 80),
        "medium": (80, 95),
        "high": (95, 100.01),
    }
)

HIT_LENGTH_CATEGORIZER = Categorizer(
    {
        "short": (0, 60),
        "medium": (60, 180),
        "long": (180, 99999),
    }
)

MAX_COMBO_CATEGORIZER = Categorizer(
    {
        "low": (0, 500),
        "medium": (500, 1500),
        "high": (1500, 9999999),
    }
)

DRAIN_CATEGORIZER = Categorizer(
    {
        "low": (0, 3.0),
        "medium": (3.0, 6.0),
        "high": (6.0, 99.0),
    }
)

AR_CATEGORIZER = Categorizer(
    {
        "low": (0, 3.0),
        "medium": (3.0, 6.0),
        "high": (6.0, 99.0),
    }
)

CS_CATEGORIZER = Categorizer(
    {
        "low": (0, 3.0),
        "medium": (3.0, 5.5),
        "high": (5.5, 99.0),
    }
)

RATING_CATEGORIZER = Categorizer(
    {
        "low": (0, 2.0),
        "medium": (2.0, 3.5),
        "high": (3.5, 99.0),
    }
)

FAVOURITE_COUNT_CATEGORIZER = Categorizer(
    {
        "low": (0, 10),
        "medium": (10, 100),
        "high": (100, 9999999),
    }
)

PLAY_COUNT_CATEGORIZER = Categorizer(
    {
        "low": (0, 100),
        "medium": (100, 1000),
        "high": (1000, 999999999),
    }
)
