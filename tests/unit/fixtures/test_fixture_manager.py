import pytest
import json
from pathlib import Path
from unittest.mock import MagicMock

import sys

from app.fixtures.manager import FixtureManager


@pytest.fixture
def temp_fixture_dir(tmp_path):
    """Create a temporary fixture directory structure."""
    fixture_dir = tmp_path / "fixtures" / "osu"
    fixture_dir.mkdir(parents=True, exist_ok=True)
    
    beatmaps_dir = fixture_dir / "beatmaps"
    beatmaps_dir.mkdir()
    
    beatmapset_dir = fixture_dir / "beatmapsets"
    beatmapset_dir.mkdir()
    
    users_dir = fixture_dir / "users" / "osu"
    users_dir.mkdir(parents=True)
    
    scores_dir = fixture_dir / "scores" / "best"
    scores_dir.mkdir(parents=True)
    
    beatmap_scores_dir = fixture_dir / "beatmap_scores"
    beatmap_scores_dir.mkdir()
    
    beatmap_attrs_dir = fixture_dir / "beatmap_attributes"
    beatmap_attrs_dir.mkdir()
    
    return fixture_dir


@pytest.fixture
def mock_beatmap_file(temp_fixture_dir):
    """Create a mock beatmap fixture file."""
    beatmap_data = {
        "id": 12345,
        "beatmapset_id": 67890,
        "status": "ranked",
        "ruleset_id": 0,
        "difficulty_rating": 4.5,
        "playcount": 1500,
    }
    
    filepath = temp_fixture_dir / "beatmaps" / "beatmap_12345.json"
    with open(filepath, "w") as f:
        json.dump(beatmap_data, f)
    
    return filepath


@pytest.fixture
def mock_beatmapset_file(temp_fixture_dir):
    """Create a mock beatmapset fixture file."""
    beatmapset_data = {
        "id": 67890,
        "status": "ranked",
    }
    
    filepath = temp_fixture_dir / "beatmapsets" / "beatmapset_67890.json"
    with open(filepath, "w") as f:
        json.dump(beatmapset_data, f)
    
    return filepath


@pytest.fixture
def mock_user_file(temp_fixture_dir):
    """Create a mock user fixture file."""
    user_data = {
        "id": 111111,
        "username": "test_user",
        "statistics": {
            "play_count": 10000,
        },
    }
    
    filepath = temp_fixture_dir / "users" / "osu" / "user_111111_osu.json"
    with open(filepath, "w") as f:
        json.dump(user_data, f)
    
    return filepath


@pytest.fixture
def mock_score_file(temp_fixture_dir):
    """Create a mock score fixture file."""
    score_data = [
        {
            "id": 55555,
            "user_id": 111111,
            "beatmap_id": 12345,
            "rank": "S",
            "mods": [4, 16],
            "score": 950000,
        }
    ]
    
    filepath = temp_fixture_dir / "scores" / "best" / "scores_111111_best.json"
    with open(filepath, "w") as f:
        json.dump(score_data, f)
    
    return filepath


@pytest.fixture
def fixture_manager(temp_fixture_dir, mock_beatmap_file, mock_user_file):
    """Create a FixtureManager with temporary fixture data."""
    metadata = {
        "targeted": {
            "beatmaps": {
                "by_status": {},
                "by_ruleset": {},
                "by_difficulty": {},
                "by_playcount": {},
                "file_metadata": {
                    "12345": {
                        "filepath": str(mock_beatmap_file),
                        "status": "ranked",
                        "ruleset": "osu",
                        "difficulty_rating": 4.5,
                        "playcount": 1500,
                    }
                }
            },
            "beatmapsets": {
                "by_status": {},
                "file_metadata": {},
            },
            "users": {
                "by_activity": {},
                "per_ruleset": {},
                "file_metadata": {
                    "111111": {
                        "filepath": str(mock_user_file),
                        "activity_level": "active",
                        "ruleset": "osu",
                    }
                }
            },
            "scores": {
                "by_rank": {},
                "by_mods": {},
                "file_metadata": {},
            }
        }
    }
    
    return FixtureManager(temp_fixture_dir, metadata)


