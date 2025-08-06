from sqlalchemy.sql.schema import Table, Column, ForeignKey
from sqlalchemy.sql.sqltypes import Integer

from .base import Base

user_role_association = Table(
    "user_role_association", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True),
    Column("role_id", Integer, ForeignKey("roles.id"), primary_key=True)
)

beatmap_snapshot_beatmapset_snapshot_association = Table(
    "beatmap_snapshot_beatmapset_snapshot_association", Base.metadata,
    Column("beatmap_snapshot_id", Integer, ForeignKey("beatmap_snapshots.id"), primary_key=True),
    Column("beatmapset_snapshot_id", Integer, ForeignKey("beatmapset_snapshots.id"), primary_key=True)
)

queue_manager_association = Table(
    "queue_manager_association", Base.metadata,
    Column("queue_id", Integer, ForeignKey("queues.id"), primary_key=True),
    Column("user_id", Integer, ForeignKey("users.id"), primary_key=True)
)

beatmapset_tag_beatmapset_snapshot_association = Table(
    "beatmapset_tag_beatmapset_snapshot_association", Base.metadata,
    Column("beatmapset_tag_id", Integer, ForeignKey("beatmapset_tags.id"), primary_key=True),
    Column("beatmapset_snapshot_id", Integer, ForeignKey("beatmapset_snapshots.id"), primary_key=True)
)

beatmap_tag_beatmap_snapshot_association = Table(
    "beatmap_tag_beatmap_snapshot_association", Base.metadata,
    Column("beatmap_tag_id", Integer, ForeignKey("beatmap_tags.id"), primary_key=True),
    Column("beatmap_snapshot_id", Integer, ForeignKey("beatmap_snapshots.id"), primary_key=True)
)

beatmap_snapshot_owner_association = Table(
    "beatmap_snapshot_owner_association", Base.metadata,
    Column("profile_id", Integer, ForeignKey("profiles.id"), primary_key=True),
    Column("beatmap_snapshot_id", Integer, ForeignKey("beatmap_snapshots.id"), primary_key=True)
)
