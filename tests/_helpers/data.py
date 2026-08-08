"""Shared test-data builders.

Keep this module named WITHOUT a `test_` prefix so pytest never collects it.
Import from tests as:  from tests._helpers.data import full_beatmapset_dict
"""

from __future__ import annotations

from typing import Any


def full_beatmapset_dict(**overrides: Any) -> dict[str, Any]:
    """Return a fresh beatmapset dict with sensible defaults.

    Accepts ``**overrides`` so tests can customize fields without
    mutating shared state. Each call returns a new dict.
    """
    base: dict[str, Any] = {
        "id": 11111,
        "user_id": 67890,
        "title": "Test Song",
        "title_unicode": "Test Song",
        "artist": "Test Artist",
        "artist_unicode": "Test Artist",
        "bpm": 180.0,
        "status": "wip",
        "ranked": 0,
        "rating": 4.5,
        "source": "",
        "tags": "test tag",
        "pack_tags": [],
        "storyboard": False,
        "spotlight": False,
        "video": False,
        "nsfw": False,
        "can_be_hyped": True,
        "discussion_enabled": True,
        "discussion_locked": False,
        "is_scoreable": True,
        "favourite_count": 100,
        "play_count": 5000,
        "offset": 0,
        "track_id": None,
        "preview_url": "https://example.com/pre.mp3",
        "legacy_thread_url": None,
        "deleted_at": None,
        "ranked_date": None,
        "creator": "TestCreator",
        "beatmaps": [],
        "availability": {"download_disabled": False, "more_information": None},
        "covers": {
            "cover": "x100",
            "cover_2x": "x200",
            "card": "x100",
            "card_2x": "x200",
            "list": "x100",
            "list_2x": "x200",
            "slimcover": "x100",
            "slimcover_2x": "x200",
        },
        "current_nominations": [],
        "description": {"description": ""},
        "genre": None,
        "hype": {"current": 0, "required": 2},
        "language": None,
        "nominations_summary": {
            "current": 0,
            "eligible_main_rulesets": None,
            "required_meta": {"main_ruleset": 0, "non_main_ruleset": 0},
        },
        "ratings": [],
        "last_updated": "2024-06-15T12:00:00+00:00",
        "submitted_date": "2024-01-01T00:00:00+00:00",
    }
    base.update(overrides)
    return base
