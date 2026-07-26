from __future__ import annotations

from typing import Any

from app.database.rules.context import ExecutionContext
from app.database.rules.validators.metadata.song_identity import MetadataProvider


class CreatorIdentityProvider(MetadataProvider):
    @property
    def name(self) -> str:
        return "creator_identity"

    async def resolve(self, context: ExecutionContext) -> dict[str, Any]:
        beatmapset = context.beatmapset
        beatmaps = context.beatmaps or []

        creator_id = beatmapset.user_id if beatmapset else 0
        creator_username = beatmapset.creator if beatmapset else ""

        mapper_ids: list[int] = []
        mapper_usernames: list[str] = []

        seen_ids: set[int] = set()
        for bm in beatmaps:
            if not bm.owners:
                continue

            for owner in bm.owners:
                if not isinstance(owner, dict) or not owner:
                    continue

                owner_id: int | None = owner.get("id")
                owner_username: str | None = owner.get("username")
                if owner_id and owner_id not in seen_ids:
                    seen_ids.add(owner_id)
                    mapper_ids.append(owner_id)
                    if owner_username:
                        mapper_usernames.append(str(owner_username))

        return {
            "artist_creator_id": creator_id,
            "artist_creator_username": creator_username,
            "mapper_ids": mapper_ids,
            "mapper_usernames": mapper_usernames,
        }
