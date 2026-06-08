import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.unit.osu_api.test_utils import (
    _create_mock_beatmap,
    _create_mock_beatmapset,
    _create_mock_user,
    _create_mock_score,
    _create_mock_beatmap_scores,
    _create_mock_beatmap_attributes,
    _create_mock_tags,
    _create_mock_rankings_user,
)


def _get_beatmap_with_fallback(fixture_manager):
    beatmaps = fixture_manager.get_beatmaps(by_status=["ranked"], count=1)
    if beatmaps:
        return beatmaps[0]
    else:
        return _create_mock_beatmap()


def _get_beatmapset_with_fallback(fixture_manager):
    beatmapsets = fixture_manager.get_beatmapsets(by_status=["ranked"], count=1)
    if beatmapsets:
        return beatmapsets[0]
    else:
        return _create_mock_beatmapset()


def _get_user_with_fallback(fixture_manager, ruleset="osu"):
    users = fixture_manager.get_users(ruleset=ruleset, count=1)
    if users:
        return users[0]
    else:
        return _create_mock_user(ruleset=ruleset)


def _get_scores_with_fallback(fixture_manager, score_type="best"):
    scores = fixture_manager.get_scores(score_type=score_type, count=1)
    if scores:
        return scores[0]
    else:
        return [_create_mock_score()]


def _get_beatmap_scores_with_fallback(fixture_manager):
    scores = fixture_manager.get_beatmap_scores(count=1)
    if scores:
        return scores[0] if scores else _create_mock_beatmap_scores()
    else:
        return _create_mock_beatmap_scores()


def _get_beatmap_attributes_with_fallback(fixture_manager):
    attrs = fixture_manager.get_beatmap_attributes()
    if attrs:
        return attrs
    else:
        return _create_mock_beatmap_attributes()
