from __future__ import annotations
from copy import copy
from datetime import datetime
from typing import Any

from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator
from pydantic.main import BaseModel

from app.osu_api.literals import PlaystyleLiteral, ProfilePageLiteral, RulesetLiteral

from .base_model_extra import BaseModelExtra
from .sub_schemas import (
    CountrySchema,
    CoverSchema,
    DailyChallengeUserStatsSchema,
    KudosuSchema,
    MatchmakingStatsSchema,
    PageSchema,
    ProfileBannerSchema,
    RankHighestSchema,
    RankHistorySchema,
    ReplayWatchedCountSchema,
    TeamSchema,
    UserAccountHistorySchema,
    UserAchievementSchema,
    UserBadgeSchema,
    UserGroupSchema,
    UserMonthlyPlaycountSchema,
    UserStatisticsSchema,
)


class ProfileSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: int | None = None
    user_id: int
    updated_at: datetime | None = None
    is_restricted: bool | None = None

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)
            data_copy["user_id"] = data_copy.pop("id")

            if data_copy["username"] in {"[deleted user]", f"DeletedUser_{data_copy['user_id']}"}:
                data_copy["is_deleted"] = True

            if data_copy["is_deleted"]:
                data_copy["username"] = None

            return data_copy

        return data

    account_history: list[UserAccountHistorySchema] | None
    active_tournament_banners: list[ProfileBannerSchema] | None
    avatar_url: str | None
    badges: list[UserBadgeSchema] | None
    beatmap_playcounts_count: int | None
    comments_count: int | None
    country_code: str | None
    country: CountrySchema | None
    cover: CoverSchema | None
    daily_challenge_user_stats: DailyChallengeUserStatsSchema | None
    default_group: str | None
    discord: str | None
    favourite_beatmapset_count: int | None
    follower_count: int | None
    graveyard_beatmapset_count: int | None
    groups: list[UserGroupSchema] | None
    guest_beatmapset_count: int | None
    has_supported: bool | None
    interests: str | None
    is_active: bool | None
    is_bot: bool | None
    is_deleted: bool | None
    is_online: bool | None
    is_supporter: bool | None
    join_date: datetime | None
    kudosu: KudosuSchema | None
    location: str | None
    loved_beatmapset_count: int | None
    last_visit: datetime | None
    mapping_follower_count: int | None
    matchmaking_stats: list[MatchmakingStatsSchema] | None
    max_blocks: int | None
    max_friends: int | None
    monthly_playcounts: list[UserMonthlyPlaycountSchema] | None
    nominated_beatmapset_count: int | None
    occupation: str | None
    page: PageSchema | None
    pending_beatmapset_count: int | None
    playmode: RulesetLiteral | None
    playstyle: list[PlaystyleLiteral] | None
    pm_friends_only: bool | None
    post_count: int | None
    previous_usernames: list[str] | None
    profile_colour: str | None
    profile_hue: int | None
    profile_order: list[ProfilePageLiteral] | None
    rank_highest: RankHighestSchema | None
    rank_history: RankHistorySchema | None
    ranked_and_approved_beatmapset_count: int | None
    ranked_beatmapset_count: int | None
    replays_watched_counts: list[ReplayWatchedCountSchema] | None
    scores_best_count: int | None
    scores_first_count: int | None
    scores_pinned_count: int | None
    scores_recent_count: int | None
    statistics: UserStatisticsSchema | None
    support_level: int | None
    team: TeamSchema | None
    title: str | None
    title_url: str | None
    twitter: str | None
    user_achievements: list[UserAchievementSchema] | None
    username: str | None
    website: str | None


class ProfileCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int


class ProfileUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    updated_at: datetime | None = None
    is_restricted: bool | None = None
    active_tournament_banners: list[ProfileBannerSchema] | None = None
    avatar_url: str | None = None
    badges: list[UserBadgeSchema] | None = None
    beatmap_playcounts_count: int | None = None
    comments_count: int | None = None
    country_code: str | None = None
    country: CountrySchema | None = None
    cover: CoverSchema | None = None
    daily_challenge_user_stats: DailyChallengeUserStatsSchema | None = None
    default_group: str | None = None
    discord: str | None = None
    favourite_beatmapset_count: int | None = None
    follower_count: int | None = None
    graveyard_beatmapset_count: int | None = None
    groups: list[UserGroupSchema] | None = None
    guest_beatmapset_count: int | None = None
    has_supported: bool | None = None
    interests: str | None = None
    is_active: bool | None = None
    is_bot: bool | None = None
    is_deleted: bool | None = None
    is_online: bool | None = None
    is_supporter: bool | None = None
    join_date: datetime | None = None
    kudosu: KudosuSchema | None = None
    location: str | None = None
    loved_beatmapset_count: int | None = None
    last_visit: datetime | None = None
    mapping_follower_count: int | None = None
    matchmaking_stats: list[MatchmakingStatsSchema] | None = None
    max_blocks: int | None = None
    max_friends: int | None = None
    monthly_playcounts: list[UserMonthlyPlaycountSchema] | None = None
    nominated_beatmapset_count: int | None = None
    occupation: str | None = None
    page: PageSchema | None = None
    pending_beatmapset_count: int | None = None
    playmode: RulesetLiteral | None = None
    playstyle: list[PlaystyleLiteral] | None = None
    pm_friends_only: bool | None = None
    post_count: int | None = None
    previous_usernames: list[str] | None = None
    profile_colour: str | None = None
    profile_hue: int | None = None
    profile_order: list[ProfilePageLiteral] | None = None
    rank_highest: RankHighestSchema | None = None
    rank_history: RankHistorySchema | None = None
    ranked_and_approved_beatmapset_count: int | None = None
    ranked_beatmapset_count: int | None = None
    replays_watched_counts: list[ReplayWatchedCountSchema] | None = None
    scores_best_count: int | None = None
    scores_first_count: int | None = None
    scores_pinned_count: int | None = None
    scores_recent_count: int | None = None
    statistics: UserStatisticsSchema | None = None
    support_level: int | None = None
    team: TeamSchema | None = None
    title: str | None = None
    title_url: str | None = None
    twitter: str | None = None
    user_achievements: list[UserAchievementSchema] | None = None
    username: str | None = None
    website: str | None = None

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)
            data_copy["user_id"] = data_copy.pop("id")

            if data_copy["username"] in {
                "[deleted user]",
                f"DeletedUser_{data_copy['user_id']}",
            }:  # Inb4 someone namechanges to this
                data_copy["is_deleted"] = True

            if data_copy["is_deleted"]:
                data_copy["username"] = None

            return data_copy

        return data
