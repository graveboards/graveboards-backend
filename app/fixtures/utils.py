import json
import shutil
from pathlib import Path
from datetime import datetime, timezone

from app.logging import get_logger
from app.config import PROJECT_ROOT

logger = get_logger(__name__)

FIXTURES_DIR = PROJECT_ROOT / "instance" / "fixtures"
FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "osu"
TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

QUEUE_TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "queues"
QUEUE_TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)

REQUEST_TEST_FIXTURES_DIR = PROJECT_ROOT / "tests" / "fixtures" / "requests"
REQUEST_TEST_FIXTURES_DIR.mkdir(parents=True, exist_ok=True)


def get_test_fixture_path(category: str, subcategory: str | None = None) -> Path:
    path = TEST_FIXTURES_DIR / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path

METADATA_FILE = FIXTURES_DIR / "metadata.json"

BASE_SAMPLE_COUNTS = {
    "beatmaps": 50,
    "beatmapsets": 30,
    "users": {"osu": 25, "taiko": 25, "fruits": 25, "mania": 25},
    "scores": {"best": 15, "firsts": 15, "recent": 15},
    "beatmap_scores": 20,
    "beatmap_attributes": 20,
    "queues": 50,
    "requests": 100,
}

ID_RANGE_MIN = 1

ID_RANGES = {
    "beatmaps": {"min": ID_RANGE_MIN, "max": 5_800_000},
    "beatmapsets": {"min": ID_RANGE_MIN, "max": 2_600_000},
    "users": {"min": ID_RANGE_MIN, "max": 40_000_000},
}

MINIMAL_PROFILE = {
    "beatmaps": 1,
    "beatmapsets": 1,
    "users": {"osu": 1, "taiko": 1, "fruits": 1, "mania": 1},
    "scores": {"best": 1, "firsts": 1, "recent": 1},
    "beatmap_scores": 1,
    "beatmap_attributes": 1,
    "queues": 1,
    "requests": 1,
}

RULESETS = ["osu", "taiko", "fruits", "mania"]
SCORE_TYPES = ["best", "firsts", "recent"]
TOP_PLAYERS_PER_RULESET = 1000


def create_targeted_metadata() -> dict:
    """Create the standard targeted fixtures metadata structure."""
    return {
        "beatmaps": {
            "by_status": {},
            "by_ruleset": {},
            "by_difficulty": {},
            "by_playcount": {},
            "file_metadata": {},
        },
        "beatmapsets": {
            "by_status": {},
            "file_metadata": {},
        },
        "users": {
            "by_activity": {},
            "per_ruleset": {},
            "file_metadata": {},
        },
        "scores": {
            "by_rank": {},
            "by_mods": {},
            "file_metadata": {},
        },
        "queues": {
            "by_visibility": {},
            "by_is_open": {},
            "file_metadata": {},
        },
        "requests": {
            "by_status": {},
            "by_mv_checked": {},
            "file_metadata": {},
        },
    }

DISCUSSION_STATUSES = ["ranked", "loved", "qualified", "graveyard", "pending", "approved", "all"]


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


def get_fixture_path(category: str, subcategory: str | None = None, fixtures_dir: Path | None = None) -> Path:
    base = fixtures_dir or FIXTURES_DIR
    path = base / category
    if subcategory:
        path = path / subcategory
    path.mkdir(parents=True, exist_ok=True)
    return path


def _metadata_path(fixtures_dir: Path | None = None) -> Path:
    base = fixtures_dir or FIXTURES_DIR
    return base / "metadata.json"


def load_metadata(fixtures_dir: Path | None = None) -> dict:
    metadata_file = _metadata_path(fixtures_dir)
    if metadata_file.exists():
        with open(metadata_file) as f:
            return json.load(f)
    return create_empty_metadata()


