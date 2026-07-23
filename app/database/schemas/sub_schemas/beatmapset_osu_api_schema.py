from datetime import datetime
from typing import Any, ClassVar

from pydantic.main import BaseModel

from app.osu_api.literals import RankedIntLiteral, RankedStatusLiteral

from .availability import AvailabilitySchema
from .beatmap_osu_api_schema import BeatmapOsuApiSchema
from .beatmapset_description import BeatmapsetDescriptionSchema
from .covers import CoversSchema
from .current_nomination import CurrentNominationSchema
from .genre import GenreSchema
from .hype import HypeSchema
from .language import LanguageSchema
from .nominations_summary import NominationsSummarySchema


class BeatmapsetOsuApiSchema(BaseModel):
    artist: str
    artist_unicode: str
    availability: AvailabilitySchema
    beatmaps: list[BeatmapOsuApiSchema] | None = None
    bpm: float
    can_be_hyped: bool
    covers: CoversSchema
    creator: str
    current_nominations: list[CurrentNominationSchema]
    deleted_at: datetime | None
    description: BeatmapsetDescriptionSchema
    discussion_enabled: bool
    discussion_locked: bool
    favourite_count: int
    genre: GenreSchema | None
    hype: HypeSchema | None
    id: int
    is_scoreable: bool
    language: LanguageSchema | None
    last_updated: datetime
    legacy_thread_url: str | None
    nominations_summary: NominationsSummarySchema
    nsfw: bool
    offset: int
    pack_tags: list[str]
    play_count: int
    preview_url: str
    ranked: RankedIntLiteral
    ranked_date: datetime | None
    rating: float
    ratings: list[int]
    source: str
    spotlight: bool
    status: RankedStatusLiteral
    storyboard: bool
    submitted_date: datetime
    tags: str
    title: str
    title_unicode: str
    track_id: int | None
    user: dict[str, Any] | None = None
    user_id: int
    video: bool

    UPDATABLE_FIELDS: ClassVar[set[str]] = {
        "availability",
        "can_be_hyped",
        "current_nominations",
        "description",
        "discussion_enabled",
        "discussion_locked",
        "favourite_count",
        "genre",
        "hype",
        "is_scoreable",
        "language",
        "last_updated",
        "nominations_summary",
        "nsfw",
        "offset",
        "pack_tags",
        "play_count",
        "ranked",
        "ratings",
        "spotlight",
        "status",
        "track_id",
    }
