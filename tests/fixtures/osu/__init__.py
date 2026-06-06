import json
from pathlib import Path


def load_beatmap(filename: str) -> dict:
    """Load a beatmap fixture from JSON file."""
    fixture_path = Path(__file__).parent / "beatmaps" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    data["beatmap_id"] = data["id"]
    data["title"] = data.get("version") or data.get("title")
    return data


def load_beatmapset(filename: str) -> dict:
    """Load a beatmapset fixture from JSON file."""
    fixture_path = Path(__file__).parent / "beatmapsets" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        data = json.load(f)
    data["beatmapset_id"] = data["id"]
    return data


def load_user(filename: str) -> dict:
    """Load a user fixture from JSON file."""
    fixture_path = Path(__file__).parent / "users" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_best(filename: str) -> list:
    """Load user scores best fixture from JSON file."""
    fixture_path = Path(__file__).parent / "scores" / "best" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_recent(filename: str) -> list:
    """Load user scores recent fixture from JSON file."""
    fixture_path = Path(__file__).parent / "scores" / "recent" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_user_scores_firsts(filename: str) -> list:
    """Load user scores firsts fixture from JSON file."""
    fixture_path = Path(__file__).parent / "scores" / "firsts" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_beatmap_scores(filename: str) -> dict:
    """Load beatmap scores fixture from JSON file."""
    fixture_path = Path(__file__).parent / "beatmap_scores" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_beatmap_attributes(filename: str) -> dict:
    """Load beatmap attributes fixture from JSON file."""
    fixture_path = Path(__file__).parent / "beatmap_attributes" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)


def load_rankings(filename: str) -> dict:
    """Load rankings fixture from JSON file."""
    fixture_path = Path(__file__).parent / "rankings" / f"{filename}.json"
    with open(fixture_path, "r") as f:
        return json.load(f)
