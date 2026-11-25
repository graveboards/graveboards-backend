from types import SimpleNamespace

from pydantic import TypeAdapter

from app.database.schemas import BeatmapSnapshotSchema
from app.database.schemas.sub_schemas.beatmap_osu_api_schema import Owner
from tests._helpers.osu_api_utils import _create_mock_beatmap


class TestBeatmapSnapshotSchemaOwners:
    """Owner records for deleted or restricted accounts carry no username."""

    @staticmethod
    def _payload(**overrides):
        return _create_mock_beatmap(beatmap_id=100001, **overrides)

    def test_accepts_owner_with_null_username(self) -> None:
        schema = BeatmapSnapshotSchema.model_validate(
            self._payload(owners=[{"id": 1000, "username": None}])
        )

        assert schema.owners == [{"id": 1000, "username": None}]

    def test_accepts_owner_without_username_key(self) -> None:
        schema = BeatmapSnapshotSchema.model_validate(self._payload(owners=[{"id": 1000}]))

        assert schema.owners == [{"id": 1000}]

    def test_owner_rebuilt_from_profile_without_username(self) -> None:
        """Mirrors the listing read path, where owners are rebuilt from profiles."""
        row = SimpleNamespace(
            beatmap_id=100001,
            owner_profiles=[SimpleNamespace(user_id=1000, username=None)],
        )

        validated = BeatmapSnapshotSchema.from_snapshot(row)

        assert TypeAdapter(list[Owner]).validate_python(validated.owners) == [
            {"id": 1000, "username": None}
        ]
