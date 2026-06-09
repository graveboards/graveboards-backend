import pytest
from unittest.mock import MagicMock, AsyncMock, patch
from io import BytesIO
from datetime import datetime

from app.beatmaps.manager import BeatmapManager
from app.redis import RedisClient
from app.database import PostgresqlDB


class TestBeatmapManager:
    """Test beatmap archival/versioning."""

    @pytest.fixture
    def mock_rc(self):
        """Create a mock Redis client."""
        return MagicMock(spec=RedisClient)

    @pytest.fixture
    def mock_db(self):
        """Create a mock database."""
        return MagicMock(spec=PostgresqlDB)

    @pytest.fixture
    def manager(self, mock_rc, mock_db):
        """Create a BeatmapManager instance."""
        return BeatmapManager(rc=mock_rc, db=mock_db)

    def test_initialization(self, mock_rc, mock_db):
        """Test manager initialization."""
        manager = BeatmapManager(rc=mock_rc, db=mock_db)

        assert manager.rc is mock_rc
        assert manager.db is mock_db
        assert manager.oac is not None

    async def test_archive_creates_snapshot(self, manager):
        """Test archive creates snapshot."""
        manager._session = MagicMock()

        mock_beatmapset = {
            "id": 123,
            "beatmaps": [{"id": 1, "checksum": "abc123"}],
            "checksum": "checksum123",
        }

        with patch.object(manager, "oac") as mock_oac:
            mock_oac.get_beatmapset = AsyncMock(return_value=mock_beatmapset)

            with patch.object(manager.db, "get") as mock_get:
                mock_get.return_value = None

                with patch.object(manager, "_populate_beatmapset"):
                    with patch.object(manager, "_snapshot_beatmapset"):
                        with patch.object(manager, "_download"):
                            result = await manager.archive(123)

    async def test_archive_updates_existing(self, manager):
        """Test archive updates existing snapshot."""
        manager._session = MagicMock()

        mock_beatmapset = {
            "id": 123,
            "beatmaps": [{"id": 1, "checksum": "existing_checksum"}],
            "checksum": "existing_checksum",
        }

        with patch.object(manager, "oac") as mock_oac:
            mock_oac.get_beatmapset = AsyncMock(return_value=mock_beatmapset)

            with patch.object(manager.db, "get") as mock_get:
                mock_get.return_value = MagicMock()

                with patch.object(manager, "_populate_beatmapset"):
                    with patch.object(manager, "_update_beatmapset"):
                        result = await manager.archive(123)

    async def test_archive_no_download(self, manager):
        """Test archive without download."""
        manager._session = MagicMock()

        mock_beatmapset = {
            "id": 123,
            "beatmaps": [{"id": 1, "checksum": "new_checksum"}],
            "checksum": "new_checksum",
        }

        with patch.object(manager, "oac") as mock_oac:
            mock_oac.get_beatmapset = AsyncMock(return_value=mock_beatmapset)

            with patch.object(manager.db, "get") as mock_get:
                mock_get.return_value = None

                with patch.object(manager, "_populate_beatmapset"):
                    with patch.object(manager, "_snapshot_beatmapset"):
                        with patch.object(manager, "_download") as mock_download:
                            result = await manager.archive(123, download=False)

                            mock_download.assert_not_called()

    async def test_snapshot_beatmapset(self, manager):
        """Test snapshot beatmapset."""
        manager._session = MagicMock()
        manager._changelog = {"snapshotted_beatmaps": []}

        mock_beatmapset_dict = {
            "id": 123,
            "beatmaps": [],
            "tags": "tag1 tag2",
        }

        with patch("app.beatmaps.manager.BeatmapsetSnapshotSchema") as mock_schema:
            mock_schema.model_validate.return_value.model_dump.return_value = {
                "id": 1,
                "beatmapset_id": 123,
            }

            with patch.object(manager.db, "add") as mock_add:
                mock_add.return_value = MagicMock()

                with patch.object(manager, "_snapshot_beatmaps"):
                    with patch.object(manager, "_populate_beatmapset_tags"):
                        await manager._snapshot_beatmapset(mock_beatmapset_dict)

    async def test_snapshot_beatmaps_reuses_existing(self, manager):
        """Test snapshot beatmaps reuses existing."""
        manager._session = MagicMock()

        mock_beatmaps = [{"id": 1, "checksum": "existing"}]

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = MagicMock()

            with patch.object(manager, "_populate_beatmap_tags"):
                with patch.object(manager, "_populate_owner_profiles"):
                    result = await manager._snapshot_beatmaps(mock_beatmaps)

                    # Should reuse existing, not create new
                    assert result is not None

    async def test_update_beatmapset(self, manager):
        """Test update beatmapset."""
        manager._session = MagicMock()

        mock_beatmapset_dict = {
            "id": 123,
            "beatmaps": [],
            "checksum": "checksum123",
        }

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = MagicMock()

            with patch("app.beatmaps.manager.BeatmapsetOsuApiSchema") as mock_schema:
                mock_schema.model_validate.return_value.model_dump.return_value = {
                    "id": 1,
                }

                with patch.object(manager.db, "update") as mock_update:
                    await manager._update_beatmapset(mock_beatmapset_dict)

    async def test_update_beatmaps(self, manager):
        """Test update beatmaps."""
        manager._session = MagicMock()

        mock_beatmaps = [{"id": 1, "checksum": "checksum123"}]

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = MagicMock()

            with patch("app.beatmaps.manager.BeatmapOsuApiSchema") as mock_schema:
                mock_schema.model_validate.return_value.model_dump.return_value = {
                    "id": 1,
                }

                await manager._update_beatmaps(mock_beatmaps)

    async def test_populate_beatmapset(self, manager):
        """Test populate beatmapset."""
        manager._session = MagicMock()

        mock_beatmapset_dict = {
            "id": 123,
            "user_id": 456,
            "beatmaps": [{"id": 1, "user_id": 456}],
        }

        with patch.object(manager, "_populate_user"):
            with patch.object(manager, "_populate_beatmap"):
                await manager._populate_beatmapset(mock_beatmapset_dict)

    async def test_populate_user(self, manager):
        """Test populate user."""
        manager._session = MagicMock()

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = None

            with patch.object(manager.db, "add") as mock_add:
                mock_add.return_value = MagicMock()

                with patch.object(manager, "_populate_profile"):
                    with patch.object(manager.db, "get") as mock_profile_get:
                        mock_profile_get.return_value = MagicMock()
                        user = await manager._populate_user(123)

                        assert user is not None

    async def test_populate_profile(self, manager):
        """Test populate profile."""
        manager._session = MagicMock()

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = None

            with patch.object(manager, "oac") as mock_oac:
                mock_oac.get_user = AsyncMock(return_value={"id": 123})

                with patch("app.beatmaps.manager.ProfileSchema") as mock_schema:
                    mock_schema.model_validate.return_value.model_dump.return_value = {
                        "id": 1,
                        "user_id": 123,
                    }

                    with patch.object(manager.db, "add") as mock_add:
                        mock_add.return_value = MagicMock()

                        with patch("app.beatmaps.manager.Namespace") as mock_namespace:
                            mock_namespace.LOCK.hash_name.return_value = "lock_key"

                            with patch.object(manager.rc, "lock_ctx"):
                                profile = await manager._populate_profile(123)

                                assert profile is not None

    async def test_populate_owner_profiles(self, manager):
        """Test populate owner profiles."""
        manager._session = MagicMock()

        owners = [{"id": 123}]

        with patch.object(manager, "_populate_user"):
            with patch.object(manager, "_populate_profile"):
                profiles = await manager._populate_owner_profiles(owners)

                assert profiles is not None

    async def test_populate_beatmapset_tags(self, manager):
        """Test populate beatmapset tags."""
        manager._session = MagicMock()

        tags_str = "tag1 tag2 tag3"

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = None

            with patch.object(manager.db, "add") as mock_add:
                mock_add.return_value = MagicMock()

                tags = await manager._populate_beatmapset_tags(tags_str)

                assert tags is not None

    async def test_populate_beatmap_tags(self, manager):
        """Test populate beatmap tags."""
        manager._session = MagicMock()

        top_tag_ids = [{"tag_id": 1}]

        with patch.object(manager, "_update_beatmap_tags_from_osu"):
            with patch.object(manager.db, "get") as mock_get:
                mock_get.return_value = MagicMock()

                tags = await manager._populate_beatmap_tags(top_tag_ids)

                assert tags is not None

    async def test_download_beatmaps(self, manager):
        """Test download beatmaps."""
        manager._session = MagicMock()

        beatmap_ids = [1, 2, 3]

        with patch("app.beatmaps.manager.httpx") as mock_httpx:
            mock_client = MagicMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock()
            mock_httpx.AsyncClient.return_value = mock_client

            with patch("app.beatmaps.manager.aiofiles") as mock_aiofiles:
                mock_file = MagicMock()
                mock_file.__aenter__ = AsyncMock(return_value=mock_file)
                mock_file.__aexit__ = AsyncMock()
                mock_aiofiles.open.return_value = mock_file

                with patch.object(manager.db, "get") as mock_get:
                    mock_get.return_value = MagicMock()

                    await manager._download(beatmap_ids)

    async def test_get_beatmap_snapshot(self, manager):
        """Test get beatmap snapshot."""
        manager._session = MagicMock()

        with patch("app.beatmaps.manager.aiofiles") as mock_aiofiles:
            mock_file = MagicMock()
            mock_file.__aenter__ = AsyncMock(return_value=mock_file)
            mock_file.read.return_value = b"test data"
            mock_aiofiles.open.return_value = mock_file

            result = await BeatmapManager.get(123, 1)

            assert result == b"test data"

    async def test_get_beatmap_path(self, manager):
        """Test get beatmap path."""
        result = BeatmapManager.get_path(123, 1)

        assert isinstance(result, str)

    async def test_get_zip(self, manager):
        """Test get zip archive."""
        manager._session = MagicMock()

        with patch.object(manager.db, "get") as mock_get:
            mock_get.return_value = MagicMock()
            mock_get.return_value.beatmap_snapshots = []

            result = await manager.get_zip(123)

            assert isinstance(result, BytesIO)

    def test_reset_changelog(self, manager):
        """Test reset changelog."""
        manager._changelog = {
            "snapshotted_beatmapset": {"id": 1},
            "snapshotted_beatmaps": [{"id": 2}],
            "updated_beatmapset": {"id": 3},
            "updated_beatmaps": [{"id": 4}],
        }

        manager._reset_changelog()

        assert manager._changelog == {
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
            "updated_beatmapset": None,
            "updated_beatmaps": []
        }

    def test_get_changelog_structure(self, manager):
        """Test changelog structure."""
        manager._reset_changelog()

        assert "snapshotted_beatmapset" in manager._changelog
        assert "snapshotted_beatmaps" in manager._changelog
        assert "updated_beatmapset" in manager._changelog
        assert "updated_beatmaps" in manager._changelog
