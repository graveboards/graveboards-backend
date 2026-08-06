"""Beatmapset snapshot model storing an archived beatmapset version."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy.dialects.postgresql.array import ARRAY
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import mapped_column, relationship
from sqlalchemy.orm.base import Mapped
from sqlalchemy.sql import select
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Boolean, Float, Integer, String

from app.utils import aware_utcnow

from .associations import (
    beatmap_snapshot_beatmapset_snapshot_association,
    beatmapset_tag_beatmapset_snapshot_association,
)
from .base import Base
from .types import AwareDateTime

if TYPE_CHECKING:
    from sqlalchemy.sql.elements import ColumnElement

    from .beatmap_snapshot import BeatmapSnapshot
    from .beatmapset_listing import BeatmapsetListing
    from .beatmapset_tag import BeatmapsetTag
    from .profile import Profile


class BeatmapsetSnapshot(Base):
    """A versioned snapshot of a beatmapset's osu! API data."""

    __tablename__ = "beatmapset_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmapset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("beatmapsets.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    snapshot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(AwareDateTime(), default=aware_utcnow)
    checksum: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # osu! API datastructure
    artist: Mapped[str] = mapped_column(String, nullable=False)
    artist_unicode: Mapped[str] = mapped_column(String, nullable=False)
    availability: Mapped[dict[str, bool | str | None]] = mapped_column(JSONB, nullable=False)
    bpm: Mapped[float] = mapped_column(Float, nullable=False)
    can_be_hyped: Mapped[bool] = mapped_column(Boolean, nullable=False)
    covers: Mapped[dict[str, str] | None] = mapped_column(JSONB)
    creator: Mapped[str] = mapped_column(String, nullable=False)
    current_nominations: Mapped[list[dict[str, int | list[str] | bool]]] = mapped_column(
        JSONB, nullable=False
    )
    deleted_at: Mapped[datetime | None] = mapped_column(AwareDateTime())
    description: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    discussion_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    discussion_locked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    favourite_count: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[dict[str, int | str] | None] = mapped_column(JSONB)
    hype: Mapped[dict[str, int] | None] = mapped_column(JSONB)
    is_scoreable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    language: Mapped[dict[str, int | str] | None] = mapped_column(JSONB)
    last_updated: Mapped[datetime] = mapped_column(AwareDateTime(), nullable=False)
    legacy_thread_url: Mapped[str | None] = mapped_column(String)
    nominations_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    nsfw: Mapped[bool] = mapped_column(Boolean, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, nullable=False)
    pack_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False)
    preview_url: Mapped[str] = mapped_column(String, nullable=False)
    ranked: Mapped[int] = mapped_column(Integer, nullable=False)
    ranked_date: Mapped[datetime | None] = mapped_column(AwareDateTime())
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ratings: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    spotlight: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    storyboard: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submitted_date: Mapped[datetime] = mapped_column(AwareDateTime())
    tags: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    title_unicode: Mapped[str] = mapped_column(String, nullable=False)
    track_id: Mapped[int | None] = mapped_column(Integer)
    video: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    beatmap_snapshots: Mapped[list[BeatmapSnapshot]] = relationship(
        "BeatmapSnapshot",
        secondary=beatmap_snapshot_beatmapset_snapshot_association,
        back_populates="beatmapset_snapshots",
        lazy=True,
    )
    beatmapset_tags: Mapped[list[BeatmapsetTag]] = relationship(
        "BeatmapsetTag", secondary=beatmapset_tag_beatmapset_snapshot_association, lazy=True
    )
    user_profile: Mapped[Profile] = relationship(
        "Profile",
        primaryjoin="foreign(BeatmapsetSnapshot.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="beatmapset_snapshots",
        lazy=True,
    )
    beatmapset_listing: Mapped[BeatmapsetListing] = relationship(
        "BeatmapsetListing",
        back_populates="beatmapset_snapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
        uselist=False,
        lazy=True,
    )

    # Hybrid annotations defined via @hybrid_property below

    __table_args__ = (
        UniqueConstraint(
            "beatmapset_id", "snapshot_number", name="_beatmapset_and_snapshot_number_uc"
        ),
    )

    @hybrid_property
    def availability_download_disabled(self) -> bool:
        """Whether downloads are marked as disabled for this snapshot."""
        return bool(self.availability["download_disabled"])

    @availability_download_disabled.inplace.expression
    def _availability_download_disabled_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.availability import availability_download_disabled_cte

        return (
            select(availability_download_disabled_cte.c.target)
            .where(availability_download_disabled_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def availability_more_information(self) -> str | None:
        """Free-form more-information field from this snapshot's availability."""
        value = self.availability["more_information"]
        return value if value is None else str(value)

    @availability_more_information.inplace.expression
    def _availability_more_information_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.availability import availability_more_information_cte

        return (
            select(availability_more_information_cte.c.target)
            .where(availability_more_information_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def description_description(self) -> str:
        """Free-form text description of the beatmapset."""
        return str(self.description["description"])

    @description_description.inplace.expression
    def _description_description_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.description import description_description_cte

        return (
            select(description_description_cte.c.target)
            .where(description_description_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def genre_id(self) -> int | None:
        """Numeric genre identifier, if present."""
        if self.genre and "id" in self.genre:
            return int(self.genre["id"])

        return None

    @genre_id.inplace.expression
    def _genre_id_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.genre import genre_id_cte

        return (
            select(genre_id_cte.c.target)
            .where(genre_id_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def genre_name(self) -> str | None:
        """Genre display name, if present."""
        if self.genre and "name" in self.genre:
            return str(self.genre["name"])

        return None

    @genre_name.inplace.expression
    def _genre_name_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.genre import genre_name_cte

        return (
            select(genre_name_cte.c.target)
            .where(genre_name_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hype_current(self) -> int | None:
        """Return the current amount of hype, if present."""
        if self.hype and "current" in self.hype:
            return int(self.hype["current"])

        return None

    @hype_current.inplace.expression
    def _hype_current_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hype import hype_current_cte

        return (
            select(hype_current_cte.c.target)
            .where(hype_current_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hype_required(self) -> str | None:
        """Return the required amount of hype, if present."""
        if self.hype and "required" in self.hype:
            return str(self.hype["required"])

        return None

    @hype_required.inplace.expression
    def _hype_required_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hype import hype_required_cte

        return (
            select(hype_required_cte.c.target)
            .where(hype_required_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def language_id(self) -> int | None:
        """Numeric language identifier, if present."""
        if self.language and "id" in self.language:
            return int(self.language["id"])

        return None

    @language_id.inplace.expression
    def _language_id_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.language import language_id_cte

        return (
            select(language_id_cte.c.target)
            .where(language_id_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def language_name(self) -> str | None:
        """Language display name, if present."""
        if self.language and "name" in self.language:
            return str(self.language["name"])

        return None

    @language_name.inplace.expression
    def _language_name_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.language import language_name_cte

        return (
            select(language_name_cte.c.target)
            .where(language_name_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    # @hybrid_property
    # def tags(self) -> str:
    #     return " ".join(tag.name for tag in self.beatmapset_tags) if self.beatmapset_tags else ""
    #
    # @tags.expression
    # def tags(cls):
    #     from app.database.ctes.bms_ss.tags import beatmapset_tags_cte
    #
    #     return (
    #         select(beatmapset_tags_cte.c.target)
    #         .where(beatmapset_tags_cte.c.id == cls.id)
    #         .scalar_subquery()
    #     )

    @hybrid_property
    def nominations_summary_current(self) -> int:
        """Return the current number of nominations."""
        return int(self.nominations_summary["current"])

    @nominations_summary_current.inplace.expression
    def _nominations_summary_current_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.nominations_summary import nominations_summary_current_cte

        return (
            select(nominations_summary_current_cte.c.target)
            .where(nominations_summary_current_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def nominations_summary_required_meta_main_ruleset(self) -> int:
        """Return the required nominations for the main ruleset."""
        return int(self.nominations_summary["required_meta"]["main_ruleset"])

    @nominations_summary_required_meta_main_ruleset.inplace.expression
    def _nominations_summary_required_meta_main_ruleset_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.nominations_summary import (
            nominations_summary_required_meta_main_ruleset_cte,
        )

        return (
            select(nominations_summary_required_meta_main_ruleset_cte.c.target)
            .where(
                nominations_summary_required_meta_main_ruleset_cte.c.beatmapset_snapshot_id
                == self.id
            )
            .scalar_subquery()
        )

    @hybrid_property
    def nominations_summary_required_meta_non_main_ruleset(self) -> int:
        """Return the required nominations for the non-main ruleset."""
        return int(self.nominations_summary["required_meta"]["non_main_ruleset"])

    @nominations_summary_required_meta_non_main_ruleset.inplace.expression
    def _nominations_summary_required_meta_non_main_ruleset_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.nominations_summary import (
            nominations_summary_required_meta_non_main_ruleset_cte,
        )

        return (
            select(nominations_summary_required_meta_non_main_ruleset_cte.c.target)
            .where(
                nominations_summary_required_meta_non_main_ruleset_cte.c.beatmapset_snapshot_id
                == self.id
            )
            .scalar_subquery()
        )

    @hybrid_property
    def num_difficulties(self) -> int:
        """Return the number of beatmap snapshots in this beatmapset snapshot."""
        return len(self.beatmap_snapshots)

    @num_difficulties.inplace.expression
    def _num_difficulties_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.num_difficulties import num_difficulties_cte

        return (
            select(num_difficulties_cte.c.target)
            .where(num_difficulties_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps(self) -> list[float]:
        """Star rating gaps between the sorted difficulties."""
        if not self.beatmap_snapshots:
            raise AttributeError(f"There are no beatmap_snapshots in BeatmapsetSnapshot {self.id}")

        ratings = sorted([snapshot.difficulty_rating for snapshot in self.beatmap_snapshots])
        diffs = [round(abs(ratings[i] - ratings[i + 1]), 2) for i in range(len(ratings) - 1)]

        return diffs if len(ratings) > 1 else []

    @sr_gaps.inplace.expression
    def _sr_gaps_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.sr_gap import sr_gap_agg_cte

        return (
            select(sr_gap_agg_cte.c.sr_gap_agg)
            .where(sr_gap_agg_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_min(self) -> float:
        """Smallest star rating gap between difficulties."""
        return float(min(self.sr_gaps))

    @sr_gaps_min.inplace.expression
    def _sr_gaps_min_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.sr_gap import min_sr_gap_cte

        return (
            select(min_sr_gap_cte.c.target)
            .where(min_sr_gap_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_max(self) -> float:
        """Largest star rating gap between difficulties."""
        return float(max(self.sr_gaps))

    @sr_gaps_max.inplace.expression
    def _sr_gaps_max_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.sr_gap import max_sr_gap_cte

        return (
            select(max_sr_gap_cte.c.target)
            .where(max_sr_gap_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_avg(self) -> float:
        """Average star rating gap between difficulties."""
        return round(float(sum(self.sr_gaps) / len(self.sr_gaps)), 2)

    @sr_gaps_avg.inplace.expression
    def _sr_gaps_avg_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.sr_gap import avg_sr_gap_cte

        return (
            select(avg_sr_gap_cte.c.target)
            .where(avg_sr_gap_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths(self) -> list[int]:
        """Hit lengths of each beatmap snapshot in this snapshots."""
        if not self.beatmap_snapshots:
            raise AttributeError(f"There are no beatmap_snapshots in BeatmapsetSnapshot {self.id}")

        return [snapshot.hit_length for snapshot in self.beatmap_snapshots]

    @hit_lengths.inplace.expression
    def _hit_lengths_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hit_length import hit_length_agg_cte

        return (
            select(hit_length_agg_cte.c.hit_length_agg)
            .where(hit_length_agg_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_min(self) -> int:
        """Smallest hit length among the beatmap snapshots."""
        return int(min(self.hit_lengths))

    @hit_lengths_min.inplace.expression
    def _hit_lengths_min_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hit_length import min_hit_length_cte

        return (
            select(min_hit_length_cte.c.target)
            .where(min_hit_length_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_max(self) -> int:
        """Largest hit length among the beatmap snapshots."""
        return int(max(self.hit_lengths))

    @hit_lengths_max.inplace.expression
    def _hit_lengths_max_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hit_length import max_hit_length_cte

        return (
            select(max_hit_length_cte.c.target)
            .where(max_hit_length_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_avg(self) -> float:
        """Average hit length among the beatmap snapshots."""
        return round(float(sum(self.hit_lengths) / len(self.hit_lengths)), 2)

    @hit_lengths_avg.inplace.expression
    def _hit_lengths_avg_expr(self) -> ColumnElement:
        from app.database.ctes.bms_ss.hit_length import avg_hit_length_cte

        return (
            select(avg_hit_length_cte.c.target)
            .where(avg_hit_length_cte.c.beatmapset_snapshot_id == self.id)
            .scalar_subquery()
        )
