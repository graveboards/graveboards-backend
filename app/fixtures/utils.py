import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

from app.logging import get_logger

logger = get_logger(__name__)

FIXTURES_DIR = Path(__file__).resolve().parent.parent.parent / "instance" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

METADATA_FILE = FIXTURES_DIR / "metadata.json"

BASE_SAMPLE_COUNTS = {
    "beatmaps": 50,
    "beatmapsets": 30,
    "users": {"osu": 25, "taiko": 25, "fruits": 25, "mania": 25},
    "scores": {"best": 15, "firsts": 15, "recent": 15},
    "beatmap_scores": 20,
    "beatmap_attributes": 20,
}

ID_RANGES = {
    "beatmaps": {"min": 1, "max": 1000000},
    "beatmapsets": {"min": 1, "max": 100000},
    "users": {"min": 1, "max": 10000000},
}

MINIMAL_PROFILE = {
    "beatmaps": 1,
    "beatmapsets": 1,
    "users": {"osu": 1, "taiko": 1, "fruits": 1, "mania": 1},
    "scores": {"best": 1, "firsts": 1, "recent": 1},
    "beatmap_scores": 1,
    "beatmap_attributes": 1,
}

RULESETS = ["osu", "taiko", "fruits", "mania"]
SCORE_TYPES = ["best", "firsts", "recent"]


def calculate_sample_counts(
    scale: float = 1.0,
    beatmaps: int | None = None,
    beatmapsets: int | None = None,
    users_osu: int | None = None,
    users_taiko: int | None = None,
    users_fruits: int | None = None,
    users_mania: int | None = None,
    scores_best: int | None = None,
    scores_firsts: int | None = None,
    scores_recent: int | None = None,
    beatmap_scores: int | None = None,
    beatmap_attributes: int | None = None,
    use_minimal: bool = False,
) -> dict:
    has_explicit_categories = any([
        beatmaps is not None,
        beatmapsets is not None,
        users_osu is not None,
        users_taiko is not None,
        users_fruits is not None,
        users_mania is not None,
        scores_best is not None,
        scores_firsts is not None,
        scores_recent is not None,
        beatmap_scores is not None,
        beatmap_attributes is not None,
    ])

    if use_minimal:
        base = MINIMAL_PROFILE.copy()
    else:
        base = BASE_SAMPLE_COUNTS.copy()

    if scale != 1.0:
        if isinstance(base, dict):
            for key, value in base.items():
                if isinstance(value, int):
                    base[key] = max(1, int(value * scale))
                elif isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        base[key][subkey] = max(1, int(subvalue * scale))

    if has_explicit_categories:
        result = {}
    else:
        result = base.copy()

    overrides = {
        "beatmaps": beatmaps,
        "beatmapsets": beatmapsets,
        "users": {
            "osu": users_osu,
            "taiko": users_taiko,
            "fruits": users_fruits,
            "mania": users_mania,
        },
        "scores": {
            "best": scores_best,
            "firsts": scores_firsts,
            "recent": scores_recent,
        },
        "beatmap_scores": beatmap_scores,
        "beatmap_attributes": beatmap_attributes,
    }

    for key, override_value in overrides.items():
        if override_value is not None:
            if isinstance(override_value, dict):
                if key not in result:
                    result[key] = {}
                for subkey, subvalue in override_value.items():
                    if subvalue is not None:
                        result[key][subkey] = subvalue
            else:
                result[key] = override_value

    return result


def get_fixture_path(category: str, subcategory: str | None = None) -> Path:
    path = FIXTURES_DIR / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path


def load_metadata() -> dict:
    if METADATA_FILE.exists():
        with open(METADATA_FILE) as f:
            return json.load(f)
    return create_empty_metadata()


def create_empty_metadata() -> dict:
    return {
        "last_updated": None,
        "samples": {
            "beatmaps": {"count": 0, "last_fetched": None},
            "beatmapsets": {"count": 0, "last_fetched": None},
            "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_fetched": None},
            "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_fetched": None},
            "beatmap_scores": {"count": 0, "last_fetched": None},
            "beatmap_attributes": {"count": 0, "last_fetched": None},
        },
        "failed_ids": {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        },
        "id_ranges": {
            "beatmaps": {"min": 1, "max": 1000000},
            "beatmapsets": {"min": 1, "max": 100000},
            "users": {"min": 1, "max": 10000000},
        },
        "rulesets": RULESETS,
        "source": "osu.ppy.sh/api/v2",
    }


def save_metadata(metadata: dict) -> None:
    metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
    metadata.setdefault("failed_ids", {
        "beatmaps": [],
        "beatmapsets": [],
        "users": {r: [] for r in RULESETS},
    })
    metadata.setdefault("id_ranges", {
        "beatmaps": {"min": 1, "max": 1000000},
        "beatmapsets": {"min": 1, "max": 100000},
        "users": {"min": 1, "max": 10000000},
    })
    with open(METADATA_FILE, "w") as f:
        json.dump(metadata, f, indent=2)


def get_fixture_count(category: str, subcategory: str | None = None) -> int:
    path = get_fixture_path(category, subcategory)
    if not path.exists():
        return 0
    return len(list(path.glob("*.json")))


def get_all_fixture_files() -> dict[str, list[Path]]:
    fixtures = {}
    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        path = FIXTURES_DIR / category
        if path.exists():
            fixtures[category] = list(path.glob("*.json"))
    for category in ["users", "scores"]:
        path = FIXTURES_DIR / category
        if path.exists():
            fixtures[category] = {}
            for sub in path.iterdir():
                if sub.is_dir():
                    fixtures[category][sub.name] = list(sub.glob("*.json"))
    return fixtures


def wipe_all_fixtures() -> None:
    if FIXTURES_DIR.exists():
        shutil.rmtree(FIXTURES_DIR)
    FIXTURES_DIR.mkdir(parents=True, exist_ok=True)
    save_metadata(create_empty_metadata())
    logger.info("All fixtures wiped")