def save_metadata(metadata: dict, fixtures_dir: Path | None = None) -> None:
    metadata["last_updated"] = datetime.now(timezone.utc).isoformat()
    metadata.setdefault("promoted_fixtures", {
        "beatmaps": {"count": 0, "last_promoted": None},
        "beatmapsets": {"count": 0, "last_promoted": None},
        "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_promoted": None},
        "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_promoted": None},
        "beatmap_scores": {"count": 0, "last_promoted": None},
        "beatmap_attributes": {"count": 0, "last_promoted": None},
        "queues": {"count": 0, "last_promoted": None},
        "requests": {"count": 0, "last_promoted": None},
    })
    metadata.setdefault("fetched_ids", {
        "beatmaps": [],
        "beatmapsets": [],
        "users": {r: [] for r in RULESETS},
    })
    metadata.setdefault("top_player_ids", {r: [] for r in RULESETS})
    metadata.setdefault("id_ranges", ID_RANGES.copy())
    metadata_file = _metadata_path(fixtures_dir)
    metadata_file.parent.mkdir(parents=True, exist_ok=True)
    with open(metadata_file, "w") as f:
        json.dump(metadata, f, indent=2)


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
            "queues": {"count": 0, "last_fetched": None},
            "requests": {"count": 0, "last_fetched": None},
        },
        "promoted_fixtures": {
            "beatmaps": {"count": 0, "last_promoted": None},
            "beatmapsets": {"count": 0, "last_promoted": None},
            "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_promoted": None},
            "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_promoted": None},
            "beatmap_scores": {"count": 0, "last_promoted": None},
            "beatmap_attributes": {"count": 0, "last_promoted": None},
            "queues": {"count": 0, "last_promoted": None},
            "requests": {"count": 0, "last_promoted": None},
        },
        "failed_ids": {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        },
        "top_player_ids": {r: [] for r in RULESETS},
        "id_ranges": ID_RANGES,
        "rulesets": RULESETS,
        "source": "osu.ppy.sh/api/v2",
    }


def create_empty_samples() -> dict:
    return {
        "beatmaps": {"count": 0, "last_fetched": None},
        "beatmapsets": {"count": 0, "last_fetched": None},
        "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_fetched": None},
        "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_fetched": None},
        "beatmap_scores": {"count": 0, "last_fetched": None},
        "beatmap_attributes": {"count": 0, "last_fetched": None},
        "queues": {"count": 0, "last_fetched": None},
        "requests": {"count": 0, "last_fetched": None},
    }


def create_empty_promoted_fixtures() -> dict:
    return {
        "beatmaps": {"count": 0, "last_promoted": None},
        "beatmapsets": {"count": 0, "last_promoted": None},
        "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_promoted": None},
        "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_promoted": None},
        "beatmap_scores": {"count": 0, "last_promoted": None},
        "beatmap_attributes": {"count": 0, "last_promoted": None},
        "queues": {"count": 0, "last_promoted": None},
        "requests": {"count": 0, "last_promoted": None},
    }





def get_fixture_count(category: str, subcategory: str | None = None, fixtures_dir: Path | None = None) -> int:
    path = get_fixture_path(category, subcategory, fixtures_dir=fixtures_dir)
    if not path.exists():
        return 0
    return len(list(path.glob("*.json")))


def get_all_fixture_files(fixtures_dir: Path | None = None) -> dict[str, list[Path]]:
    base = fixtures_dir or FIXTURES_DIR
    fixtures = {}
    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes", "queues", "requests"]:
        path = base / category
        if path.exists():
            fixtures[category] = list(path.glob("*.json"))
    for category in ["users", "scores"]:
        path = base / category
        if path.exists():
            fixtures[category] = {}
            for sub in path.iterdir():
                if sub.is_dir():
                    fixtures[category][sub.name] = list(sub.glob("*.json"))
    return fixtures


def load_top_player_ids(fixtures_dir: Path | None = None) -> dict[str, list[int]]:
    metadata = load_metadata(fixtures_dir=fixtures_dir)
    return metadata.get("top_player_ids", {r: [] for r in RULESETS})


def save_top_player_ids(top_player_ids: dict[str, list[int]], fixtures_dir: Path | None = None) -> None:
    metadata = load_metadata(fixtures_dir=fixtures_dir)
    metadata["top_player_ids"] = top_player_ids
    save_metadata(metadata, fixtures_dir=fixtures_dir)


def wipe_all_fixtures(clear_failed_ids: bool = False, clear_top_player_ids: bool = False, fixtures_dir: Path | None = None) -> None:
    base = fixtures_dir or FIXTURES_DIR
    if base.exists():
        shutil.rmtree(base)
    base.mkdir(parents=True, exist_ok=True)
    
    metadata = create_empty_metadata()
    metadata_file = _metadata_path(fixtures_dir)
    if not clear_failed_ids and metadata_file.exists():
        existing_metadata = load_metadata(fixtures_dir=fixtures_dir)
        metadata["failed_ids"] = existing_metadata.get("failed_ids", metadata["failed_ids"])
    if not clear_top_player_ids and metadata_file.exists():
        existing_metadata = load_metadata(fixtures_dir=fixtures_dir)
        metadata["top_player_ids"] = existing_metadata.get("top_player_ids", metadata["top_player_ids"])
    
    save_metadata(metadata, fixtures_dir=fixtures_dir)
    logger.info("All fixtures wiped")
