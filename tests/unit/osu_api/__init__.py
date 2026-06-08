from pathlib import Path
import sys

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
from tests.unit.osu_api.test_helpers import (
    _get_beatmap_with_fallback,
    _get_beatmapset_with_fallback,
    _get_user_with_fallback,
    _get_scores_with_fallback,
    _get_beatmap_scores_with_fallback,
    _get_beatmap_attributes_with_fallback,
)
