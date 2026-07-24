from app.search.enums import Scope, SearchableFieldCategory
from app.search.mappings import (
    CATEGORY_FIELD_GROUPS_MAPPING,
    CATEGORY_MODEL_FIELDS_MAPPING,
    SCOPE_CATEGORIES_MAPPING,
    SCOPE_MODEL_MAPPING,
    SCOPE_SCHEMA_MAPPING,
)


class TestScopeModelMapping:
    """Test SCOPE_MODEL_MAPPING."""

    def test_beatmaps_scope_model(self) -> None:
        """Test beatmaps scope maps to beatmap snapshot model."""
        from app.database.models import ModelClass

        assert SCOPE_MODEL_MAPPING[Scope.BEATMAPS] == ModelClass.BEATMAP_SNAPSHOT

    def test_beatmapsets_scope_model(self) -> None:
        """Test beatmapsets scope maps to beatmapset snapshot model."""
        from app.database.models import ModelClass

        assert SCOPE_MODEL_MAPPING[Scope.BEATMAPSETS] == ModelClass.BEATMAPSET_SNAPSHOT

    def test_queues_scope_model(self) -> None:
        """Test queues scope maps to queue model."""
        from app.database.models import ModelClass

        assert SCOPE_MODEL_MAPPING[Scope.QUEUES] == ModelClass.QUEUE

    def test_requests_scope_model(self) -> None:
        """Test requests scope maps to request model."""
        from app.database.models import ModelClass

        assert SCOPE_MODEL_MAPPING[Scope.REQUESTS] == ModelClass.REQUEST


class TestScopeSchemaMapping:
    """Test SCOPE_SCHEMA_MAPPING."""

    def test_beatmaps_scope_schema(self) -> None:
        """Test beatmaps scope maps to beatmap snapshot schema."""
        from app.database.schemas import BeatmapSnapshotSchema

        assert SCOPE_SCHEMA_MAPPING[Scope.BEATMAPS] == BeatmapSnapshotSchema

    def test_beatmapsets_scope_schema(self) -> None:
        """Test beatmapsets scope maps to beatmapset snapshot schema."""
        from app.database.schemas import BeatmapsetSnapshotSchema

        assert SCOPE_SCHEMA_MAPPING[Scope.BEATMAPSETS] == BeatmapsetSnapshotSchema

    def test_queues_scope_schema(self) -> None:
        """Test queues scope maps to queue schema."""
        from app.database.schemas import QueueSchema

        assert SCOPE_SCHEMA_MAPPING[Scope.QUEUES] == QueueSchema

    def test_requests_scope_schema(self) -> None:
        """Test requests scope maps to request schema."""
        from app.database.schemas import RequestSchema

        assert SCOPE_SCHEMA_MAPPING[Scope.REQUESTS] == RequestSchema


class TestScopeCategoriesMapping:
    """Test SCOPE_CATEGORIES_MAPPING."""

    def test_beatmaps_categories(self) -> None:
        """Test beatmaps scope has beatmap and beatmapset categories."""
        categories = SCOPE_CATEGORIES_MAPPING[Scope.BEATMAPS]

        assert SearchableFieldCategory.BEATMAP in categories
        assert SearchableFieldCategory.BEATMAPSET in categories

    def test_beatmapsets_categories(self) -> None:
        """Test beatmapsets scope has beatmap and beatmapset categories."""
        categories = SCOPE_CATEGORIES_MAPPING[Scope.BEATMAPSETS]

        assert SearchableFieldCategory.BEATMAP in categories
        assert SearchableFieldCategory.BEATMAPSET in categories

    def test_queues_categories(self) -> None:
        """Test queues scope has multiple categories."""
        categories = SCOPE_CATEGORIES_MAPPING[Scope.QUEUES]

        assert SearchableFieldCategory.BEATMAP in categories
        assert SearchableFieldCategory.BEATMAPSET in categories
        assert SearchableFieldCategory.QUEUE in categories
        assert SearchableFieldCategory.REQUEST in categories

    def test_requests_categories(self) -> None:
        """Test requests scope has multiple categories."""
        categories = SCOPE_CATEGORIES_MAPPING[Scope.REQUESTS]

        assert SearchableFieldCategory.BEATMAP in categories
        assert SearchableFieldCategory.BEATMAPSET in categories
        assert SearchableFieldCategory.REQUEST in categories


class TestCategoryModelFieldsMapping:
    """Test CATEGORY_MODEL_FIELDS_MAPPING."""

    def test_beatmap_category_fields(self) -> None:
        """Test beatmap category has version field."""
        fields = CATEGORY_MODEL_FIELDS_MAPPING[SearchableFieldCategory.BEATMAP]

        assert "version" in fields

    def test_beatmapset_category_fields(self) -> None:
        """Test beatmapset category has title and artist fields."""
        fields = CATEGORY_MODEL_FIELDS_MAPPING[SearchableFieldCategory.BEATMAPSET]

        assert "title" in fields
        assert "artist" in fields
        assert "creator" in fields
        assert "tags" in fields

    def test_queue_category_fields(self) -> None:
        """Test queue category has name and description fields."""
        fields = CATEGORY_MODEL_FIELDS_MAPPING[SearchableFieldCategory.QUEUE]

        assert "name" in fields
        assert "description" in fields

    def test_request_category_fields(self) -> None:
        """Test request category has comment field."""
        fields = CATEGORY_MODEL_FIELDS_MAPPING[SearchableFieldCategory.REQUEST]

        assert "comment" in fields


class TestCategoryFieldGroupsMapping:
    """Test CATEGORY_FIELD_GROUPS_MAPPING."""

    def test_beatmapset_field_groups(self) -> None:
        """Test beatmapset category has title and artist groups."""
        groups = CATEGORY_FIELD_GROUPS_MAPPING[SearchableFieldCategory.BEATMAPSET]

        assert "title" in groups
        assert "artist" in groups

    def test_beatmapset_title_group_fields(self) -> None:
        """Test beatmapset title group contains title variants."""
        groups = CATEGORY_FIELD_GROUPS_MAPPING[SearchableFieldCategory.BEATMAPSET]

        assert "title" in groups["title"]
        assert "title_unicode" in groups["title"]

    def test_beatmapset_artist_group_fields(self) -> None:
        """Test beatmapset artist group contains artist variants."""
        groups = CATEGORY_FIELD_GROUPS_MAPPING[SearchableFieldCategory.BEATMAPSET]

        assert "artist" in groups["artist"]
        assert "artist_unicode" in groups["artist"]
