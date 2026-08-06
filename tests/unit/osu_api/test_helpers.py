from typing import Any

from tests.unit.osu_api.test_utils import (
    _create_mock_beatmap,
    _create_mock_beatmap_attributes,
    _create_mock_beatmap_scores,
    _create_mock_beatmapset,
    _create_mock_score,
    _create_mock_user,
)


def _get_beatmap_with_fallback(fixture_manager: Any) -> Any:
    beatmaps = fixture_manager.get_beatmaps(by_status=["ranked"], count=1)
    if beatmaps:
        return beatmaps[0]
    return _create_mock_beatmap()


def _get_beatmapset_with_fallback(fixture_manager: Any) -> Any:
    beatmapsets = fixture_manager.get_beatmapsets(by_status=["ranked"], count=1)
    if beatmapsets:
        return beatmapsets[0]
    return _create_mock_beatmapset()


def _get_user_with_fallback(fixture_manager: Any, ruleset: str = "osu") -> Any:
    users = fixture_manager.get_users(ruleset=ruleset, count=1)
    if users:
        return users[0]
    return _create_mock_user(ruleset=ruleset)


def _get_scores_with_fallback(fixture_manager: Any, score_type: str = "best") -> Any:
    scores = fixture_manager.get_scores(score_type=score_type, count=1)
    if scores:
        return scores[0]
    return [_create_mock_score()]


def _get_beatmap_scores_with_fallback(fixture_manager: Any) -> Any:
    scores = fixture_manager.get_beatmap_scores(count=1)
    if scores:
        return scores[0] if scores else _create_mock_beatmap_scores()
    return _create_mock_beatmap_scores()


def _get_beatmap_attributes_with_fallback(fixture_manager: Any) -> Any:
    attrs = fixture_manager.get_beatmap_attributes()
    if attrs:
        return attrs
    return _create_mock_beatmap_attributes()
