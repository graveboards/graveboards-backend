from datetime import datetime
from typing import Optional, Union, TYPE_CHECKING

from sqlalchemy.sql import select
from sqlalchemy.sql.schema import ForeignKey, UniqueConstraint
from sqlalchemy.sql.sqltypes import Integer, String, DateTime, Boolean, Float
from sqlalchemy.orm import relationship, mapped_column
from sqlalchemy.orm.base import Mapped
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.dialects.postgresql.json import JSONB
from sqlalchemy.dialects.postgresql.array import ARRAY

from app.utils import aware_utcnow
from .base import Base
from .associations import beatmap_snapshot_beatmapset_snapshot_association, beatmapset_tag_beatmapset_snapshot_association

if TYPE_CHECKING:
    from .beatmap_snapshot import BeatmapSnapshot
    from .beatmapset_tag import BeatmapsetTag
    from .profile import Profile


class BeatmapsetSnapshot(Base):
    __tablename__ = "beatmapset_snapshots"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    beatmapset_id: Mapped[int] = mapped_column(Integer, ForeignKey("beatmapsets.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("users.id"), nullable=False)
    snapshot_number: Mapped[int] = mapped_column(Integer, nullable=False)
    snapshot_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=aware_utcnow)
    checksum: Mapped[str] = mapped_column(String(32), unique=True, nullable=False)
    verified: Mapped[bool] = mapped_column(Boolean, default=False)

    # osu! API datastructure
    artist: Mapped[str] = mapped_column(String, nullable=False)
    artist_unicode: Mapped[str] = mapped_column(String, nullable=False)
    availability: Mapped[dict[str, Union[bool, str, None]]] = mapped_column(JSONB, nullable=False)
    bpm: Mapped[float] = mapped_column(Float, nullable=False)
    can_be_hyped: Mapped[bool] = mapped_column(Boolean, nullable=False)
    covers: Mapped[Optional[dict[str, str]]] = mapped_column(JSONB)
    creator: Mapped[str] = mapped_column(String, nullable=False)
    current_nominations: Mapped[list[dict[str, Union[int, list[str], bool]]]] = mapped_column(JSONB, nullable=False)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    description: Mapped[dict[str, str]] = mapped_column(JSONB, nullable=False)
    discussion_enabled: Mapped[bool] = mapped_column(Boolean, nullable=False)
    discussion_locked: Mapped[bool] = mapped_column(Boolean, nullable=False)
    favourite_count: Mapped[int] = mapped_column(Integer, nullable=False)
    genre: Mapped[Optional[dict[str, Union[int, str]]]] = mapped_column(JSONB)
    hype: Mapped[Optional[dict[str, int]]] = mapped_column(JSONB)
    is_scoreable: Mapped[bool] = mapped_column(Boolean, nullable=False)
    language: Mapped[Optional[dict[str, Union[int, str]]]] = mapped_column(JSONB)
    last_updated: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    legacy_thread_url: Mapped[Optional[str]] = mapped_column(String)
    nominations_summary: Mapped[dict[str, Union[int, list[str], dict[str, int], None]]] = mapped_column(JSONB, nullable=False)
    nsfw: Mapped[bool] = mapped_column(Boolean, nullable=False)
    offset: Mapped[int] = mapped_column(Integer, nullable=False)
    pack_tags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False)
    play_count: Mapped[int] = mapped_column(Integer, nullable=False)
    preview_url: Mapped[str] = mapped_column(String, nullable=False)
    ranked: Mapped[int] = mapped_column(Integer, nullable=False)
    ranked_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    rating: Mapped[float] = mapped_column(Float, nullable=False)
    ratings: Mapped[list[int]] = mapped_column(ARRAY(Integer), nullable=False)
    source: Mapped[str] = mapped_column(String, nullable=False)
    spotlight: Mapped[bool] = mapped_column(Boolean, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    storyboard: Mapped[bool] = mapped_column(Boolean, nullable=False)
    submitted_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tags: Mapped[str] = mapped_column(String, nullable=False)
    title: Mapped[str] = mapped_column(String, nullable=False)
    title_unicode: Mapped[str] = mapped_column(String, nullable=False)
    track_id: Mapped[Optional[int]] = mapped_column(Integer)
    video: Mapped[bool] = mapped_column(Boolean, nullable=False)

    # Relationships
    beatmap_snapshots: Mapped[list["BeatmapSnapshot"]] = relationship(
        "BeatmapSnapshot",
        secondary=beatmap_snapshot_beatmapset_snapshot_association,
        back_populates="beatmapset_snapshots",
        lazy=True
    )
    beatmapset_tags: Mapped[list["BeatmapsetTag"]] = relationship(
        "BeatmapsetTag",
        secondary=beatmapset_tag_beatmapset_snapshot_association,
        lazy=True
    )
    user_profile: Mapped["Profile"] = relationship(
        "Profile",
        primaryjoin="foreign(BeatmapsetSnapshot.user_id) == remote(Profile.user_id)",
        uselist=False,
        overlaps="beatmapset_snapshots",
        lazy=True
    )

    # Hybrid annotations
    availability_download_disabled: Mapped[bool]
    availability_more_information: Mapped[Optional[str]]
    description_description: Mapped[str]
    genre_name: Mapped[str]
    genre_id: Mapped[int]
    genre_name: Mapped[str]
    hype_current: Mapped[int]
    hype_required: Mapped[int]
    language_id: Mapped[int]
    language_name: Mapped[str]
    # tags: Mapped[str]
    nominations_summary_current: Mapped[int]
    nominations_summary_required_meta_main_ruleset: Mapped[int]
    nominations_summary_required_meta_non_main_ruleset: Mapped[int]
    num_difficulties: Mapped[int]
    sr_gaps: Mapped[list[float]]
    sr_gaps_min: Mapped[float]
    sr_gaps_max: Mapped[float]
    sr_gaps_avg: Mapped[float]
    hit_lengths: Mapped[list[int]]
    hit_lengths_min: Mapped[int]
    hit_lengths_max: Mapped[int]
    hit_lengths_avg: Mapped[int]

    __table_args__ = (
        UniqueConstraint("beatmapset_id", "snapshot_number", name="_beatmapset_and_snapshot_number_uc"),
    )

    @hybrid_property
    def availability_download_disabled(self) -> bool:
        return self.availability["download_disabled"]

    @availability_download_disabled.expression
    def availability_download_disabled(cls):
        from app.database.ctes.bms_ss.availability import availability_download_disabled_cte

        return (
            select(availability_download_disabled_cte.c.target)
            .where(availability_download_disabled_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def availability_more_information(self) -> str | None:
        return self.availability["more_information"]

    @availability_more_information.expression
    def availability_more_information(cls):
        from app.database.ctes.bms_ss.availability import availability_more_information_cte

        return (
            select(availability_more_information_cte.c.target)
            .where(availability_more_information_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def description_description(self) -> str:
        return self.description["description"]

    @description_description.expression
    def description_description(cls):
        from app.database.ctes.bms_ss.description import description_description_cte

        return (
            select(description_description_cte.c.target)
            .where(description_description_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def genre_id(self) -> int | None:
        if self.genre and "id" in self.genre:
            return self.genre["id"]

        return None

    @genre_id.expression
    def genre_id(cls):
        from app.database.ctes.bms_ss.genre import genre_id_cte

        return (
            select(genre_id_cte.c.target)
            .where(genre_id_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def genre_name(self) -> str | None:
        if self.genre and "name" in self.genre:
            return self.genre["name"]

        return None

    @genre_name.expression
    def genre_name(cls):
        from app.database.ctes.bms_ss.genre import genre_name_cte

        return (
            select(genre_name_cte.c.target)
            .where(genre_name_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hype_current(self) -> int | None:
        if self.hype and "current" in self.hype:
            return self.hype["current"]

        return None

    @hype_current.expression
    def hype_current(cls):
        from app.database.ctes.bms_ss.hype import hype_current_cte

        return (
            select(hype_current_cte.c.target)
            .where(hype_current_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hype_required(self) -> str | None:
        if self.hype and "required" in self.hype:
            return self.hype["required"]

        return None

    @hype_required.expression
    def hype_required(cls):
        from app.database.ctes.bms_ss.hype import hype_required_cte

        return (
            select(hype_required_cte.c.target)
            .where(hype_required_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def language_id(self) -> int | None:
        if self.language and "id" in self.language:
            return self.language["id"]

        return None

    @language_id.expression
    def language_id(cls):
        from app.database.ctes.bms_ss.language import language_id_cte

        return (
            select(language_id_cte.c.target)
            .where(language_id_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def language_name(self) -> str | None:
        if self.language and "name" in self.language:
            return self.language["name"]

        return None

    @language_name.expression
    def language_name(cls):
        from app.database.ctes.bms_ss.language import language_name_cte

        return (
            select(language_name_cte.c.target)
            .where(language_name_cte.c.beatmapset_snapshot_id == cls.id)
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
        return self.nominations_summary["current"]

    @nominations_summary_current.expression
    def nominations_summary_current(cls):
        from app.database.ctes.bms_ss.nominations_summary import nominations_summary_current_cte

        return (
            select(nominations_summary_current_cte.c.target)
            .where(nominations_summary_current_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def nominations_summary_required_meta_main_ruleset(self) -> int:
        return self.nominations_summary["required_meta"]["main_ruleset"]

    @nominations_summary_required_meta_main_ruleset.expression
    def nominations_summary_required_meta_main_ruleset(cls):
        from app.database.ctes.bms_ss.nominations_summary import nominations_summary_required_meta_main_ruleset_cte

        return (
            select(nominations_summary_required_meta_main_ruleset_cte.c.target)
            .where(nominations_summary_required_meta_main_ruleset_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def nominations_summary_required_meta_non_main_ruleset(self) -> int:
        return self.nominations_summary["required_meta"]["non_main_ruleset"]

    @nominations_summary_required_meta_non_main_ruleset.expression
    def nominations_summary_required_meta_non_main_ruleset(cls):
        from app.database.ctes.bms_ss.nominations_summary import nominations_summary_required_meta_non_main_ruleset_cte

        return (
            select(nominations_summary_required_meta_non_main_ruleset_cte.c.target)
            .where(nominations_summary_required_meta_non_main_ruleset_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def num_difficulties(self) -> int:
        return len(self.beatmap_snapshots)

    @num_difficulties.expression
    def num_difficulties(cls):
        from app.database.ctes.bms_ss.num_difficulties import num_difficulties_cte

        return (
            select(num_difficulties_cte.c.target)
            .where(num_difficulties_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps(self) -> list[float]:
        if not self.beatmap_snapshots:
            raise AttributeError(f"There are no beatmap_snapshots in BeatmapsetSnapshot {self.id}")

        ratings = sorted([snapshot.difficulty_rating for snapshot in self.beatmap_snapshots])
        diffs = [round(abs(ratings[i] - ratings[i + 1]), 2) for i in range(len(ratings) - 1)]

        return diffs if len(ratings) > 1 else []

    @sr_gaps.expression
    def sr_gaps(cls):
        from app.database.ctes.bms_ss.sr_gap import sr_gap_agg_cte

        return (
            select(sr_gap_agg_cte.c.sr_gap_agg)
            .where(sr_gap_agg_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_min(self) -> float:
        return min(self.sr_gaps)

    @sr_gaps_min.expression
    def sr_gaps_min(cls):
        from app.database.ctes.bms_ss.sr_gap import min_sr_gap_cte

        return (
            select(min_sr_gap_cte.c.target)
            .where(min_sr_gap_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_max(self) -> float:
        return max(self.sr_gaps)

    @sr_gaps_max.expression
    def sr_gaps_max(cls):
        from app.database.ctes.bms_ss.sr_gap import max_sr_gap_cte

        return (
            select(max_sr_gap_cte.c.target)
            .where(max_sr_gap_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def sr_gaps_avg(self) -> float:
        return round(sum(self.sr_gaps) / len(self.sr_gaps), 2)

    @sr_gaps_avg.expression
    def sr_gaps_avg(cls):
        from app.database.ctes.bms_ss.sr_gap import avg_sr_gap_cte

        return (
            select(avg_sr_gap_cte.c.target)
            .where(avg_sr_gap_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths(self) -> list[int]:
        if not self.beatmap_snapshots:
            raise AttributeError(f"There are no beatmap_snapshots in BeatmapsetSnapshot {self.id}")

        return [snapshot.hit_length for snapshot in self.beatmap_snapshots]

    @hit_lengths.expression
    def hit_lengths(cls):
        from app.database.ctes.bms_ss.hit_length import hit_length_agg_cte

        return (
            select(hit_length_agg_cte.c.hit_length_agg)
            .where(hit_length_agg_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_min(self) -> int:
        return min(self.hit_lengths)

    @hit_lengths_min.expression
    def hit_lengths_min(cls):
        from app.database.ctes.bms_ss.hit_length import min_hit_length_cte

        return (
            select(min_hit_length_cte.c.target)
            .where(min_hit_length_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_max(self) -> int:
        return max(self.hit_lengths)

    @hit_lengths_max.expression
    def hit_lengths_max(cls):
        from app.database.ctes.bms_ss.hit_length import max_hit_length_cte

        return (
            select(max_hit_length_cte.c.target)
            .where(max_hit_length_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )

    @hybrid_property
    def hit_lengths_avg(self) -> float:
        return round(sum(self.hit_lengths) / len(self.hit_lengths), 2)

    @hit_lengths_avg.expression
    def hit_lengths_avg(cls):
        from app.database.ctes.bms_ss.hit_length import avg_hit_length_cte

        return (
            select(avg_hit_length_cte.c.target)
            .where(avg_hit_length_cte.c.beatmapset_snapshot_id == cls.id)
            .scalar_subquery()
        )