class TestFixtureManager:
    """Tests for FixtureManager."""
    
    def test_init(self, temp_fixture_dir):
        """Test FixtureManager initialization."""
        manager = FixtureManager(temp_fixture_dir)
        assert manager.fixture_dir == temp_fixture_dir
        assert "targeted" in manager.metadata
    
    def test_get_beatmaps_by_status(self, fixture_manager, mock_beatmap_file):
        """Test getting beatmaps by status preference."""
        beatmaps = fixture_manager.get_beatmaps(
            count=1,
            by_status=["ranked"]
        )
        
        assert len(beatmaps) >= 1
        assert beatmaps[0]["id"] == 12345
        assert beatmaps[0]["status"] == "ranked"
    
    def test_get_beatmaps_by_difficulty(self, fixture_manager):
        """Test getting beatmaps by difficulty preference."""
        beatmaps = fixture_manager.get_beatmaps(
            count=1,
            by_difficulty="medium"
        )
        
        assert len(beatmaps) >= 1
    
    def test_get_beatmaps_by_ruleset(self, fixture_manager):
        """Test getting beatmaps by ruleset preference."""
        beatmaps = fixture_manager.get_beatmaps(
            count=1,
            by_ruleset="osu"
        )
        
        assert len(beatmaps) >= 1
    
    def test_get_users_by_activity(self, temp_fixture_dir):
        """Test getting users by activity level."""
        users_dir = temp_fixture_dir / "users" / "osu"
        users_dir.mkdir(parents=True, exist_ok=True)
        
        user_data = {
            "id": 111111,
            "username": "test_user",
            "statistics": {
                "play_count": 10000,
            },
        }
        
        filepath = users_dir / "user_111111_osu.json"
        with open(filepath, "w") as f:
            json.dump(user_data, f)
        
        metadata = {
            "targeted": {
                "users": {
                    "by_activity": {},
                    "per_ruleset": {},
                    "file_metadata": {
                        "111111": {
                            "filepath": str(filepath),
                            "activity_level": "active",
                            "ruleset": "osu",
                        }
                    }
                },
                "beatmaps": {"file_metadata": {}},
                "beatmapsets": {"file_metadata": {}},
                "scores": {"file_metadata": {}},
            }
        }
        
        manager = FixtureManager(temp_fixture_dir, metadata)
        users = manager.get_users(
            ruleset="osu",
            count=1,
            activity_level="active"
        )
        
        assert len(users) >= 1
        assert users[0]["id"] == 111111
    
    def test_get_beatmapsets_by_status(self, temp_fixture_dir, mock_beatmapset_file):
        """Test getting beatmapsets by status."""
        metadata = {
            "targeted": {
                "beatmapsets": {
                    "file_metadata": {
                        "67890": {
                            "filepath": str(mock_beatmapset_file),
                            "status": "ranked",
                        }
                    }
                }
            }
        }
        
        manager = FixtureManager(temp_fixture_dir, metadata)
        beatmapsets = manager.get_beatmapsets(
            count=1,
            by_status=["ranked"]
        )
        
        assert len(beatmapsets) >= 1
        assert beatmapsets[0]["id"] == 67890
    
    def test_get_scores(self, temp_fixture_dir, mock_score_file):
        """Test getting scores by rank."""
        scores_dir = temp_fixture_dir / "scores" / "best"
        scores_dir.mkdir(parents=True, exist_ok=True)
        
        score_data = [
            {
                "id": 55555,
                "user_id": 111111,
                "beatmap_id": 12345,
                "rank": "S",
                "mods": [4, 16],
                "score": 950000,
            }
        ]
        
        filepath = scores_dir / "scores_111111_best.json"
        with open(filepath, "w") as f:
            json.dump(score_data, f)
        
        metadata = {
            "targeted": {
                "scores": {
                    "by_rank": {},
                    "by_mods": {},
                    "file_metadata": {
                        "55555": {
                            "filepath": str(filepath),
                            "rank": "S",
                            "mods": [4, 16],
                        }
                    }
                },
                "beatmaps": {"file_metadata": {}},
                "beatmapsets": {"file_metadata": {}},
                "users": {"file_metadata": {}},
            }
        }
        
        manager = FixtureManager(temp_fixture_dir, metadata)
        scores = manager.get_scores(
            score_type="best",
            count=1,
            rank_coverage=["S"]
        )
        
        assert len(scores) >= 1
        assert scores[0][0]["rank"] == "S"
    
    def test_coverage_report(self, fixture_manager):
        """Test coverage report generation."""
        coverage = fixture_manager.get_coverage_report()
        
        assert "beatmaps" in coverage
        assert "users" in coverage
        assert "file_metadata" in coverage["beatmaps"]
    
    def test_ensure_coverage(self, fixture_manager):
        """Test ensure_coverage method."""
        targets = {
            "beatmaps": {
                "by_status": {
                    "ranked": 10,
                    "loved": 5,
                }
            }
        }
        
        gaps = fixture_manager.ensure_coverage(targets)
        
        assert "beatmaps" in gaps
    
    def test_get_fixtures_empty_category(self, temp_fixture_dir):
        """Test getting fixtures from empty category."""
        manager = FixtureManager(temp_fixture_dir)
        beatmaps = manager.get_beatmaps(count=5)
        
        assert len(beatmaps) == 0
    
    def test_resolve_preference_empty_metadata(self, temp_fixture_dir):
        """Test resolving preferences when no metadata exists."""
        manager = FixtureManager(temp_fixture_dir)
        
        beatmaps = manager.get_beatmaps(
            count=1,
            by_status=["ranked"]
        )
        
        assert len(beatmaps) == 0


