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
