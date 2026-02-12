import os
import asyncio
import logging
from io import BytesIO
from zipfile import ZipFile
from copy import copy
from typing import Union

import httpx
import aiofiles
from httpx import HTTPError
from sqlalchemy.exc import IntegrityError

from .osu_api import OsuAPIClient
from .database import PostgresqlDB
from .database.models import (
    Profile,
    BeatmapsetTag,
    BeatmapTag,
    User,
    BeatmapSnapshot,
    BeatmapsetSnapshot,
    Beatmapset,
    Beatmap,
    ProfileFetcherTask
)
from .database.schemas import (
    BeatmapSnapshotSchema,
    BeatmapsetSnapshotSchema,
    ProfileSchema,
    BeatmapTagSchema,
    BeatmapsetOsuApiSchema,
    BeatmapOsuApiSchema
)
from .redis import RedisClient, Namespace
from .utils import combine_checksums, aware_utcnow
from .exceptions import RestrictedUserError, RedisLockTimeoutError
from .config import INSTANCE_DIR

BEATMAPS_PATH = os.path.join(INSTANCE_DIR, "beatmaps")
BEATMAPSETS_PATH = os.path.join(INSTANCE_DIR, "beatmapsets")
BEATMAP_DOWNLOAD_BASEURL = "https://osu.ppy.sh/osu/"
BEATMAP_SNAPSHOT_FILE_PATH = os.path.join(BEATMAPS_PATH, "{beatmap_id}/{snapshot_number}.osu")
logger = logging.getLogger(__name__)


