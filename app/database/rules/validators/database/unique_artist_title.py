from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from pydantic import BaseModel
from sqlalchemy import select

from app.database.models import Request
from app.database.models.beatmapset_snapshot import BeatmapsetSnapshot
from app.database.rules.base import DatabaseRestrictionBase
from app.database.rules.exceptions import RuleViolationError
from app.database.rules.validators.metadata.song_identity import normalized_identity_forms

if TYPE_CHECKING:
    from app.database.rules.context import ExecutionContext

logger = logging.getLogger(__name__)


class UniqueArtistTitleConfig(BaseModel):
    normalize_versions: bool = True


class UniqueArtistTitleRestriction(DatabaseRestrictionBase):
    type = "unique_artist_title"
    config_schema = UniqueArtistTitleConfig
    supported_versions = {"1.0"}

    async def check_database(self, context: ExecutionContext) -> None:
        config = UniqueArtistTitleConfig(**context.config)
        identity = await context.get_metadata("song_identity")

        candidate_forms = normalized_identity_forms(
            identity.get("artist", ""),
            identity.get("title", ""),
            identity.get("artist_unicode", ""),
            identity.get("title_unicode", ""),
            strip_version_markers=config.normalize_versions,
        )
        if not candidate_forms:
            raise RuleViolationError(
                self.type,
                "Could not resolve song identity for uniqueness check",
            )

        session = context.session
        if session is None:
            raise RuleViolationError(
                self.type,
                "Database session unavailable for queue uniqueness check",
            )

        current_beatmapset_id = context.beatmapset.id if context.beatmapset else None

        stmt = (
            select(
                BeatmapsetSnapshot.artist,
                BeatmapsetSnapshot.title,
                BeatmapsetSnapshot.artist_unicode,
                BeatmapsetSnapshot.title_unicode,
                Request.beatmapset_id,
            )
            .join(Request, Request.beatmapset_snapshot_id == BeatmapsetSnapshot.id)
            .where(Request.queue_id == context.queue_id)
        )
        rows = (await session.execute(stmt)).all()

        for artist, title, artist_unicode, title_unicode, beatmapset_id in rows:
            # Exclude the beatmapset being submitted; a resubmission of the same
            # set is handled by the (beatmapset_id, queue_id) uniqueness constraint.
            if current_beatmapset_id is not None and beatmapset_id == current_beatmapset_id:
                continue

            existing_forms = normalized_identity_forms(
                artist,
                title,
                artist_unicode,
                title_unicode,
                strip_version_markers=config.normalize_versions,
            )
            if candidate_forms & existing_forms:
                raise RuleViolationError(
                    self.type,
                    f"Song '{identity['artist']} - {identity['title']}' already "
                    f"has a request in this queue (beatmapset_id={beatmapset_id})",
                )
