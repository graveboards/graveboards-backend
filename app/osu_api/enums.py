"""osu! API enumerations for endpoints, score types, and metadata."""

from __future__ import annotations

from enum import Enum, IntEnum

__all__ = [
    "APIEndpoint",
    "GenreId",
    "GenreName",
    "LanguageId",
    "LanguageName",
    "ProfilePage",
    "RankedInt",
    "RankedStatus",
    "Ruleset",
    "ScoreType",
]

API_BASEURL = "https://osu.ppy.sh/api/v2"


class APIEndpoint(Enum):
    """osu! API v2 endpoint URLs.

    Attributes:
        value:
            The full API URL with optional path parameters.
    """

    # Beatmaps
    BEATMAP_PACKS = API_BASEURL + "/beatmaps/packs"
    BEATMAP_LOOKUP = API_BASEURL + "/beatmaps/lookup"
    BEATMAP_USER_SCORE = API_BASEURL + "/beatmaps/{beatmap}/scores/users/{user}"
    BEATMAP_USER_SCORES = API_BASEURL + "/beatmaps/{beatmap}/scores/users/{user}/all"
    BEATMAP_SCORES = API_BASEURL + "/beatmaps/{beatmap}/scores"
    BEATMAPS = API_BASEURL + "/beatmaps"
    BEATMAP = API_BASEURL + "/beatmaps/{beatmap}"
    BEATMAP_ATTRIBUTES = API_BASEURL + "/beatmaps/{beatmap}/attributes"

    # Beatmapsets
    BEATMAPSET_LOOKUP = API_BASEURL + "/beatmapsets/lookup"
    BEATMAPSET = API_BASEURL + "/beatmapsets/{beatmapset}"
    BEATMAPSET_DISCUSSIONS = API_BASEURL + "/beatmapsets/discussions"
    BEATMAPSET_SEARCH = API_BASEURL + "/beatmapsets/search"

    # Users
    ME = API_BASEURL + "/me"
    SCORES = API_BASEURL + "/users/{user}/scores/{type}"
    USER = API_BASEURL + "/users/{user}/{mode}"

    # Rankings
    RANKINGS = API_BASEURL + "/rankings/{ruleset}/{mode}"

    # Tags
    TAGS = API_BASEURL + "/tags"

    def format(self, *args: str, **kwargs: str) -> str:
        """Format the endpoint URL with provided path parameters.

        Args:
            *args:
                Positional path parameters.
            **kwargs:
                Named path parameters.

        Returns:
            The formatted URL with trailing slash removed.
        """
        args = tuple(arg or "" for arg in args)
        kwargs = {key: value or "" for key, value in kwargs.items()}

        return str.format(self.value, *args, **kwargs).rstrip("/")


class ScoreType(Enum):
    """Score display types for user score queries."""

    BEST = "best"
    FIRSTS = "firsts"
    RECENT = "recent"


class Ruleset(Enum):
    """osu! game modes.

    Attributes:
        value:
            The lowercase mode identifier.
    """

    FRUITS = "fruits"
    MANIA = "mania"
    OSU = "osu"
    TAIKO = "taiko"

    @property
    def mode_int(self) -> int:
        """Return the integer mode ID for this ruleset.

        Returns:
            The mode integer (osu=0, taiko=1, fruits=2, mania=3).
        """
        # Canonical osu! mode ordering: osu=0, taiko=1, fruits=2, mania=3.
        return _RULESET_MODE_INT[self]

    @classmethod
    def to_mode_int(cls, ruleset: str | Ruleset) -> int:
        """Convert a ruleset name or instance to its integer mode ID.

        Args:
            ruleset:
                A ruleset name string or Ruleset enum member.

        Returns:
            The integer mode ID.
        """
        if isinstance(ruleset, str):
            ruleset = cls(ruleset)
        return ruleset.mode_int


_RULESET_MODE_INT = {
    Ruleset.OSU: 0,
    Ruleset.TAIKO: 1,
    Ruleset.FRUITS: 2,
    Ruleset.MANIA: 3,
}


class ProfilePage(Enum):
    """osu! profile page types."""

    ME = "me"
    RECENT_ACTIVITY = "recent_activity"
    BEATMAPS = "beatmaps"
    HISTORICAL = "historical"
    KUDOSU = "kudosu"
    TOP_RANKS = "top_ranks"
    MEDALS = "medals"


class RankedInt(IntEnum):
    """Integer representation of beatmap ranked statuses."""

    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class RankedStatus(Enum):
    """String representation of beatmap ranked statuses."""

    GRAVEYARD = "graveyard"
    WIP = "wip"
    PENDING = "pending"
    RANKED = "ranked"
    APPROVED = "approved"
    QUALIFIED = "qualified"
    LOVED = "loved"


class GenreId(IntEnum):
    """Integer genre IDs for beatmap filtering."""

    ANY = 0
    UNSPECIFIED = 1
    VIDEO_GAME = 2
    ANIME = 3
    ROCK = 4
    POP = 5
    OTHER = 6
    NOVELTY = 7
    # 8 is intentionally missing
    HIP_HOP = 9
    ELECTRONIC = 10
    METAL = 11
    CLASSICAL = 12
    FOLK = 13
    JAZZ = 14


class GenreName(Enum):
    """String genre names for beatmap filtering."""

    ANY = "Any"
    UNSPECIFIED = "Unspecified"
    VIDEO_GAME = "Video Game"
    ANIME = "Anime"
    ROCK = "Rock"
    POP = "Pop"
    OTHER = "Other"
    NOVELTY = "Novelty"
    HIP_HOP = "Hip Hop"
    ELECTRONIC = "Electronic"
    METAL = "Metal"
    CLASSICAL = "Classical"
    FOLK = "Folk"
    JAZZ = "Jazz"


class LanguageId(IntEnum):
    """Integer language IDs for beatmap filtering."""

    ANY = 0
    UNSPECIFIED = 1
    ENGLISH = 2
    JAPANESE = 3
    CHINESE = 4
    INSTRUMENTAL = 5
    KOREAN = 6
    FRENCH = 7
    GERMAN = 8
    SWEDISH = 9
    SPANISH = 10
    ITALIAN = 11
    RUSSIAN = 12
    POLISH = 13
    OTHER = 14


class LanguageName(Enum):
    """String language names for beatmap filtering."""

    ANY = "Any"
    UNSPECIFIED = "Unspecified"
    ENGLISH = "English"
    JAPANESE = "Japanese"
    CHINESE = "Chinese"
    INSTRUMENTAL = "Instrumental"
    KOREAN = "Korean"
    FRENCH = "French"
    GERMAN = "German"
    SWEDISH = "Swedish"
    SPANISH = "Spanish"
    ITALIAN = "Italian"
    RUSSIAN = "Russian"
    POLISH = "Polish"
    OTHER = "Other"
