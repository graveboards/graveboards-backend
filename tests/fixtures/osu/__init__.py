import json
from pathlib import Path


def load_beatmap_fixture(beatmap_id: int) -> dict:
    path = Path(__file__).parent / "osu" / "beatmaps" / f"beatmap_{beatmap_id}.json"
    with open(path) as f:
        return json.load(f)


def load_beatmapset_fixture(beatmapset_id: int) -> dict:
    path = Path(__file__).parent / "osu" / "beatmapsets" / f"beatmapset_{beatmapset_id}.json"
    with open(path) as f:
        return json.load(f)


def load_user_fixture(user_id: int, ruleset: str = "osu") -> dict:
    path = Path(__file__).parent / "osu" / "users" / ruleset / f"user_{user_id}_{ruleset}.json"
    with open(path) as f:
        return json.load(f)


def load_scores_fixture(user_id: int, score_type: str = "best") -> dict:
    path = Path(__file__).parent / "osu" / "scores" / score_type / f"scores_{user_id}_{score_type}.json"
    with open(path) as f:
        return json.load(f)


def load_beatmap_scores_fixture(beatmap_id: int) -> dict:
    path = Path(__file__).parent / "osu" / "beatmap_scores" / f"beatmap_scores_{beatmap_id}.json"
    with open(path) as f:
        return json.load(f)


def load_beatmap_attributes_fixture(beatmap_id: int, mods: int) -> dict:
    path = Path(__file__).parent / "osu" / "beatmap_attributes" / f"beatmap_attrs_{beatmap_id}_mods{mods}.json"
    with open(path) as f:
        return json.load(f)
