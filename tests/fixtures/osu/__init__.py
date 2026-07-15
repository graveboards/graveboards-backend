import json
from pathlib import Path
from typing import Union

from app.fixtures.paths import get_test_fixture_path
from app.fixtures.manager import FixtureManager


def load_beatmap(filename: str) -> dict:
    """Load a beatmap fixture from JSON file."""
    fixture_path = get_test_fixture_path("beatmaps") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_beatmapset(filename: str) -> dict:
    """Load a beatmapset fixture from JSON file."""
    fixture_path = get_test_fixture_path("beatmapsets") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user(filename: str) -> dict:
    """Load a user fixture from JSON file."""
    fixture_path = get_test_fixture_path("users") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_best(filename: str) -> list:
    """Load user scores best fixture from JSON file."""
    fixture_path = get_test_fixture_path("scores", "best") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_recent(filename: str) -> list:
    """Load user scores recent fixture from JSON file."""
    fixture_path = get_test_fixture_path("scores", "recent") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_firsts(filename: str) -> list:
    """Load user scores firsts fixture from JSON file."""
    fixture_path = get_test_fixture_path("scores", "firsts") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_beatmap_scores(filename: str) -> dict:
    """Load beatmap scores fixture from JSON file."""
    fixture_path = get_test_fixture_path("beatmap_scores") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_beatmap_attributes(filename: str) -> dict:
    """Load beatmap attributes fixture from JSON file."""
    fixture_path = get_test_fixture_path("beatmap_attributes") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_rankings(filename: str) -> dict:
    """Load rankings fixture from JSON file."""
    fixture_path = get_test_fixture_path("rankings") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_tags(filename: str = "tags") -> dict:
    """Load tags fixture from JSON file."""
    fixture_path = get_test_fixture_path("tags") / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)
