from copy import copy
from datetime import datetime
from typing import Any

from typing import Optional

from pydantic.main import BaseModel
from pydantic.config import ConfigDict
from pydantic.functional_validators import model_validator

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
    UserStatisticsSchema,
    UserAccountHistorySchema,
    UserAchievementSchema,
    UserBadgeSchema,
    UserMonthlyPlaycountSchema,
    UserGroupSchema
)


class ProfileSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    user_id: int
    updated_at: Optional[datetime] = None
    is_restricted: Optional[bool] = None

    account_history: Optional[list["UserAccountHistorySchema"]]
    active_tournament_banners: Optional[list["ProfileBannerSchema"]]
    avatar_url: Optional[str]
    badges: Optional[list["UserBadgeSchema"]]
    beatmap_playcounts_count: Optional[int]
    comments_count: Optional[int]
    country_code: Optional[str]
    country: Optional["CountrySchema"]
    cover: Optional["CoverSchema"]
    daily_challenge_user_stats: Optional["DailyChallengeUserStatsSchema"]
    default_group: Optional[str]
    discord: Optional[str]
    favourite_beatmapset_count: Optional[int]
    follower_count: Optional[int]
    graveyard_beatmapset_count: Optional[int]
    groups: Optional[list["UserGroupSchema"]]
    guest_beatmapset_count: Optional[int]
    has_supported: Optional[bool]
    interests: Optional[str]
    is_active: Optional[bool]
    is_bot: Optional[bool]
    is_deleted: Optional[bool]
    is_online: Optional[bool]
    is_supporter: Optional[bool]
    join_date: Optional[datetime]
    kudosu: Optional["KudosuSchema"]
    location: Optional[str]
    loved_beatmapset_count: Optional[int]
    last_visit: Optional[datetime]
    mapping_follower_count: Optional[int]
    matchmaking_stats: Optional[list["MatchmakingStatsSchema"]]
    max_blocks: Optional[int]
    max_friends: Optional[int]
    monthly_playcounts: Optional[list["UserMonthlyPlaycountSchema"]]
    nominated_beatmapset_count: Optional[int]
    occupation: Optional[str]
    page: Optional["PageSchema"]
    pending_beatmapset_count: Optional[int]
    playmode: Optional[RulesetLiteral]
    playstyle: Optional[list[PlaystyleLiteral]]
    pm_friends_only: Optional[bool]
    post_count: Optional[int]
    previous_usernames: Optional[list[str]]
    profile_colour: Optional[str]
    profile_hue: Optional[int]
    profile_order: Optional[list[ProfilePageLiteral]]
    rank_highest: Optional["RankHighestSchema"]
    rank_history: Optional["RankHistorySchema"]
    ranked_and_approved_beatmapset_count: Optional[int]
    ranked_beatmapset_count: Optional[int]
    replays_watched_counts: Optional[list["ReplayWatchedCountSchema"]]
    scores_best_count: Optional[int]
    scores_first_count: Optional[int]
    scores_pinned_count: Optional[int]
    scores_recent_count: Optional[int]
    statistics: Optional["UserStatisticsSchema"]
    support_level: Optional[int]
    team: Optional["TeamSchema"]
    title: Optional[str]
    title_url: Optional[str]
    twitter: Optional[str]
    user_achievements: Optional[list["UserAchievementSchema"]]
    username: Optional[str]
    website: Optional[str]


class ProfileCreateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    user_id: int


class ProfileUpdateSchema(BaseModel, BaseModelExtra):
    model_config = ConfigDict(from_attributes=True, extra="forbid")

    updated_at: Optional[datetime] = None
    is_restricted: Optional[bool] = None
    active_tournament_banners: Optional[list["ProfileBannerSchema"]] = None
    avatar_url: Optional[str] = None
    badges: Optional[list["UserBadgeSchema"]] = None
    beatmap_playcounts_count: Optional[int] = None
    comments_count: Optional[int] = None
    country_code: Optional[str] = None
    country: Optional["CountrySchema"] = None
    cover: Optional["CoverSchema"] = None
    daily_challenge_user_stats: Optional["DailyChallengeUserStatsSchema"] = None
    default_group: Optional[str] = None
    discord: Optional[str] = None
    favourite_beatmapset_count: Optional[int] = None
    follower_count: Optional[int] = None
    graveyard_beatmapset_count: Optional[int] = None
    groups: Optional[list["UserGroupSchema"]] = None
    guest_beatmapset_count: Optional[int] = None
    has_supported: Optional[bool] = None
    interests: Optional[str] = None
    is_active: Optional[bool] = None
    is_bot: Optional[bool] = None
    is_deleted: Optional[bool] = None
    is_online: Optional[bool] = None
    is_supporter: Optional[bool] = None
    join_date: Optional[datetime] = None
    kudosu: Optional["KudosuSchema"] = None
    location: Optional[str] = None
    loved_beatmapset_count: Optional[int] = None
    last_visit: Optional[datetime] = None
    mapping_follower_count: Optional[int] = None
    matchmaking_stats: Optional[list["MatchmakingStatsSchema"]] = None
    max_blocks: Optional[int] = None
    max_friends: Optional[int] = None
    monthly_playcounts: Optional[list["UserMonthlyPlaycountSchema"]] = None
    nominated_beatmapset_count: Optional[int] = None
    occupation: Optional[str] = None
    page: Optional["PageSchema"] = None
    pending_beatmapset_count: Optional[int] = None
    playmode: Optional[RulesetLiteral] = None
    playstyle: Optional[list[PlaystyleLiteral]] = None
    pm_friends_only: Optional[bool] = None
    post_count: Optional[int] = None
    previous_usernames: Optional[list[str]] = None
    profile_colour: Optional[str] = None
    profile_hue: Optional[int] = None
    profile_order: Optional[list[ProfilePageLiteral]] = None
    rank_highest: Optional["RankHighestSchema"] = None
    rank_history: Optional["RankHistorySchema"] = None
    ranked_and_approved_beatmapset_count: Optional[int] = None
    ranked_beatmapset_count: Optional[int] = None
    replays_watched_counts: Optional[list["ReplayWatchedCountSchema"]] = None
    scores_best_count: Optional[int] = None
    scores_first_count: Optional[int] = None
    scores_pinned_count: Optional[int] = None
    scores_recent_count: Optional[int] = None
    statistics: Optional["UserStatisticsSchema"] = None
    support_level: Optional[int] = None
    team: Optional["TeamSchema"] = None
    title: Optional[str] = None
    title_url: Optional[str] = None
    twitter: Optional[str] = None
    user_achievements: Optional[list["UserAchievementSchema"]] = None
    username: Optional[str] = None
    website: Optional[str] = None

    @model_validator(mode="before")
    @classmethod
    def from_osu_api_format(cls, data: Any) -> Any:
        if isinstance(data, dict):
            data_copy = copy(data)
            data_copy["user_id"] = data_copy.pop("id")

            if data_copy["username"] in {"[deleted user]", f"DeletedUser_{data_copy["user_id"]}"}:  # Inb4 someone namechanges to this
                data_copy["is_deleted"] = True

            if data_copy["is_deleted"]:
                data_copy["username"] = None

            return data_copy

        return data
