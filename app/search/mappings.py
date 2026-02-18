from sqlalchemy.orm.strategy_options import selectinload, noload, joinedload

from app.database.models import ModelClass, BeatmapSnapshot, BeatmapsetSnapshot, Queue, Request
from app.database.schemas import BeatmapSnapshotSchema, BeatmapsetSnapshotSchema, QueueSchema, RequestSchema
from .enums import Scope, SearchableFieldCategory, ModelField

__all__ = [
    "SCOPE_MODEL_MAPPING",
    "SCOPE_SCHEMA_MAPPING",
    "SCOPE_OPTIONS_MAPPING",
    "SCOPE_CATEGORIES_MAPPING",
    "CATEGORY_MODEL_FIELDS_MAPPING",
    "CATEGORY_FIELD_GROUPS_MAPPING"
]

SCOPE_MODEL_MAPPING = {
    Scope.BEATMAPS: ModelClass.BEATMAP_SNAPSHOT,
    Scope.BEATMAPSETS: ModelClass.BEATMAPSET_SNAPSHOT,
    Scope.SCORES: ...,
    Scope.QUEUES: ModelClass.QUEUE,
    Scope.REQUESTS: ModelClass.REQUEST
}
"""Maps search ``Scope`` to its underlying ``ModelClass``.

Defines which root model a query operates against.
"""

SCOPE_SCHEMA_MAPPING = {
    Scope.BEATMAPS: BeatmapSnapshotSchema,
    Scope.BEATMAPSETS: BeatmapsetSnapshotSchema,
    Scope.SCORES: ...,
    Scope.QUEUES: QueueSchema,
    Scope.REQUESTS: RequestSchema
}
"""Maps search ``Scope`` to its response serialization schema.

Determines how results are serialized for each scope.
"""

SCOPE_OPTIONS_MAPPING = {
    Scope.BEATMAPS: (
        selectinload(BeatmapSnapshot.beatmap_tags),
        selectinload(BeatmapSnapshot.owner_profiles),
        selectinload(BeatmapSnapshot.beatmapset_snapshots)
        .options(
            noload(BeatmapsetSnapshot.beatmap_snapshots),
            selectinload(BeatmapsetSnapshot.beatmapset_tags),
            joinedload(BeatmapsetSnapshot.user_profile)
        ),
        noload(BeatmapSnapshot.leaderboard)
    ),
    Scope.BEATMAPSETS: (
        selectinload(BeatmapsetSnapshot.beatmap_snapshots)
        .options(
            selectinload(BeatmapSnapshot.beatmap_tags),
            selectinload(BeatmapSnapshot.owner_profiles),
            noload(BeatmapSnapshot.beatmapset_snapshots),
            noload(BeatmapSnapshot.leaderboard)
        ),
        selectinload(BeatmapsetSnapshot.beatmapset_tags),
        joinedload(BeatmapsetSnapshot.user_profile)
    ),
    Scope.SCORES: ...,
    Scope.QUEUES: (
        noload(Queue.managers),
        joinedload(Queue.user_profile),
        selectinload(Queue.manager_profiles),
        selectinload(Queue.requests)
        .options(
            joinedload(Request.beatmapset_snapshot)
            .options(
                selectinload(BeatmapsetSnapshot.beatmap_snapshots)
                .options(
                    selectinload(BeatmapSnapshot.beatmap_tags),
                    selectinload(BeatmapSnapshot.owner_profiles),
                    noload(BeatmapSnapshot.beatmapset_snapshots),
                    noload(BeatmapSnapshot.leaderboard)
                ),
                selectinload(BeatmapsetSnapshot.beatmapset_tags),
                joinedload(BeatmapsetSnapshot.user_profile)
            ),
            noload(Request.user_profile),
            noload(Request.queue)
        )
    ),
    Scope.REQUESTS: (
        joinedload(Request.beatmapset_snapshot)
        .options(
            selectinload(BeatmapsetSnapshot.beatmap_snapshots)
            .options(
                selectinload(BeatmapSnapshot.beatmap_tags),
                selectinload(BeatmapSnapshot.owner_profiles),
                noload(BeatmapSnapshot.beatmapset_snapshots),
                noload(BeatmapSnapshot.leaderboard)
            ),
            selectinload(BeatmapsetSnapshot.beatmapset_tags),
            joinedload(BeatmapsetSnapshot.user_profile)
        ),
        joinedload(Request.user_profile),
        joinedload(Request.queue)
        .options(
            noload(Queue.managers),
            joinedload(Queue.user_profile),
            selectinload(Queue.manager_profiles),
            noload(Queue.requests)
        )
    )
}
"""Eager-loading strategy per ``Scope``.

Defines ORM loading behavior (selectinload/joinedload/noload) to optimize query 
execution and prevent N+1 issues.
"""

SCOPE_CATEGORIES_MAPPING = {
    Scope.BEATMAPS: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET],
    Scope.BEATMAPSETS: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET],
    Scope.SCORES: ...,
    Scope.QUEUES: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET, SearchableFieldCategory.QUEUE, SearchableFieldCategory.REQUEST],
    Scope.REQUESTS: [SearchableFieldCategory.BEATMAP, SearchableFieldCategory.BEATMAPSET, SearchableFieldCategory.REQUEST]
}
"""Allowed ``SearchableFieldCategory`` values per ``Scope``.

Constrains which field categories may be used in a given query scope.
"""

CATEGORY_MODEL_FIELDS_MAPPING = {
    SearchableFieldCategory.BEATMAP: {
        "version": ModelField.BEATMAPSNAPSHOT__VERSION
    },
    SearchableFieldCategory.BEATMAPSET: {
        "title": ModelField.BEATMAPSETSNAPSHOT__TITLE,
        "title_unicode": ModelField.BEATMAPSETSNAPSHOT__TITLE_UNICODE,
        "artist": ModelField.BEATMAPSETSNAPSHOT__ARTIST,
        "artist_unicode": ModelField.BEATMAPSETSNAPSHOT__ARTIST_UNICODE,
        "creator": ModelField.BEATMAPSETSNAPSHOT__CREATOR,
        "source": ModelField.BEATMAPSETSNAPSHOT__SOURCE,
        "tags": ModelField.BEATMAPSETSNAPSHOT__TAGS,
        "description": ModelField.BEATMAPSETSNAPSHOT__DESCRIPTION__DESCRIPTION
    },
    SearchableFieldCategory.QUEUE: {
        "name": ModelField.QUEUE__NAME,
        "description": ModelField.QUEUE__DESCRIPTION
    },
    SearchableFieldCategory.REQUEST: {
        "comment": ModelField.REQUEST__COMMENT
    }
}
"""Public field name to `ModelField` mapping per category.

Acts as an allow-list for searchable fields within each category.
"""

CATEGORY_FIELD_GROUPS_MAPPING = {
    SearchableFieldCategory.BEATMAPSET: {
        "title": {"title", "title_unicode"},
        "artist": {"artist", "artist_unicode"}
    }
}
"""Logical field group definitions per category.

Allows grouped searching across multiple related fields.
"""
