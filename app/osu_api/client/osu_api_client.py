from pydantic_core import ValidationError

from app.logging import get_logger
from app.osu_api.enums import APIEndpoint, Ruleset, ScoreType
from app.redis import CACHED_BEATMAP_EXPIRY, CACHED_BEATMAPSET_EXPIRY, Namespace, rate_limit
from app.redis.models import Beatmap, Beatmapset

from .base import OsuAPIClientBase

logger = get_logger(__name__)


class OsuAPIClient(OsuAPIClientBase):
    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_beatmap(self, beatmap_id: int) -> dict:
        """Fetch a beatmap from the osu! API with Redis caching.

        Retrieves beatmap data from Redis cache or the osu! API, caching
        the result for future requests.

        Args:
            beatmap_id: The ID of the beatmap to fetch.

        Returns:
            Dictionary containing beatmap data.
        """
        cached_beatmap_hash_name = Namespace.CACHED_BEATMAP.hash_name(beatmap_id)

        async def get_cached_beatmap_from_redis() -> Beatmap | None:
            if serialized_beatmap := await self.rc.hgetall(cached_beatmap_hash_name):
                try:
                    return Beatmap.deserialize(serialized_beatmap)
                except (ValidationError, ValueError) as e:
                    logger.warning(f"Error when deserializing from redis cache: {e}")

            return None

        if cached_beatmap := await get_cached_beatmap_from_redis():
            return cached_beatmap.model_dump(mode="json")

        url = APIEndpoint.BEATMAP.format(beatmap=beatmap_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        beatmap_data = response.json()

        cached_beatmap = Beatmap.model_validate(beatmap_data)
        await self.rc.hset(cached_beatmap_hash_name, mapping=cached_beatmap.serialize())
        await self.rc.expire(cached_beatmap_hash_name, CACHED_BEATMAP_EXPIRY)

        return beatmap_data

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_beatmap_scores(
        self, beatmap_id: int, limit: int | None = None, offset: int | None = None
    ) -> dict:
        """Fetch scores for a beatmap from the osu! API.

        Args:
            beatmap_id: The ID of the beatmap.
            limit: Maximum number of scores to return.
            offset: Offset for pagination.

        Returns:
            Dictionary containing scores data.
        """
        url = APIEndpoint.BEATMAP_SCORES.format(beatmap=beatmap_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        query_parameters: dict[str, int] = {}

        if limit is not None:
            query_parameters["limit"] = limit

        if offset is not None:
            query_parameters["offset"] = offset

        url += self.format_query_parameters(query_parameters)

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_beatmap_attributes(self, beatmap_id: int, mods: list[int]) -> dict:
        """Fetch beatmap attributes (difficulty) from the osu! API.

        Args:
            beatmap_id: The ID of the beatmap.
            mods: List of mod IDs to calculate attributes for.

        Returns:
            Dictionary containing beatmap attributes.
        """
        url = APIEndpoint.BEATMAP_ATTRIBUTES.format(beatmap=beatmap_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }
        body = {"mods": mods}

        response = await self._http_client.post(url, headers=headers, json=body)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_beatmapset(self, beatmapset_id: int) -> dict:
        """Fetch a beatmapset from the osu! API with Redis caching.

        Retrieves beatmapset data from Redis cache or the osu! API, caching
        the result for future requests.

        Args:
            beatmapset_id: The ID of the beatmapset to fetch.

        Returns:
            Dictionary containing beatmapset data.
        """
        cached_beatmapset_hash_name = Namespace.CACHED_BEATMAPSET.hash_name(beatmapset_id)

        async def get_cached_beatmapset_from_redis() -> Beatmapset | None:
            if serialized_beatmapset := await self.rc.hgetall(cached_beatmapset_hash_name):
                try:
                    return Beatmapset.deserialize(serialized_beatmapset)
                except (ValidationError, ValueError) as e:
                    logger.warning(
                        f"Error when deserializing from redis cache: {e}, falling back to fetching directly from osu! API"
                    )

            return None

        if cached_beatmapset := await get_cached_beatmapset_from_redis():
            return cached_beatmapset.model_dump(mode="json")

        url = APIEndpoint.BEATMAPSET.format(beatmapset=beatmapset_id)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        beatmapset_data = response.json()

        cached_beatmapset = Beatmapset.model_validate(beatmapset_data)
        await self.rc.hset(cached_beatmapset_hash_name, mapping=cached_beatmapset.serialize())
        await self.rc.expire(cached_beatmapset_hash_name, CACHED_BEATMAPSET_EXPIRY)

        return beatmapset_data

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_beatmapset_discussions(
        self,
        beatmapset_status: str = "all",
        page: int = 1,
        limit: int = 50,
    ) -> dict:
        """Fetch beatmapsets by status using the discussions endpoint.

        Args:
            beatmapset_status: Filter by beatmapset status (e.g., "all", "ranked").
            page: Page number for pagination.
            limit: Maximum number of results per page.

        Returns:
            Dictionary containing beatmapset discussions data.
        """
        url = APIEndpoint.BEATMAPSET_DISCUSSIONS.format()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        query_parameters: dict[str, int | str] = {
            "beatmapset_status": beatmapset_status,
            "cursor[page]": page,
            "limit": limit,
        }

        url += self.format_query_parameters(query_parameters)

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def search_beatmapsets(
        self,
        status: str | None = None,
        genre: int | None = None,
        language: int | None = None,
        mode: int | None = None,
        nsfw: bool | None = None,
        page: int = 1,
        sort: str | None = None,
        query: str | None = None,
    ) -> dict:
        """Search beatmapsets with server-side filters.

        `query` maps to the osu! `q` free-text parameter, letting callers narrow
        the listing by artist/title instead of paging the entire ranked catalog.
        """
        url = APIEndpoint.BEATMAPSET_SEARCH.format()

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        query_parameters: dict[str, int | str] = {}

        if query is not None:
            query_parameters["q"] = query
        if status is not None:
            query_parameters["s"] = status
        if genre is not None:
            query_parameters["g"] = genre
        if language is not None:
            query_parameters["l"] = language
        if mode is not None:
            query_parameters["m"] = mode
        if nsfw is not None:
            query_parameters["nsfw"] = "true" if nsfw else "false"
        if page is not None:
            query_parameters["page"] = page
        if sort is not None:
            query_parameters["sort"] = sort

        url += self.format_query_parameters(query_parameters)

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_own_data(self, access_token: str) -> dict:
        """Fetch the authenticated user's data from the osu! API.

        Args:
            access_token: The OAuth2 access token for authentication.

        Returns:
            Dictionary containing the user's data.
        """
        url = APIEndpoint.ME.value

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(access_token),
        }

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_user_scores(
        self,
        user_id: int,
        score_type: ScoreType,
        legacy_only: int = 0,
        include_fails: int = 0,
        mode: Ruleset | None = None,
        limit: int | None = None,
        offset: int | None = None,
    ) -> dict:
        """Fetch scores for a user from the osu! API.

        Args:
            user_id: The ID of the user.
            score_type: The type of scores to fetch (e.g., PERFORMANCE, TOP).
            legacy_only: Include legacy scores only.
            include_fails: Include failed scores.
            mode: Filter by game mode.
            limit: Maximum number of scores to return.
            offset: Offset for pagination.

        Returns:
            Dictionary containing user scores data.
        """
        url = APIEndpoint.SCORES.format(user=user_id, type=score_type.value)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        query_parameters: dict[str, int | str] = {
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

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_user(self, user_id: int, mode: Ruleset | None = None) -> dict:
        """Fetch a user from the osu! API.

        Args:
            user_id: The ID of the user.
            mode: The game mode (e.g., OSU, TAITO, MANIA).

        Returns:
            Dictionary containing user data.
        """
        mode_str = mode.value if mode is not None else ""
        url = APIEndpoint.USER.format(user=user_id, mode=mode_str)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_tags(self) -> dict[str, list[dict[str, int | str]]]:
        """Fetch all tags from the osu! API.

        Returns:
            Dictionary mapping tag names to their associated IDs.
        """
        url = APIEndpoint.TAGS.value

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()

    @rate_limit(min_interval=0.5, limit_per_window=120, window_size=60)
    async def get_rankings(
        self,
        ruleset: Ruleset,
        mode: str,
        limit: int | None = None,
        offset: int | None = None,
        cursor_page: int | None = None,
    ) -> dict:
        """Fetch rankings from the osu! API.

        Args:
            ruleset: The game ruleset (e.g., OSU, TAITO, MANIA).
            mode: The ranking mode (e.g., SCORE, PERFORMANCE).
            limit: Maximum number of rankings to return.
            offset: Offset for pagination.
            cursor_page: Cursor-based pagination page.

        Returns:
            Dictionary containing rankings data.
        """
        url = APIEndpoint.RANKINGS.format(ruleset=ruleset.value, mode=mode)

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            **await self.get_auth_headers(),
        }

        query_parameters: dict[str, int | str] = {}

        if limit is not None:
            query_parameters["limit"] = limit

        if offset is not None:
            query_parameters["offset"] = offset

        if cursor_page is not None:
            query_parameters["cursor[page]"] = cursor_page

        url += self.format_query_parameters(query_parameters)

        response = await self._http_client.get(url, headers=headers)

        response.raise_for_status()
        return response.json()
