from datetime import date, datetime

from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql.expression import cast
from sqlalchemy.sql.functions import func
from sqlalchemy.sql.schema import ForeignKey
from sqlalchemy.sql.sqltypes import Boolean, DateTime, Integer, String

from app.utils import aware_utcnow

from .base import Base


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=aware_utcnow, onupdate=aware_utcnow
    )
    is_restricted: Mapped[bool] = mapped_column(Boolean, default=False)

    # osu! API datastructure
    account_history: Mapped[list[dict[str, str | int | bool | datetime | None]] | None] = (
        mapped_column(JSONB)
    )
    active_tournament_banners: Mapped[list[dict[str, str | int | None]] | None] = mapped_column(
        JSONB
    )
    avatar_url: Mapped[str | None] = mapped_column(String)
    badges: Mapped[list[dict[str, datetime | str]] | None] = mapped_column(JSONB)
    beatmap_playcounts_count: Mapped[int | None] = mapped_column(Integer)
    comments_count: Mapped[int | None] = mapped_column(Integer)
    country_code: Mapped[str | None] = mapped_column(String(2))
    country: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    cover: Mapped[dict[str, str | int | None] | None] = mapped_column(JSONB)
    # current_season_stats  # Unknown
    daily_challenge_user_stats: Mapped[dict[str, int | datetime] | None] = mapped_column(JSONB)
    default_group: Mapped[str | None] = mapped_column(String)
    discord: Mapped[str | None] = mapped_column(String)
    favourite_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    follower_count: Mapped[int | None] = mapped_column(Integer)
    graveyard_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    groups: Mapped[list[dict[str, str | bool | int | list[str] | None]] | None] = mapped_column(
        JSONB
    )
    guest_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    has_supported: Mapped[bool | None] = mapped_column(Boolean)
    interests: Mapped[str | None] = mapped_column(String)
    is_active: Mapped[bool | None] = mapped_column(Boolean)
    is_bot: Mapped[bool | None] = mapped_column(Boolean)
    is_deleted: Mapped[bool | None] = mapped_column(Boolean)
    is_online: Mapped[bool | None] = mapped_column(Boolean)
    is_supporter: Mapped[bool | None] = mapped_column(Boolean)
    join_date: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kudosu: Mapped[dict[str, int] | None] = mapped_column(JSONB)
    location: Mapped[str | None] = mapped_column(String)
    last_visit: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    loved_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    mapping_follower_count: Mapped[int | None] = mapped_column(Integer)
    matchmaking_stats: Mapped[list[dict[str, int | bool | dict[str, bool | int | str]]] | None] = (
        mapped_column(JSONB)
    )
    max_blocks: Mapped[int | None] = mapped_column(Integer)
    max_friends: Mapped[int | None] = mapped_column(Integer)
    monthly_playcounts: Mapped[list[dict[str, date | int]] | None] = mapped_column(JSONB)
    nominated_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    occupation: Mapped[str | None] = mapped_column(String)
    page: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    pending_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    playmode: Mapped[str | None] = mapped_column(String)
    playstyle: Mapped[list[str] | None] = mapped_column(JSONB)
    pm_friends_only: Mapped[bool | None] = mapped_column(Boolean)
    post_count: Mapped[int | None] = mapped_column(Integer)
    previous_usernames: Mapped[list[str] | None] = mapped_column(JSONB)
    profile_colour: Mapped[str | None] = mapped_column(String)
    profile_hue: Mapped[int | None] = mapped_column(Integer)
    profile_order: Mapped[list[str] | None] = mapped_column(JSONB)
    rank_highest: Mapped[dict[str, int | datetime] | None] = mapped_column(JSONB)
    rank_history: Mapped[dict[str, str | list[int]] | None] = mapped_column(JSONB)
    ranked_and_approved_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    ranked_beatmapset_count: Mapped[int | None] = mapped_column(Integer)
    replays_watched_counts: Mapped[list[dict[str, date | int]] | None] = mapped_column(JSONB)
    scores_best_count: Mapped[int | None] = mapped_column(Integer)
    scores_first_count: Mapped[int | None] = mapped_column(Integer)
    scores_pinned_count: Mapped[int | None] = mapped_column(Integer)
    scores_recent_count: Mapped[int | None] = mapped_column(Integer)
    statistics: Mapped[
        dict[str, int | dict[str, int | str | None] | float | bool | None] | None
    ] = mapped_column(JSONB)
    support_level: Mapped[int | None] = mapped_column(Integer)
    team: Mapped[dict[str, str | int] | None] = mapped_column(JSONB)
    title: Mapped[str | None] = mapped_column(String)
    title_url: Mapped[str | None] = mapped_column(String)
    twitter: Mapped[str | None] = mapped_column(String)
    user_achievements: Mapped[list[dict[str, datetime | int]] | None] = mapped_column(JSONB)
    username: Mapped[str | None] = mapped_column(String)
    website: Mapped[str | None] = mapped_column(String)

    # Hybrid annotations
    total_maps: Mapped[int]
    total_kudosu: Mapped[int]
    # TODO: Yeah... a lot of shit

    @hybrid_property
    def total_maps(self) -> int:  # Missing approved maps?
        return (
            (self.graveyard_beatmapset_count or 0)
            + (self.loved_beatmapset_count or 0)
            + (self.pending_beatmapset_count or 0)
            + (self.ranked_beatmapset_count or 0)
        )

    @total_maps.expression
    def total_maps(cls):
        return (
            func.coalesce(cls.graveyard_beatmapset_count, 0)
            + func.coalesce(cls.loved_beatmapset_count, 0)
            + func.coalesce(cls.pending_beatmapset_count, 0)
            + func.coalesce(cls.ranked_beatmapset_count, 0)
        )

    @hybrid_property
    def total_kudosu(self) -> int:
        return self.kudosu.get("total", 0) if self.kudosu else 0

    @total_kudosu.expression
    def total_kudosu(cls):
        return func.coalesce(cast(cls.kudosu["total"].astext, Integer), 0)
