from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, TYPE_CHECKING

if TYPE_CHECKING:
    from app.database import PostgresqlDB
    from app.redis import RedisClient
    from app.osu_api.client import OsuAPIClient
    from app.database.schemas.sub_schemas import BeatmapsetOsuApiSchema, BeatmapOsuApiSchema
    from app.database.models.beatmapset_snapshot import BeatmapsetSnapshot
    from app.database.models.beatmap_snapshot import BeatmapSnapshot
    from app.database.models.base import AsyncSession

    MetadataProvider = Any


@dataclass
class ExecutionContext:
    queue_id: int
    user_id: int
    beatmapset: BeatmapsetOsuApiSchema | None = None
    beatmaps: list[BeatmapOsuApiSchema] | None = None
    beatmapset_snapshot: BeatmapsetSnapshot | None = None
    beatmap_snapshots: list[BeatmapSnapshot] | None = None
    db: PostgresqlDB | None = None
    redis: RedisClient | None = None
    osu_client: OsuAPIClient | None = None
    session: AsyncSession | None = None
    config: dict[str, Any] = field(default_factory=dict)
    metadata_providers: dict[str, type[MetadataProvider]] | None = None
    last_violation: Any = None
    _provider_cache: dict[str, dict[str, Any]] = field(default_factory=dict)

    async def get_metadata(self, provider_name: str) -> dict[str, Any]:
        if provider_name in self._provider_cache:
            return self._provider_cache[provider_name]

        if not self.metadata_providers or provider_name not in self.metadata_providers:
            raise KeyError(
                f"Metadata provider '{provider_name}' is not registered. "
                f"Available providers: {list(self.metadata_providers or [])}"
            )

        provider_cls = self.metadata_providers[provider_name]
        provider = provider_cls()
        result = await provider.resolve(self)
        self._provider_cache[provider_name] = result
        return result

    def invalidate_metadata(self, provider_name: str | None = None) -> None:
        if provider_name is None:
            self._provider_cache.clear()
        else:
            self._provider_cache.pop(provider_name, None)


def parse_osu_beatmapset(
    beatmapset_dict: dict[str, Any],
) -> tuple[BeatmapsetOsuApiSchema, list[BeatmapOsuApiSchema]]:
    """Convert a raw osu! API beatmapset dict into the typed objects validators expect.

    Rule validators access beatmapset/beatmap fields as attributes on Pydantic objects
    and iterate a populated beatmap list; passing them the raw dict (with
    ``context.beatmaps`` left as ``None``) makes every Tier-2/Tier-3 beatmap rule fail.
    This is the single typed context-construction helper used by both the synchronous
    Phase-1 request path and the asynchronous Phase-2/Tier-3 daemon path, so both build
    context identically.

    Args:
        beatmapset_dict:
            Raw beatmapset mapping as returned by ``OsuAPIClient.get_beatmapset`` -
            either a fresh osu! API response or a Redis-cached ``model_dump``. Both
            shapes validate because the cache model subclasses ``BeatmapsetOsuApiSchema``.

    Returns:
        A tuple of the parsed ``BeatmapsetOsuApiSchema`` and its list of
        ``BeatmapOsuApiSchema`` (an empty list when the set has no beatmaps).
    """
    from app.database.schemas.sub_schemas import BeatmapsetOsuApiSchema

    beatmapset = BeatmapsetOsuApiSchema.model_validate(beatmapset_dict)
    return beatmapset, list(beatmapset.beatmaps or [])