class BeatmapManager:
    def __init__(self, rc: RedisClient, db: PostgresqlDB):
        self.rc = rc
        self.db = db
        self.oac = OsuAPIClient(rc)

        self._changelog = {}

    async def archive(self, beatmapset_id: int, download: bool = True) -> dict[str, Union[dict, list[dict], str, None]]:
        logger.debug(f"Started archive process for beatmapset {beatmapset_id}: {download=}")
        self._reset_changelog()

        beatmapset_dict = await self.oac.get_beatmapset(beatmapset_id)
        beatmapset_dict["play_count"] = 90
        beatmapset_dict["beatmaps"][0]["top_tag_ids"] = [{"tag_id":8}]
        checksum = combine_checksums([beatmap["checksum"] for beatmap in beatmapset_dict["beatmaps"]])

        await self._populate_beatmapset(beatmapset_dict)

        if not await self.db.get(BeatmapsetSnapshot, checksum=checksum):
            await self._snapshot_beatmapset(beatmapset_dict)

            if download:
                beatmap_ids = [bm_ss_dict["beatmap_id"] for bm_ss_dict in self._changelog["snapshotted_beatmaps"]]
                await self._download(beatmap_ids)
        else:
            await self._update_beatmapset(beatmapset_dict)

        logger.debug(f"Finished archive process for beatmapset {beatmapset_id}: changelog={self._changelog}")

        try:
            return copy(self._changelog)
        finally:
            self._reset_changelog()

    async def _snapshot_beatmapset(self, beatmapset_dict: dict):
        beatmapset_snapshot_dict = BeatmapsetSnapshotSchema.model_validate(beatmapset_dict).model_dump(
            exclude={"beatmap_snapshots", "beatmapset_tags", "user_profile"}
        )
        beatmapset_snapshot_dict["beatmap_snapshots"] = await self._snapshot_beatmaps(beatmapset_dict["beatmaps"])
        beatmapset_snapshot_dict["beatmapset_tags"] = await self._populate_beatmapset_tags(beatmapset_dict["tags"])
        beatmapset_snapshot = await self.db.add(BeatmapsetSnapshot, **beatmapset_snapshot_dict)

        info = {field: getattr(beatmapset_snapshot, field) for field in {"id", "beatmapset_id", "snapshot_number", "checksum"}}
        self._changelog["snapshotted_beatmapset"] = info
        logger.debug(f"Snapshotted beatmapset: {info}")

    async def _snapshot_beatmaps(self, beatmap_dicts: list[dict]) -> list[BeatmapSnapshot]:
        beatmap_snapshots = []

        for beatmap_dict in beatmap_dicts:
            beatmap_snapshot = await self.db.get(BeatmapSnapshot, checksum=beatmap_dict["checksum"])

            if not beatmap_snapshot:
                beatmap_snapshot_dict = BeatmapSnapshotSchema.model_validate(beatmap_dict).model_dump(
                    exclude={"beatmapset_snapshots", "beatmap_tags", "leaderboard", "owner_profiles"}
                )
                beatmap_snapshot_dict["beatmap_tags"] = await self._populate_beatmap_tags(beatmap_dict["top_tag_ids"])
                beatmap_snapshot_dict["owner_profiles"] = await self._populate_owner_profiles(beatmap_dict["owners"])
                beatmap_snapshot = await self.db.add(BeatmapSnapshot, **beatmap_snapshot_dict)

                info = {field: getattr(beatmap_snapshot, field) for field in {"id", "beatmap_id", "snapshot_number", "checksum"}}
                self._changelog["snapshotted_beatmaps"].append(info)
                logger.debug(f"Snapshotted beatmap: {info}")

            beatmap_snapshots.append(beatmap_snapshot)

        return beatmap_snapshots

    async def _update_beatmapset(self, beatmapset_dict: dict):
        await self._update_beatmaps(beatmapset_dict["beatmaps"])

        checksum = combine_checksums([beatmap["checksum"] for beatmap in beatmapset_dict["beatmaps"]])
        beatmapset_snapshot = await self.db.get(
            BeatmapsetSnapshot,
            checksum=checksum,
            _sorting=[{"field": "BeatmapsetSnapshot.id", "order": "desc"}]
        )
        old = BeatmapsetOsuApiSchema.model_validate(beatmapset_snapshot, from_attributes=True).model_dump()
        new = BeatmapsetOsuApiSchema.model_validate(beatmapset_dict).model_dump()
        delta = {}

        for field in BeatmapsetOsuApiSchema.UPDATABLE_FIELDS:
            if (new_value := new[field]) != old[field]:
                delta[field] = new_value

        if delta:
            await self.db.update(BeatmapsetSnapshot, beatmapset_snapshot.id, **delta)

            info = {**{"beatmapset_id": beatmapset_snapshot.beatmapset_id}, **delta}
            self._changelog["updated_beatmapset"] = {**{"beatmapset_id": beatmapset_snapshot.beatmapset_id}, **delta}
            logger.debug(f"Updated beatmapset: {info}")

    async def _update_beatmaps(self, beatmap_dicts: list[dict]):
        for beatmap_dict in beatmap_dicts:
            async with self.db.session() as session:
                beatmap_snapshot = await self.db.get(
                    BeatmapSnapshot,
                    checksum=beatmap_dict["checksum"],
                    _include={"beatmap_tags": True, "owner_profiles": True},
                    session=session
                )
                old = BeatmapOsuApiSchema.model_validate(beatmap_snapshot, from_attributes=True).model_dump()
                new = BeatmapOsuApiSchema.model_validate(beatmap_dict).model_dump()
                delta = {}

                for field in BeatmapOsuApiSchema.UPDATABLE_FIELDS:
                    if (new_value := new[field]) != old[field]:
                        delta[field] = new_value

                if delta:
                    for key, value in delta.items():
                        if key not in {"top_tag_ids", "owners"}:
                            setattr(beatmap_snapshot, key, value)

                    # Need to find a more elegant solution to updating relationships...
                    beatmap_tags_ = await self._populate_beatmap_tags(beatmap_dict["top_tag_ids"])
                    owners = beatmap_dict["owners"] or {"id": beatmap_dict["user_id"]}
                    # Always ensure at least one owner in owner_profiles
                    # Beatmap user_id inherits from beatmapset if no owners specified on the osu! website
                    owner_profiles_ = await self._populate_owner_profiles(owners)
                    beatmap_tags = await self.db.get_many(BeatmapTag, _where=BeatmapTag.id.in_([t.id for t in beatmap_tags_]), session=session)
                    owner_profiles = await self.db.get_many(Profile, _where=Profile.id.in_([p.id for p in owner_profiles_]), session=session)
                    beatmap_snapshot.beatmap_tags = beatmap_tags
                    beatmap_snapshot.owner_profiles = owner_profiles

                    info = {**{"beatmap_id": beatmap_snapshot.beatmap_id}, **delta}
                    self._changelog["updated_beatmaps"].append(info)
                    logger.debug(f"Updated beatmap: {info}")

    async def _populate_beatmapset(self, beatmapset_dict: dict):
        beatmapset_id = beatmapset_dict["id"]
        user_id = beatmapset_dict["user_id"]

        try:
            await self._populate_user(user_id)
        except RestrictedUserError:
            user_dict = beatmapset_dict["user"]
            await self._populate_profile(user_id, restricted_user_dict=user_dict, is_restricted=True)

        if not await self.db.get(Beatmapset, id=beatmapset_id):
            await self.db.add(Beatmapset, id=beatmapset_id, user_id=user_id)
            info = {"id": beatmapset_id, "user_id": user_id}
            logger.debug(f"Added beatmapset: {info}")

        for beatmap_dict in beatmapset_dict["beatmaps"]:
            await self._populate_beatmap(beatmap_dict)

    async def _populate_beatmap(self, beatmap_dict: dict):
        beatmap_id = beatmap_dict["id"]
        beatmapset_id = beatmap_dict["beatmapset_id"]
        user_id = beatmap_dict["user_id"]  # Appears to always be first user in owners, else host

        try:
            await self._populate_user(user_id)
        except RestrictedUserError:
            await self._populate_profile(user_id, is_restricted=True)

        if not await self.db.get(Beatmap, id=beatmap_id):
            await self.db.add(Beatmap, id=beatmap_id, beatmapset_id=beatmapset_id)
            info = {"id": beatmap_id, "beatmapset_id": beatmapset_id}
            logger.debug(f"Added beatmap: {info}")

    async def _populate_user(self, user_id: int) -> User:
        if not (user := await self.db.get(User, id=user_id)):
            user = await self.db.add(User, id=user_id)
            info = {"id": user_id}
            logger.debug(f"Added user: {info}")

        try:
            profile = await self._populate_profile(user_id)
            user.profile = profile
        except HTTPError:
            raise RestrictedUserError(user_id)

        return user

    async def _populate_profile(self, user_id: int, restricted_user_dict: dict = None, is_restricted: bool = False) -> Profile:
        restricted_user_dict = restricted_user_dict if restricted_user_dict is not None else {}
        lock_hash_name = Namespace.LOCK.hash_name(Namespace.OSU_USER_PROFILE.hash_name(user_id))

        try:
            async with self.rc.lock_ctx(lock_hash_name):
                if (profile := await self.db.get(Profile, user_id=user_id)) and not is_restricted:
                    return profile

                if not is_restricted:
                    user_dict = await self.oac.get_user(user_id)
                    profile_dict = ProfileSchema.model_validate(user_dict).model_dump(
                        exclude={"id", "updated_at", "is_restricted"},
                        context={"jsonify_nested": True}
                    )
                else:
                    user_dict = {
                        **ProfileSchema.get_blank_slate(),
                        **restricted_user_dict,
                        **{
                            "id": user_id,
                            "is_restricted": True,
                        }
                    }
                    profile_dict = ProfileSchema.model_validate(user_dict).model_dump(
                        exclude={"id", "updated_at"},
                        context={"jsonify_nested": True}
                    )

                try:
                    profile = await self.db.add(Profile, **profile_dict)
                    info = {"id": profile.id, "user_id": profile.user_id, "is_restricted": profile.is_restricted}
                    logger.debug(f"Added profile: {info}")
                except IntegrityError:
                    logger.warning(f"IntegrityError - This shouldn't happen after obtaining the lock... {user_id=}")
                    profile = await self.db.get(Profile, user_id=user_id)
                    profile = await self.db.update(Profile, profile.id, **profile_dict)

                task = (await self.db.get(ProfileFetcherTask, user_id=user_id))
                await self.db.update(ProfileFetcherTask, task.id, last_fetch=aware_utcnow())

                return profile
        except RedisLockTimeoutError:
            raise

    async def _populate_owner_profiles(self, owners: list[dict]) -> list[Profile]:
        profiles = []

        for owner_dict in owners:
            user_id = owner_dict["id"]

            try:
                user = await self._populate_user(user_id)
                profile = user.profile
            except RestrictedUserError:
                profile = await self._populate_profile(user_id, restricted_user_dict=owner_dict, is_restricted=True)

            profiles.append(profile)

        return profiles

    async def _populate_beatmapset_tags(self, tags_str: str) -> list[BeatmapsetTag]:
        tag_strs = set(tag.strip() for tag in tags_str.split(" ") if tag.strip())
        beatmapset_tags = []

        if not tags_str:
            return []

        for tag_str in tag_strs:
            if not (beatmapset_tag := await self.db.get(BeatmapsetTag, name=tag_str)):
                beatmapset_tag = await self.db.add(BeatmapsetTag, name=tag_str)
                info = {"id": beatmapset_tag.id, "name": beatmapset_tag.name}
                logger.debug(f"Added beatmapset tag: {info}")

            beatmapset_tags.append(beatmapset_tag)

        return beatmapset_tags

    async def _populate_beatmap_tags(self, top_tag_ids: list[dict[str, int]]) -> list[BeatmapTag]:
        async def fetch_beatmap_tag(_recursed=False) -> BeatmapTag | None:
            if not (beatmap_tag_ := await self.db.get(BeatmapTag, id=tag_id)):
                if _recursed:
                    logger.warning(f"fetch_beatmap_tag() recursed more than once for {tag_id=}, skipping")
                    return None

                await self._update_beatmap_tags_from_osu()
                return await fetch_beatmap_tag(_recursed=True)

            return beatmap_tag_

        beatmap_tags = []

        if not top_tag_ids:
            return []

        for top_tag in top_tag_ids:
            tag_id = top_tag["tag_id"]

            if (beatmap_tag := await fetch_beatmap_tag()) is None:
                continue

            beatmap_tags.append(beatmap_tag)

        return beatmap_tags

    async def _update_beatmap_tags_from_osu(self):
        osu_beatmap_tags = await self.oac.get_tags()

        for osu_beatmap_tag in osu_beatmap_tags["tags"]:
            tag_id = osu_beatmap_tag["id"]

            if not (beatmap_tag := await self.db.get(BeatmapTag, id=tag_id)):
                await self.db.add(BeatmapTag, **osu_beatmap_tag)
                logger.debug(f"Added beatmap tag: {osu_beatmap_tag}")
            else:
                old_osu_beatmap_tag = BeatmapTagSchema.model_validate(beatmap_tag).model_dump(exclude={"created_at", "updated_at"})

                if osu_beatmap_tag != old_osu_beatmap_tag:
                    await self.db.update(BeatmapTag, primary_key=tag_id, **osu_beatmap_tag)
                    logger.debug(f"Updated beatmap tag: old={old_osu_beatmap_tag}, new={osu_beatmap_tag}")

    async def _download(self, beatmap_ids: list[int]):
        if not beatmap_ids:
            return

        async with httpx.AsyncClient() as client:
            for beatmap_id in beatmap_ids:
                url = os.path.join(BEATMAP_DOWNLOAD_BASEURL, str(beatmap_id))
                output_directory = os.path.join(BEATMAPS_PATH, str(beatmap_id))
                os.makedirs(output_directory, exist_ok=True)
                beatmap_snapshot = (await self.db.get(BeatmapSnapshot, beatmap_id=beatmap_id, _sorting=[{"field": "BeatmapSnapshot.id", "order": "desc"}]))
                output_path = os.path.join(output_directory, f"{beatmap_snapshot.snapshot_number}.osu")
                exists = os.path.exists(output_path)

                async with client.stream("GET", url) as response:
                    async with aiofiles.open(output_path, "wb") as f:
                        async for chunk in response.aiter_bytes():
                            await f.write(chunk)

                logger.debug(f"Downloaded .osu file to '{output_path}'")

                if exists:
                    logger.warning(f"Overwrote .osu file at '{output_path}'")  # Caused by local instance files not being in sync with the database (e.g., leftover files)

    @staticmethod
    async def get(beatmap_id: int, snapshot_number: int) -> bytes:
        file_path = BEATMAP_SNAPSHOT_FILE_PATH.format(beatmap_id=beatmap_id, snapshot_number=snapshot_number)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No .osu file found for beatmap {beatmap_id}, snapshot {snapshot_number}")

        async with aiofiles.open(file_path, "rb") as file:
            return await file.read()

    @staticmethod
    def get_path(beatmap_id: int, snapshot_number: int) -> str:
        file_path = BEATMAP_SNAPSHOT_FILE_PATH.format(beatmap_id=beatmap_id, snapshot_number=snapshot_number)

        if not os.path.exists(file_path):
            raise FileNotFoundError(f"No .osu file found for beatmap {beatmap_id}, snapshot {snapshot_number}")

        return file_path

    async def get_zip(self, beatmapset_id: int, snapshot_number: int = -1) -> BytesIO:
        if snapshot_number < 0:
            offset = abs(snapshot_number) - 1

            beatmapset_snapshot = await self.db.get(
                BeatmapsetSnapshot,
                beatmapset_id=beatmapset_id,
                _order_by=BeatmapsetSnapshot.snapshot_number.desc(),
                _include={"beatmap_snapshots": True},
                _offset=offset
            )
        else:
            beatmapset_snapshot = await self.db.get(
                BeatmapsetSnapshot,
                beatmapset_id=beatmapset_id,
                snapshot_number=snapshot_number,
                _include={"beatmap_snapshots": True}
            )

        if not beatmapset_snapshot:
            raise ValueError(f"No snapshot found for beatmapset {beatmapset_id}, snapshot {snapshot_number}")

        beatmap_paths = []

        for beatmap_snapshot in beatmapset_snapshot.beatmap_snapshots:
            beatmap_path = self.get_path(beatmap_snapshot.beatmap_id, beatmap_snapshot.snapshot_number)

            if os.path.exists(beatmap_path):
                beatmap_paths.append((beatmap_path, f"{beatmap_snapshot.beatmap_id}.osu"))
            else:
                logger.warning(f"File {beatmap_path} does not exist and will be skipped.")

        return await asyncio.to_thread(self._create_zip, beatmap_paths)

    @staticmethod
    def _create_zip(beatmap_paths: list[tuple[str, str]]) -> BytesIO:
        zip_buffer = BytesIO()

        with ZipFile(zip_buffer, "w") as zip_file:
            for beatmap_path, filename in beatmap_paths:
                zip_file.write(beatmap_path, filename)

        zip_buffer.seek(0)
        return zip_buffer

    def _reset_changelog(self):
        self._changelog = {
            "snapshotted_beatmapset": None,
            "snapshotted_beatmaps": [],
            "updated_beatmapset": None,
            "updated_beatmaps": []
        }
