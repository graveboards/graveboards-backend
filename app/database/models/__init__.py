"""SQLAlchemy ORM models and association tables for the data layer.

Re-exports every mapped model class and association table for convenient
single-module imports (e.g. ``from app.database.models import User``).
"""

from __future__ import annotations

from .api_key import ApiKey
from .associations import (
    beatmap_snapshot_beatmapset_snapshot_association,
    beatmap_snapshot_owner_association,
    beatmap_tag_beatmap_snapshot_association,
    beatmapset_tag_beatmapset_snapshot_association,
    queue_manager_association,
    user_role_association,
)
from .audit_log import AuditLog
from .base import Base, BaseType
from .beatmap import Beatmap
from .beatmap_listing import BeatmapListing
from .beatmap_snapshot import BeatmapSnapshot
from .beatmap_tag import BeatmapTag
from .beatmapset import Beatmapset
from .beatmapset_listing import BeatmapsetListing
from .beatmapset_snapshot import BeatmapsetSnapshot
from .beatmapset_tag import BeatmapsetTag
from .leaderboard import Leaderboard
from .model_class import ModelClass
from .oauth_token import OAuthToken
from .profile import Profile
from .profile_fetcher_task import ProfileFetcherTask
from .queue import Queue
from .queue_rule import QueueRule
from .request import Request
from .role import Role
from .score import Score
from .score_fetcher_task import ScoreFetcherTask
from .user import User

__all__ = [
    "ApiKey",
    "AuditLog",
    "Base",
    "BaseType",
    "Beatmap",
    "BeatmapListing",
    "BeatmapSnapshot",
    "BeatmapTag",
    "Beatmapset",
    "BeatmapsetListing",
    "BeatmapsetSnapshot",
    "BeatmapsetTag",
    "Leaderboard",
    "ModelClass",
    "OAuthToken",
    "Profile",
    "ProfileFetcherTask",
    "Queue",
    "QueueRule",
    "Request",
    "Role",
    "Score",
    "ScoreFetcherTask",
    "User",
    "beatmap_snapshot_beatmapset_snapshot_association",
    "beatmap_snapshot_owner_association",
    "beatmap_tag_beatmap_snapshot_association",
    "beatmapset_tag_beatmapset_snapshot_association",
    "queue_manager_association",
    "user_role_association",
]
