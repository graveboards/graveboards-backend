from datetime import datetime, date
from typing import Optional, Union

from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.expression import cast
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql.json import JSONB

from app.utils import aware_utcnow
from .base import Base


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow)
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)

    # osu! API datastructure
    account_history: Mapped[Optional[list[dict[str, Union[str, int, bool, datetime, None]]]]] = mapped_column(JSONB)
    active_tournament_banners: Mapped[Optional[list[dict[str, Union[str, int, None]]]]] = mapped_column(JSONB)
    avatar_url: Mapped[Optional[str]] = mapped_column(String)
    badges: Mapped[Optional[list[dict[str, Union[datetime, str]]]]] = mapped_column(JSONB)
    beatmap_playcounts_count: Mapped[Optional[int]] = mapped_column(Integer)
    comments_count: Mapped[Optional[int]] = mapped_column(Integer)
    country_code: Mapped[Optional[str]] = mapped_column(String(2))
    country: Mapped[Optional[dict[str, str]]] = mapped_column(JSONB)
    cover: Mapped[Optional[dict[str, Union[str, int, None]]]] = mapped_column(JSONB)
    # current_season_stats  # Unknown
    daily_challenge_user_stats: Mapped[Optional[dict[str, Union[int, datetime]]]] = mapped_column(JSONB)
    default_group: Mapped[Optional[str]] = mapped_column(String)
    discord: Mapped[Optional[str]] = mapped_column(String)
    favourite_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    graveyard_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    groups: Mapped[Optional[list[dict[str, Union[str, bool, int, list[str], None]]]]] = mapped_column(JSONB)
    guest_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    has_supported: Mapped[Optional[bool]] = mapped_column(Boolean)
    interests: Mapped[Optional[str]] = mapped_column(String)
    is_active: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_bot: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_deleted: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_online: Mapped[Optional[bool]] = mapped_column(Boolean)
    is_supporter: Mapped[Optional[bool]] = mapped_column(Boolean)
    join_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    kudosu: Mapped[Optional[dict[str, int]]] = mapped_column(JSONB)
    location: Mapped[Optional[str]] = mapped_column(String)
    last_visit: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    loved_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    mapping_follower_count: Mapped[Optional[int]] = mapped_column(Integer)
    matchmaking_stats: Mapped[Optional[list[dict[str, Union[int, bool, dict[str, Union[bool, int, str]]]]]]] = mapped_column(JSONB)
    max_blocks: Mapped[Optional[int]] = mapped_column(Integer)
    max_friends: Mapped[Optional[int]] = mapped_column(Integer)
    monthly_playcounts: Mapped[Optional[list[dict[str, Union[date, int]]]]] = mapped_column(JSONB)
    nominated_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    occupation: Mapped[Optional[str]] = mapped_column(String)
    page: Mapped[Optional[dict[str, str]]] = mapped_column(JSONB)
    pending_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    playmode: Mapped[Optional[str]] = mapped_column(String)
    playstyle: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    pm_friends_only: Mapped[Optional[bool]] = mapped_column(Boolean)
    post_count: Mapped[Optional[int]] = mapped_column(Integer)
    previous_usernames: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    profile_colour: Mapped[Optional[str]] = mapped_column(String)
    profile_hue: Mapped[Optional[int]] = mapped_column(Integer)
    profile_order: Mapped[Optional[list[str]]] = mapped_column(JSONB)
    rank_highest: Mapped[Optional[dict[str, Union[int, datetime]]]] = mapped_column(JSONB)
    rank_history: Mapped[Optional[dict[str, Union[str, list[int]]]]] = mapped_column(JSONB)
    ranked_and_approved_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    ranked_beatmapset_count: Mapped[Optional[int]] = mapped_column(Integer)
    replays_watched_counts: Mapped[Optional[list[dict[str, Union[date, int]]]]] = mapped_column(JSONB)
    scores_best_count: Mapped[Optional[int]] = mapped_column(Integer)
    scores_first_count: Mapped[Optional[int]] = mapped_column(Integer)
    scores_pinned_count: Mapped[Optional[int]] = mapped_column(Integer)
    scores_recent_count: Mapped[Optional[int]] = mapped_column(Integer)
    statistics: Mapped[Optional[dict[str, Union[int, dict[str, Union[int, str, None]], float, bool, None]]]] = mapped_column(JSONB)
    support_level: Mapped[Optional[int]] = mapped_column(Integer)
    team: Mapped[Optional[dict[str, Union[str, int]]]] = mapped_column(JSONB)
    title: Mapped[Optional[str]] = mapped_column(String)
    title_url: Mapped[Optional[str]] = mapped_column(String)
    twitter: Mapped[Optional[str]] = mapped_column(String)
    user_achievements: Mapped[Optional[list[dict[str, Union[datetime, int]]]]] = mapped_column(JSONB)
    username: Mapped[Optional[str]] = mapped_column(String)
    website: Mapped[Optional[str]] = mapped_column(String)

    # Hybrid annotations
    total_maps: Mapped[int]
    total_kudosu: Mapped[int]
    # TODO: Yeah... a lot of shit

    @hybrid_property
    def total_maps(self) -> int:  # Missing approved maps?
        return (
            (self.graveyard_beatmapset_count or 0) +
            (self.loved_beatmapset_count or 0) +
            (self.pending_beatmapset_count or 0) +
            (self.ranked_beatmapset_count or 0)
        )

    @total_maps.expression
    def total_maps(cls):
        return (
            func.coalesce(cls.graveyard_beatmapset_count, 0) +
            func.coalesce(cls.loved_beatmapset_count, 0) +
            func.coalesce(cls.pending_beatmapset_count, 0) +
            func.coalesce(cls.ranked_beatmapset_count, 0)
        )

    @hybrid_property
    def total_kudosu(self) -> int:
        return self.kudosu.get("total", 0) if self.kudosu else 0

    @total_kudosu.expression
    def total_kudosu(cls):
        return func.coalesce(cast(cls.kudosu["total"].astext, Integer), 0)
