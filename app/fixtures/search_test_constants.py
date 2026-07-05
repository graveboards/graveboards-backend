"""Search test fixture constants for comprehensive search engine testing.

Provides all constants needed for the SearchTestFixtureFetcher, including
osu! API spec values for genres, languages, beatmap statuses/modes,
and country codes for profile filtering.
"""

GENRE_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14]
GENRE_NAMES = {
    0: "Any", 1: "Unspecified", 2: "Video Game", 3: "Anime", 4: "Rock", 5: "Pop",
    6: "Other", 7: "Novelty", 9: "Hip Hop", 10: "Electronic", 11: "Metal",
    12: "Classical", 13: "Folk", 14: "Jazz",
}

LANGUAGE_IDS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
LANGUAGE_NAMES = {
    0: "Any", 1: "Unspecified", 2: "English", 3: "Japanese", 4: "Chinese",
    5: "Instrumental", 6: "Korean", 7: "French", 8: "German", 9: "Swedish",
    10: "Spanish", 11: "Italian", 12: "Russian", 13: "Polish", 14: "Other",
}

COUNTRY_CODES = [
    "US", "GB", "DE", "FR", "JP", "KR", "CN", "BR", "RU", "AU", "CA", "IT",
    "ES", "NL", "SE", "NO", "DK", "FI", "PL", "CZ", "HU", "RO", "BG", "GR",
    "TR", "IL", "IN", "TH", "VN", "PH", "MY", "SG", "ID", "TW", "HK", "AR",
    "CL", "CO", "PE", "ZA", "EG", "SA", "AE", "PK", "BD", "LK", "NP",
]

BEATMAP_STATUSES = [-2, -1, 0, 1, 2, 3, 4, 5]
BEATMAP_STATUS_NAMES = {
    -2: "wip", -1: "pending", 0: "qualified", 1: "loved",
    2: "ranked", 3: "approved", 4: "deleted", 5: "graveyard",
}

BEATMAP_MODES = [0, 1, 2, 3]
BEATMAP_MODE_NAMES = {0: "osu", 1: "taiko", 2: "catch", 3: "mania"}
