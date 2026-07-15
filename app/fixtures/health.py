"""Fixture health check utilities for Graveboards Backend.

This module provides health check functionality for fixture data,
including completeness verification, coverage analysis, and gap detection.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime
import json

from app.fixtures.paths import get_test_fixture_path
from app.fixtures.constants import RULESETS, SCORE_TYPES


@dataclass
class FixtureHealthResult:
    """Result of a fixture health check."""

    category: str
    expected_count: int
    actual_count: int
    coverage_percentage: float
    complete: bool
    files: List[str] = field(default_factory=list)
    missing_files: List[str] = field(default_factory=list)
    integrity_errors: List[str] = field(default_factory=list)
    last_updated: Optional[datetime] = None


@dataclass
class FixtureReport:
    """Comprehensive fixture report."""

    total_categories: int
    complete_categories: int
    incomplete_categories: int
    coverage_percentage: float
    categories: List[FixtureHealthResult] = field(default_factory=list)
    missing_gaps: List[Dict[str, Any]] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.utcnow)


def calculate_fixture_counts() -> Dict[str, int]:
    """Calculate expected fixture counts based on directory contents.

    Returns:
        Dictionary mapping fixture categories to expected counts
    """
    counts = {
        "beatmaps": 0,
        "beatmapsets": 0,
        "users": 0,
        "scores": 0,
        "beatmap_scores": 0,
        "beatmap_attributes": 0,
    }

    for ruleset in RULESETS:
        user_path = get_test_fixture_path("users") / ruleset
        if user_path.exists():
            counts["users"] += len(list(user_path.glob("*.json")))

    score_path = get_test_fixture_path("scores")
    for score_type in SCORE_TYPES:
        type_path = score_path / score_type
        if type_path.exists():
            counts["scores"] += len(list(type_path.glob("*.json")))

    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        cat_path = get_test_fixture_path(category)
        if cat_path.exists():
            counts[category] = len(list(cat_path.glob("*.json")))

    return counts


def validate_fixture_integrity(category: str, filename: str) -> List[str]:
    """Validate a single fixture file's integrity.

    Args:
        category: Fixture category
        filename: Filename to validate

    Returns:
        List of integrity errors (empty if valid)
    """
    errors = []
    fixture_path = get_test_fixture_path(category) / filename

    if not fixture_path.exists():
        return [f"File not found: {filename}"]

    try:
        with open(fixture_path, "r") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return [f"Invalid JSON: {str(e)}"]
    except Exception as e:
        return [f"Read error: {str(e)}"]

    if not isinstance(data, (dict, list)):
        errors.append("Root element must be object or array")

    return errors


def check_category_health(
    category: str, expected_count: Optional[int] = None
) -> FixtureHealthResult:
    """Check health of a specific fixture category.

    Args:
        category: Category to check
        expected_count: Expected fixture count (uses calculated count if None)

    Returns:
        Health result for the category
    """
    fixture_path = get_test_fixture_path(category)
    files = []

    if not fixture_path.exists():
        expected = (
            expected_count
            if expected_count is not None
            else calculate_fixture_counts().get(category, 0)
        )
        return FixtureHealthResult(
            category=category,
            expected_count=expected,
            actual_count=0,
            coverage_percentage=0.0,
            complete=False,
            integrity_errors=[f"Category directory does not exist: {category}"],
        )

    files = [f.name for f in fixture_path.glob("*.json")]
    actual_count = len(files)

    if expected_count is None:
        expected_count = calculate_fixture_counts().get(category, 0)

    integrity_errors = []
    for filename in files:
        errors = validate_fixture_integrity(category, filename)
        integrity_errors.extend(errors)

    coverage = (
        (actual_count / expected_count * 100)
        if expected_count > 0
        else (100.0 if actual_count == 0 else 0.0)
    )

    return FixtureHealthResult(
        category=category,
        expected_count=expected_count,
        actual_count=actual_count,
        coverage_percentage=coverage,
        complete=coverage >= 100 and len(integrity_errors) == 0,
        files=files,
        integrity_errors=integrity_errors,
    )


def check_all_categories() -> FixtureReport:
    """Check health of all fixture categories.

    Returns:
        Comprehensive report of all category health
    """
    expected_counts = calculate_fixture_counts()
    categories = []
    total_expected = 0
    total_actual = 0
    missing_gaps = []

    for category, expected_count in expected_counts.items():
        health = check_category_health(category, expected_count)
        categories.append(health)

        total_expected += expected_count
        total_actual += health.actual_count

        if expected_count > 0 and health.actual_count < expected_count:
            missing_gaps.append(
                {
                    "category": category,
                    "missing_count": expected_count - health.actual_count,
                    "coverage_percentage": health.coverage_percentage,
                }
            )

    coverage = (total_actual / total_expected * 100) if total_expected > 0 else 0.0

    return FixtureReport(
        total_categories=len(categories),
        complete_categories=sum(1 for c in categories if c.complete),
        incomplete_categories=sum(1 for c in categories if not c.complete),
        coverage_percentage=coverage,
        categories=categories,
        missing_gaps=missing_gaps,
    )


def get_incomplete_categories() -> List[FixtureHealthResult]:
    """Get list of incomplete fixture categories.

    Returns:
        List of categories with coverage < 100%
    """
    report = check_all_categories()
    return [c for c in report.categories if not c.complete]


def get_category_gaps() -> List[Dict[str, Any]]:
    """Get detailed gap information for each category.

    Returns:
        List of gap information dictionaries
    """
    categories = [
        "beatmaps",
        "beatmapsets",
        "users",
        "scores",
        "beatmap_scores",
        "beatmap_attributes",
    ]
    gaps = []

    for category in categories:
        health = check_category_health(category)
        if health.expected_count > 0 and health.actual_count < health.expected_count:
            expected_files = set(f.name for f in get_test_fixture_path(category).glob("*.json"))
            expected_list = sorted([f.name for f in get_test_fixture_path(category).glob("*.json")])

            gaps.append(
                {
                    "category": category,
                    "expected_count": health.expected_count,
                    "actual_count": health.actual_count,
                    "missing_count": health.expected_count - health.actual_count,
                    "coverage_percentage": health.coverage_percentage,
                    "expected_files": expected_list,
                }
            )

    return gaps