class TestPreferenceMatching:
    """Tests for preference matching logic."""
    
    def test_in_list_match(self, fixture_manager):
        """Test matching values in list."""
        assert fixture_manager._in_list("ranked", ["ranked", "loved"])
        assert not fixture_manager._in_list("graveyard", ["ranked", "loved"])
        assert fixture_manager._in_list(None, ["ranked", "loved"])
    
    def test_in_difficulty_range(self, fixture_manager):
        """Test difficulty range matching."""
        assert fixture_manager._in_difficulty_range(1.5, "easy")
        assert fixture_manager._in_difficulty_range(3.0, "medium")
        assert fixture_manager._in_difficulty_range(6.0, "hard")
        assert fixture_manager._in_difficulty_range(8.0, "expert")
        assert not fixture_manager._in_difficulty_range(8.0, "easy")
    
    def test_in_playcount_range(self, fixture_manager):
        """Test playcount range matching."""
        assert fixture_manager._in_playcount_range(50, "low")
        assert fixture_manager._in_playcount_range(500, "medium")
        assert fixture_manager._in_playcount_range(2000, "high")
        assert not fixture_manager._in_playcount_range(500, "low")
    
    def test_matches_preferences(self, fixture_manager):
        """Test full preference matching."""
        metadata = {
            "status": "ranked",
            "difficulty_rating": 4.5,
            "ruleset": "osu",
            "playcount": 500,
        }
        
        preferences = {
            "by_status": ["ranked"],
            "by_difficulty": "medium",
            "by_ruleset": "osu",
            "by_playcount": "medium",
        }
        
        assert fixture_manager._matches_preferences(metadata, preferences)
    
    def test_matches_preferences_no_match(self, fixture_manager):
        """Test preference matching when no match."""
        metadata = {
            "status": "graveyard",
            "difficulty_rating": 1.0,
        }
        
        preferences = {
            "by_status": ["ranked"],
            "by_difficulty": "medium",
        }
        
        assert not fixture_manager._matches_preferences(metadata, preferences)


class TestMetadataExtraction:
    """Tests for metadata extraction from file paths."""
    
    def test_extract_beatmap_id(self, fixture_manager):
        """Test extracting beatmap ID from filename."""
        path = Path("/fixtures/beatmaps/beatmap_12345.json")
        assert fixture_manager._extract_id_from_path(path, "beatmaps") == 12345
    
    def test_extract_beatmapset_id(self, fixture_manager):
        """Test extracting beatmapset ID from filename."""
        path = Path("/fixtures/beatmapsets/beatmapset_67890.json")
        assert fixture_manager._extract_id_from_path(path, "beatmapsets") == 67890
    
    def test_extract_user_id(self, fixture_manager):
        """Test extracting user ID from filename."""
        path = Path("/fixtures/users/osu/user_111111_osu.json")
        assert fixture_manager._extract_id_from_path(path, "users.osu") == 111111
    
    def test_extract_beatmap_scores_id(self, fixture_manager):
        """Test extracting beatmap scores ID from filename."""
        path = Path("/fixtures/beatmap_scores/beatmap_scores_12345.json")
        assert fixture_manager._extract_id_from_path(path, "beatmap_scores") == 12345
    
    def test_extract_beatmap_attrs_id(self, fixture_manager):
        """Test extracting beatmap attributes ID from filename."""
        path = Path("/fixtures/beatmap_attributes/beatmap_attrs_12345_mods64.json")
        assert fixture_manager._extract_id_from_path(path, "beatmap_attributes") == 12345
