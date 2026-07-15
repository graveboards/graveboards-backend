import os
import json
import asyncio
import hashlib
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy.ext.asyncio.session import AsyncSession

from app.database import PostgresqlDB
from app.database.models import (
    Profile,
    BeatmapTag,
    BeatmapsetTag,
    User,
    BeatmapSnapshot,
    BeatmapsetSnapshot,
    Beatmapset,
    Beatmap,
)
from app.database.schemas import (
    BeatmapSnapshotSchema,
    BeatmapsetSnapshotSchema,
    ProfileSchema,
)
from app.database.crud import session_manager, db_session_resolver
from app.database.seeding import SeederTarget
from app.database.seeding.event import SeedEvent
from .base import Seeder

BEATMAP_TAGS_PATH = Path("instance/fixtures/beatmap_tags.json")


class BeatmapSeeder(Seeder):
    def __init__(self, db: PostgresqlDB):
        super().__init__(db)
        self._beatmap_tags: list[dict] = []

    def set_data(self, data: list[dict]) -> None:
        """Inject fixture data loaded by the fixture loader."""
        super().set_data(data)
        self.total = len([bm for bs in self.data for bm in bs.get("beatmaps", [])])

    def set_beatmap_tags(self, tags: list[dict]) -> None:
        """Inject beatmap tag data loaded by the fixture loader."""
        self._beatmap_tags = tags

    @session_manager(session_resolver=db_session_resolver, autoflush_allowed=False)
    async def seed(self, queue: asyncio.Queue[SeedEvent | None], session: AsyncSession = None):
        self.queue = queue
        self.session = session
        await queue.put(SeedEvent(SeederTarget.BEATMAP, self.progress, self.total))
        await self._seed_beatmap_tags()

        for beatmapset_entry in self.data:
            await self._seed_beatmapset(beatmapset_entry)

    async def _seed_beatmap_tags(self):
        if self._beatmap_tags:
            tag_data = self._beatmap_tags
        elif BEATMAP_TAGS_PATH.exists():
            with open(BEATMAP_TAGS_PATH) as f:
                tag_data = json.load(f)
            tag_data = Seeder._normalize_datetimes(tag_data)
        else:
            return

        for beatmap_tag_entry in tag_data:
            if not await self.db.get(BeatmapTag, id=beatmap_tag_entry["id"], session=self.session):
                await self.db.add(BeatmapTag, **beatmap_tag_entry, session=self.session)

    async def _seed_beatmapset(self, beatmapset_entry: dict):
        """Seed a beatmapset following BeatmapManager pattern."""
        beatmapset_id = beatmapset_entry["id"]
        user_id = beatmapset_entry["user_id"]

        # 1. Ensure user exists (with restricted user handling)
        await self._ensure_user(user_id, beatmapset_entry.get("user", {}))

        # 2. Ensure Beatmapset exists
        if not await self.db.get(Beatmapset, id=beatmapset_id, session=self.session):
            await self.db.add(Beatmapset, id=beatmapset_id, user_id=user_id, session=self.session)

        # 3. Seed beatmaps and collect their snapshots
        bms_bm_mapping: dict[int, list[dict]] = {}
        beatmaps = beatmapset_entry.get("beatmaps", [])
        
        if not beatmaps:
            self.logger.debug(f"Skipping beatmapset {beatmapset_id}: no beatmaps in fixture data")
            return

        for beatmap_entry in beatmaps:
            added_bm_dict = await self._seed_beatmap(beatmap_entry)
            bms_bm_mapping.setdefault(beatmapset_id, []).extend(added_bm_dict)

        # 4. Generate BeatmapsetSnapshot using schema validation
        if bms_bm_mapping.get(beatmapset_id):
            await self._generate_bms_snapshot(beatmapset_entry, bms_bm_mapping)

    async def _ensure_user(self, user_id: int, user_dict: dict = None):
        """Ensure User and Profile exist, handling restricted users.
        
        Follows BeatmapManager._populate_user pattern.
        """
        if not await self.db.get(User, id=user_id, session=self.session):
            await self.db.add(User, id=user_id, session=self.session)

        # Try to populate profile
        try:
            if user_dict:
                # Use beatmapset's user data for restricted/deleted users
                profile_data = {
                    **ProfileSchema.get_blank_slate(),
                    **user_dict,
                    "user_id": user_id,
                    "is_restricted": True,
                }
            else:
                # Try fetching from API (won't work in seeding, but kept for consistency)
                profile_data = {"id": user_id}
            
            profile_dict = ProfileSchema.model_validate(profile_data).model_dump(
                exclude={"id", "updated_at"},
                context={"jsonify_nested": True}
            )
            await self.db.add(Profile, **profile_dict, session=self.session)
        except Exception as e:
            self.logger.debug(f"Failed to populate profile for user {user_id}: {e}")
            # Create minimal restricted profile as fallback
            profile_dict = {
                **ProfileSchema.get_blank_slate(),
                "user_id": user_id,
                "is_restricted": True,
            }
            await self.db.add(Profile, **profile_dict, session=self.session)

    async def _generate_bms_snapshot(self, beatmapset_entry: dict, bms_bm_mapping: dict[int, list[dict]]):
        """Generate BeatmapsetSnapshot using schema validation (following BeatmapManager)."""
        beatmapset_id = beatmapset_entry["id"]
        
        # Map id -> beatmapset_id (following BeatmapManager pattern)
        snapshot_data = beatmapset_entry.copy()
        snapshot_data["beatmapset_id"] = snapshot_data.pop("id")
        
        # Generate checksum from beatmaps (using their checksums if available)
        beatmaps = beatmapset_entry.get("beatmaps", [])
        if beatmaps:
            checksum_parts = [bm.get("checksum", str(bm["id"])) for bm in beatmaps]
            checksum = hashlib.md5(",".join(checksum_parts).encode()).hexdigest()
        else:
            checksum = hashlib.md5(f"{beatmapset_id}:{datetime.now(timezone.utc).isoformat()}".encode()).hexdigest()
        
        # Add checksum BEFORE validation (it's a required field)
        snapshot_data["checksum"] = checksum
        
        # Use schema to validate and exclude relationships/extra fields
        try:
            snapshot_dict = BeatmapsetSnapshotSchema.model_validate(snapshot_data).model_dump(
                exclude={"id", "beatmap_snapshots", "beatmapset_tags", "user_profile", "beatmaps", "user"}
            )
        except Exception as e:
            self.logger.warning(f"Schema validation failed for beatmapset {beatmapset_id}: {e}")
            # Fallback: manually construct snapshot data with only valid fields
            snapshot_dict = self._build_snapshot_fallback(beatmapset_entry)
        
        # Add relationships
        snapshot_dict["beatmap_snapshots"] = bms_bm_mapping.get(beatmapset_id, [])
        snapshot_dict["snapshot_number"] = 1
        
        # Insert snapshot if it doesn't exist
        if not await self.db.get(BeatmapsetSnapshot, checksum=checksum, session=self.session):
            await self.db.add(BeatmapsetSnapshot, **snapshot_dict, session=self.session)

    def _build_snapshot_fallback(self, beatmapset_entry: dict) -> dict:
        """Fallback snapshot construction if schema validation fails."""
        # Valid BeatmapsetSnapshot columns from the model
        valid_columns = {
            "artist", "artist_unicode", "availability", "bpm", "can_be_hyped",
            "covers", "creator", "current_nominations", "deleted_at", "description",
            "discussion_enabled", "discussion_locked", "favourite_count", "genre",
            "hype", "is_scoreable", "language", "last_updated", "legacy_thread_url",
            "nominations_summary", "nsfw", "offset", "pack_tags", "play_count",
            "preview_url", "ranked", "ranked_date", "rating", "ratings", "source",
            "spotlight", "status", "storyboard", "submitted_date", "tags", "title",
            "title_unicode", "track_id", "video"
        }
        
        return {
            k: v for k, v in beatmapset_entry.items() 
            if k in valid_columns
        }

    async def _seed_beatmap(self, beatmap_entry: dict) -> list[dict]:
        """Seed a beatmap and its snapshot."""
        beatmap_id = beatmap_entry["id"]
        beatmapset_id = beatmap_entry["beatmapset_id"]
        beatmap_user_id = beatmap_entry.get("user_id")

        # Ensure beatmap owner user exists (BeatmapSnapshot has user_id FK)
        if beatmap_user_id:
            await self._ensure_user(beatmap_user_id)

        # Ensure beatmap exists
        if not await self.db.get(Beatmap, id=beatmap_id, session=self.session):
            await self.db.add(Beatmap, id=beatmap_id, beatmapset_id=beatmapset_id, session=self.session)

        added_bm_dicts: list[dict] = []
        
        # Check if beatmap has snapshot data in fixtures
        snapshots = beatmap_entry.get("snapshots", [])
        if snapshots:
            # Use fixture snapshot data if available
            for beatmap_snapshot_entry in snapshots:
                added_bm_dict = await self._seed_beatmap_snapshot(beatmap_snapshot_entry)
                added_bm_dicts.append(added_bm_dict)
        else:
            # Generate snapshot from beatmap data (following BeatmapManager pattern)
            added_bm_dict = await self._generate_bm_snapshot(beatmap_entry)
            if added_bm_dict:
                added_bm_dicts.append(added_bm_dict)

        self.progress += 1
        await self.queue.put(SeedEvent(SeederTarget.BEATMAP, self.progress, self.total))

        return added_bm_dicts

    async def _generate_bm_snapshot(self, beatmap_entry: dict) -> dict | None:
        """Generate BeatmapSnapshot using schema validation."""
        beatmap_id = beatmap_entry["id"]
        checksum = beatmap_entry.get("checksum", hashlib.md5(str(beatmap_id).encode()).hexdigest())
        
        # Check if snapshot already exists
        if await self.db.get(BeatmapSnapshot, checksum=checksum, session=self.session):
            bm_snapshot = await self.db.get(BeatmapSnapshot, checksum=checksum, session=self.session)
            return {"id": bm_snapshot.id}
        
        # Map id -> beatmap_id (following BeatmapManager pattern)
        snapshot_data = beatmap_entry.copy()
        snapshot_data["beatmap_id"] = snapshot_data.pop("id")
        
        # Use schema to validate
        try:
            snapshot_dict = BeatmapSnapshotSchema.model_validate(snapshot_data).model_dump(
                exclude={"id", "beatmapset_snapshots", "beatmap_tags", "leaderboard", "owner_profiles", "owners", "top_tag_ids"}
            )
        except Exception as e:
            self.logger.debug(f"Schema validation failed for beatmap {beatmap_id}: {e}")
            # Fallback: use the beatmap data directly (it should be valid)
            snapshot_dict = beatmap_entry.copy()
            snapshot_dict["beatmap_id"] = beatmap_id
        
        snapshot_dict["checksum"] = checksum
        snapshot_dict["snapshot_number"] = 1
        
        # Insert snapshot
        beatmap_snapshot = await self.db.add(BeatmapSnapshot, **snapshot_dict, session=self.session)
        return {"id": beatmap_snapshot.id}

    async def _seed_beatmap_snapshot(self, beatmap_snapshot_entry: dict) -> dict:
        """Seed an existing beatmap snapshot from fixture data."""
        checksum = beatmap_snapshot_entry["checksum"]
        
        beatmap_snapshot = await self.db.get(BeatmapSnapshot, checksum=checksum, session=self.session)
        if not beatmap_snapshot:
            beatmap_snapshot = await self.db.add(BeatmapSnapshot, **beatmap_snapshot_entry, session=self.session)
        
        return {"id": beatmap_snapshot.id}

    async def _seed_beatmapset_snapshot(self, beatmapset_snapshot_entry: dict, bm_bms_mapping: dict[int, list[dict]]):
        """Seed an existing beatmapset snapshot from fixture data."""
        beatmapset_snapshot_entry["beatmap_snapshots"] = bm_bms_mapping[beatmapset_snapshot_entry["beatmapset_id"]]
        
        if not await self.db.get(BeatmapsetSnapshot, checksum=beatmapset_snapshot_entry["checksum"], session=self.session):
            await self.db.add(BeatmapsetSnapshot, **beatmapset_snapshot_entry, session=self.session)
