from typing import Literal

__all__ = [
    "RulesetLiteral",
    "RulesetIntLiteral",
    "PlaystyleLiteral",
    "ProfilePageLiteral",
    "RankedIntLiteral",
    "RankedStatusLiteral",
    "GenreIdLiteral",
    "GenreNameLiteral",
    "LanguageIdLiteral",
    "LanguageNameLiteral"
]

RulesetLiteral = Literal["fruits", "mania", "osu", "taiko"]
RulesetIntLiteral = Literal[0, 1, 2, 3]
PlaystyleLiteral = Literal["mouse", "keyboard", "tablet", "touch"]
ProfilePageLiteral = Literal[
    "me",
    "recent_activity",
    "beatmaps",
    "historical",
    "kudosu",
    "top_ranks",
    "medals"
]
RankedIntLiteral = Literal[-2, -1, 0, 1, 2, 3, 4]
RankedStatusLiteral = Literal[
    "graveyard",
    "wip",
    "pending",
    "ranked",
    "approved",
    "qualified",
    "loved"
]
GenreIdLiteral = Literal[0, 1, 2, 3, 4, 5, 6, 7, 9, 10, 11, 12, 13, 14]
GenreNameLiteral = Literal[
    "Any",
    "Unspecified",
    "Video Game",
    "Anime",
    "Rock",
    "Pop",
    "Other",
    "Novelty",
    "Hip Hop",
    "Electronic",
    "Metal",
    "Classical",
    "Folk",
    "Jazz"
]
LanguageIdLiteral = Literal[0, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14]
LanguageNameLiteral = Literal[
    "Any",
    "Unspecified",
    "English",
    "Japanese",
    "Chinese",
    "Instrumental",
    "Korean",
    "French",
    "German",
    "Swedish",
    "Spanish",
    "Italian",
    "Russian",
    "Polish",
    "Other"
]
