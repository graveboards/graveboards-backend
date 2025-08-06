import logging
from typing import Union

import httpx
from pydantic_core import ValidationError

from app.redis import rate_limit, Namespace, CACHED_BEATMAP_EXPIRY, CACHED_BEATMAPSET_EXPIRY
from app.redis.models import Beatmap, Beatmapset
from .base import OsuAPIClientBase
from app.osu_api.enums import APIEndpoint, ScoreType, Ruleset

RATE_LIMIT = 60
logger = logging.getLogger(__name__)


class OsuAPIClient(OsuAPIClientBase):
    # Beatmaps
    @rate_limit(RATE_LIMIT)
    async def get_beatmap(self, beatmap_id: int) -> dict:
        async def get_cached_beatmap_from_redis() -> Beatmap | None:
            if serialized_beatmap := await self.rc.hgetall(cached_beatmap_hash_name):
                try:
                    return Beatmap.deserialize(serialized_beatmap)
                except (ValidationError, ValueError) as e:
                    logger.warning(f"Error when deserializing from redis cache: {e}")

            return None

        cached_beatmap_hash_name = Namespace.CACHED_BEATMAP.hash_name(beatmap_id)

        if cached_beatmap := await get_cached_beatmap_from_redis():
            return cached_beatmap.model_dump(mode="json")

        url = APIEndpoint.BEATMAP.format(beatmap=beatmap_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        beatmap_data = response.json()

        cached_beatmap = Beatmapset.model_validate(beatmap_data)
        await self.rc.hset(cached_beatmap_hash_name, mapping=cached_beatmap.serialize())
        await self.rc.expire(cached_beatmap_hash_name, CACHED_BEATMAP_EXPIRY)

        return beatmap_data

    @rate_limit(RATE_LIMIT)
    async def get_beatmap_attributes(self, beatmap_id: int, mods: int) -> dict:
        url = APIEndpoint.BEATMAP_ATTRIBUTES.format(beatmap=beatmap_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }
        body = {
            "mods": mods
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=body)

        response.raise_for_status()
        return response.json()

    # Beatmapsets
    @rate_limit(RATE_LIMIT)
    async def get_beatmapset(self, beatmapset_id: int) -> dict:
        async def get_cached_beatmapset_from_redis() -> Beatmapset | None:
            if serialized_beatmapset := await self.rc.hgetall(cached_beatmapset_hash_name):
                try:
                    return Beatmapset.deserialize(serialized_beatmapset)
                except (ValidationError, ValueError) as e:
                    logger.warning(f"Error when deserializing from redis cache: {e}, falling back to fetching directly from osu! API")

            return None

        cached_beatmapset_hash_name = Namespace.CACHED_BEATMAPSET.hash_name(beatmapset_id)

        if cached_beatmapset := await get_cached_beatmapset_from_redis():
            return cached_beatmapset.model_dump(mode="json")

        url = APIEndpoint.BEATMAPSET.format(beatmapset=beatmapset_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        beatmapset_data = response.json()

        cached_beatmapset = Beatmapset.model_validate(beatmapset_data)
        await self.rc.hset(cached_beatmapset_hash_name, mapping=cached_beatmapset.serialize())
        await self.rc.expire(cached_beatmapset_hash_name, CACHED_BEATMAPSET_EXPIRY)

        return beatmapset_data

    # Users
    @rate_limit(RATE_LIMIT)
    async def get_own_data(self, access_token: str) -> dict:
        url = APIEndpoint.ME.value

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(access_token)
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(RATE_LIMIT)
    async def get_user_scores(self, user_id: int, score_type: ScoreType, legacy_only: int = 0, include_fails: int = 0, mode: Ruleset | None = None, limit: int | None = None, offset: int | None = None):
        url = APIEndpoint.SCORES.format(user=user_id, type=score_type.value)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }

        query_parameters: dict[str, Union[int, str]] = {
            "legacy_only": legacy_only,
            "include_fails": include_fails,
        }

        if mode is not None:
            query_parameters["mode"] = mode.value

        if limit is not None:
            query_parameters["limit"] = limit

        if offset is not None:
            query_parameters["offset"] = offset

        url += self.format_query_parameters(query_parameters)

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(RATE_LIMIT)
    async def get_user(self, user_id: int, mode: Ruleset | None = None) -> dict:
        url = APIEndpoint.USER.format(user=user_id, mode=mode)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)  # httpx.readtimeout ??

        response.raise_for_status()
        return response.json()

    # Tags
    @rate_limit(RATE_LIMIT)
    async def get_tags(self) -> dict[str, list[dict[str, Union[int, str]]]]:
        url = APIEndpoint.TAGS.value

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers()
        }

        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()
