from typing import Optional, Any, ClassVar
from datetime import datetime

from pydantic.main import BaseModel

from app.osu_api.literals import RankedIntLiteral, RankedStatusLiteral
from .availability import AvailabilitySchema
from .beatmap_osu_api_schema import BeatmapOsuApiSchema
from .covers import CoversSchema
from .current_nomination import CurrentNominationSchema
from .beatmapset_description import BeatmapsetDescriptionSchema
from .genre import GenreSchema
from .hype import HypeSchema
from .language import LanguageSchema
from .nominations_summary import NominationsSummarySchema


class BeatmapsetOsuApiSchema(BaseModel):
    artist: str
    artist_unicode: str
    availability: "AvailabilitySchema"
    beatmaps: Optional[list["BeatmapOsuApiSchema"]] = None
    bpm: float
    can_be_hyped: bool
    covers: "CoversSchema"
    creator: str
    current_nominations: list["CurrentNominationSchema"]
    deleted_at: Optional[datetime]
    description: "BeatmapsetDescriptionSchema"
    discussion_enabled: bool
    discussion_locked: bool
    favourite_count: int
    genre: Optional["GenreSchema"]
    hype: Optional["HypeSchema"]
    id: int
    is_scoreable: bool
    language: Optional["LanguageSchema"]
    last_updated: datetime
    legacy_thread_url: Optional[str]
    nominations_summary: "NominationsSummarySchema"
    nsfw: bool
    offset: int
    pack_tags: list[str]
    play_count: int
    preview_url: str
    ranked: RankedIntLiteral
    ranked_date: Optional[datetime]
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
    track_id: Optional[int]
    user: Optional[dict[str, Any]] = None
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
        "track_id"
    }
