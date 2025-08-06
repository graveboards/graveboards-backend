from enum import Enum, IntEnum

__all__ = [
    "APIEndpoint",
    "ScoreType",
    "Ruleset",
    "ProfilePage",
    "RankedInt",
    "RankedStatus",
    "GenreId",
    "GenreName",
    "LanguageId",
    "LanguageName"
]

API_BASEURL = "https://osu.ppy.sh/api/v2"


class APIEndpoint(Enum):
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

    # Users
    ME = API_BASEURL + "/me"
    SCORES = API_BASEURL + "/users/{user}/scores/{type}"
    USER = API_BASEURL + "/users/{user}/{mode}"

    # Tags
    TAGS = API_BASEURL + "/tags"

    def format(self, *args, **kwargs) -> str:
        args = [arg if arg is not None else "" for arg in args]
        kwargs = {key: value if value is not None else "" for key, value in kwargs.items()}

        return str.format(self.value, *args, **kwargs).rstrip("/")


class ScoreType(Enum):
    BEST = "best"
    FIRSTS = "firsts"
    RECENT = "recent"


class Ruleset(Enum):
    FRUITS = "fruits"
    MANIA = "mania"
    OSU = "osu"
    TAIKO = "taiko"


class ProfilePage(Enum):
    ME = "me"
    RECENT_ACTIVITY = "recent_activity"
    BEATMAPS = "beatmaps"
    HISTORICAL = "historical"
    KUDOSU = "kudosu"
    TOP_RANKS = "top_ranks"
    MEDALS = "medals"


class RankedInt(IntEnum):
    GRAVEYARD = -2
    WIP = -1
    PENDING = 0
    RANKED = 1
    APPROVED = 2
    QUALIFIED = 3
    LOVED = 4


class RankedStatus(Enum):
    GRAVEYARD = "graveyard"
    WIP = "wip"
    PENDING = "pending"
    RANKED = "ranked"
    APPROVED = "approved"
    QUALIFIED = "qualified"
    LOVED = "loved"


class GenreId(IntEnum):
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
