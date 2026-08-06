"""Re-exports for osu! API client and enums."""

from __future__ import annotations

from typing import Any

__all__ = [
    "APIEndpoint",
    "GenreId",
    "GenreIdLiteral",
    "GenreName",
    "GenreNameLiteral",
    "LanguageId",
    "LanguageIdLiteral",
    "LanguageName",
    "LanguageNameLiteral",
    "OsuAPIClient",
    "PlaystyleLiteral",
    "ProfilePage",
    "ProfilePageLiteral",
    "RankedInt",
    "RankedIntLiteral",
    "RankedStatus",
    "RankedStatusLiteral",
    "Ruleset",
    "RulesetIntLiteral",
    "RulesetLiteral",
    "ScoreType",
]


def __getattr__(name: str) -> Any:
    if name == "OsuAPIClient":
        from .client import OsuAPIClient

        return OsuAPIClient

    if name in {
        "APIEndpoint",
        "ScoreType",
        "Ruleset",
        "ProfilePage",
        "RankedInt",
        "RankedStatus",
        "GenreId",
        "GenreName",
        "LanguageId",
        "LanguageName",
    }:
        from . import enums

        return getattr(enums, name)

    if name in {
        "RulesetLiteral",
        "RulesetIntLiteral",
        "PlaystyleLiteral",
        "ProfilePageLiteral",
        "RankedIntLiteral",
        "RankedStatusLiteral",
        "GenreIdLiteral",
        "GenreNameLiteral",
        "LanguageIdLiteral",
        "LanguageNameLiteral",
    }:
        from . import literals

        return getattr(literals, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
