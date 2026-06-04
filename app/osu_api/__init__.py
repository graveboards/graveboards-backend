__all__ = [
    "OsuAPIClient",
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
]


def __getattr__(name):
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
