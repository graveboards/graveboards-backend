"""Constants for the fixtures system."""

# Rulesets and score types
RULESETS = ["osu", "taiko", "fruits", "mania"]
SCORE_TYPES = ["best", "firsts", "recent"]

# API limits and retry configuration
TOP_PLAYERS_PER_RULESET = 1000
RANKING_PAGE_SIZE = 50
MAX_RETRIES = 10
MAX_RETRIES_SCORES = 50

# ID ranges for random guessing
ID_RANGE_MIN = 1
ID_RANGES = {
    "beatmaps": {"min": ID_RANGE_MIN, "max": 5_800_000},
    "beatmapsets": {"min": ID_RANGE_MIN, "max": 2_600_000},
    "users": {"min": ID_RANGE_MIN, "max": 40_000_000},
}

# Sample count profiles
BASE_SAMPLE_COUNTS = {
    "beatmaps": 50,
    "beatmapsets": 30,
    "users": {"osu": 25, "taiko": 25, "fruits": 25, "mania": 25},
    "scores": {"best": 15, "firsts": 15, "recent": 15},
    "beatmap_scores": 20,
    "beatmap_attributes": 20,
    "queues": 50,
    "requests": 100,
}

MINIMAL_PROFILE = {
    "beatmaps": 1,
    "beatmapsets": 1,
    "users": {"osu": 1, "taiko": 1, "fruits": 1, "mania": 1},
    "scores": {"best": 1, "firsts": 1, "recent": 1},
    "beatmap_scores": 1,
    "beatmap_attributes": 1,
    "queues": 1,
    "requests": 1,
}

# Discussion/queue statuses
DISCUSSION_STATUSES = ["ranked", "loved", "qualified", "graveyard", "pending", "approved", "all"]
REQUEST_STATUSES = [-1, 0, 1]
REQUEST_STATUS_NAMES = ["rejected", "pending", "accepted"]

# osu! API constants
BEATMAP_STATUSES = [-2, -1, 0, 1, 2, 3, 4, 5]
BEATMAP_STATUS_NAMES = {
    -2: "wip",
    -1: "pending",
    0: "qualified",
    1: "loved",
    2: "ranked",
    3: "approved",
    4: "deleted",
    5: "graveyard",
}

BEATMAP_MODES = [0, 1, 2, 3]
BEATMAP_MODE_NAMES = {0: "osu", 1: "taiko", 2: "catch", 3: "mania"}

GENRE_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14]
GENRE_NAMES = {
    0: "Any",
    1: "Unspecified",
    2: "Video Game",
    3: "Anime",
    4: "Rock",
    5: "Pop",
    6: "Other",
    7: "Novelty",
    9: "Hip Hop",
    10: "Electronic",
    11: "Metal",
    12: "Classical",
    13: "Folk",
    14: "Jazz",
}

LANGUAGE_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
LANGUAGE_NAMES = {
    0: "Any",
    1: "Unspecified",
    2: "English",
    3: "Japanese",
    4: "Chinese",
    5: "Instrumental",
    6: "Korean",
    7: "French",
    8: "German",
    9: "Swedish",
    10: "Spanish",
    11: "Italian",
    12: "Russian",
    13: "Polish",
    14: "Other",
}

COUNTRY_CODES = [
    "US",
    "GB",
    "DE",
    "FR",
    "JP",
    "KR",
    "CN",
    "BR",
    "RU",
    "AU",
    "CA",
    "IT",
    "ES",
    "NL",
    "SE",
    "NO",
    "DK",
    "FI",
    "PL",
    "CZ",
    "HU",
    "RO",
    "BG",
    "GR",
    "TR",
    "IL",
    "IN",
    "TH",
    "VN",
    "PH",
    "MY",
    "SG",
    "ID",
    "TW",
    "HK",
    "AR",
    "CL",
    "CO",
    "PE",
    "ZA",
    "EG",
    "SA",
    "AE",
    "PK",
    "BD",
    "LK",
    "NP",
]
