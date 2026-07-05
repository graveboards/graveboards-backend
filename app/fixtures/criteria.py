"""Declarative criteria and report dataclasses for fixture fetching."""

from dataclasses import dataclass, field
from typing import Any


class Criteria:
    """Coverage/variety profile for fixture fetching."""
    MINIMAL = "minimal"
    STANDARD = "standard"
    TARGETED = "targeted"
    SEARCH_TEST = "search-test"

    ALL = [MINIMAL, STANDARD, TARGETED, SEARCH_TEST]


class Source:
    """ID source priority for fixture fetching."""
    AUTO = "auto"
    ARCHIVE = "archive"
    TOP_PLAYERS = "top-players"

    ALL = [AUTO, ARCHIVE, TOP_PLAYERS]


@dataclass
class TargetedOverrides:
    """Overrides for the targeted criteria."""
    statuses: list[str] | None = None
    difficulty_range: str | None = None
    playcount_range: str | None = None
    activity_tier: str | None = None
    rulesets: list[str] | None = None


@dataclass
class SearchTestOverrides:
    """Overrides for the search-test criteria."""
    quick: bool = False
    min_per_category: int = 1
    max_total: int = 500
    gaps: bool = False
    full: bool = False


@dataclass
class FetchCriteria:
    """Declarative specification of what fixtures to fetch and how.

    Two orthogonal dimensions:
    - criteria: what variety to achieve (minimal, standard, targeted, search-test)
    - source: where to get IDs (auto, archive, top-players)
    """

    # Coverage profile
    criteria: str = Criteria.STANDARD

    # ID source
    source: str = Source.AUTO

    # Overrides per criteria
    targeted: TargetedOverrides = field(default_factory=TargetedOverrides)
    search_test: SearchTestOverrides = field(default_factory=SearchTestOverrides)

    # Data type counts (used by standard criteria, can override minimal)
    beatmaps: int = 0
    beatmapsets: int = 0
    users: dict[str, int] = field(default_factory=lambda: {"osu": 0, "taiko": 0, "fruits": 0, "mania": 0})
    scores: dict[str, int] = field(default_factory=lambda: {"best": 0, "firsts": 0, "recent": 0})
    beatmap_scores: int = 0
    beatmap_attributes: int = 0

    # Behavior
    force_fetch: bool = False
    no_progress: bool = False
    verbose: bool = False
    dry_run: bool = False
    concurrent: bool = False
    concurrency: int = 3
    exclude_ids: list[int] = field(default_factory=list)

    # Custom fixtures directory
    fixtures_dir: str | None = None

    @property
    def is_targeted(self) -> bool:
        return self.criteria == Criteria.TARGETED

    @property
    def is_search_test(self) -> bool:
        return self.criteria == Criteria.SEARCH_TEST

    @property
    def is_minimal(self) -> bool:
        return self.criteria == Criteria.MINIMAL

    @property
    def is_standard(self) -> bool:
        return self.criteria == Criteria.STANDARD

    def resolve_sample_counts(self) -> dict:
        """Convert criteria into the sample_counts format expected by fetchers."""
        # Minimal: 1 of each type (unless explicitly overridden)
        if self.is_minimal:
            from app.fixtures.utils import calculate_sample_counts
            return calculate_sample_counts(
                scale=1.0,
                beatmaps=self.beatmaps or 1,
                beatmapsets=self.beatmapsets or 1,
                users_osu=self.users.get("osu", 1),
                users_taiko=self.users.get("taiko", 1),
                users_fruits=self.users.get("fruits", 1),
                users_mania=self.users.get("mania", 1),
                scores_best=self.scores.get("best", 1),
                scores_firsts=self.scores.get("firsts", 1),
                scores_recent=self.scores.get("recent", 1),
                beatmap_scores=self.beatmap_scores or 1,
                beatmap_attributes=self.beatmap_attributes or 1,
                use_minimal=False,
            )

        from app.fixtures.utils import calculate_sample_counts
        return calculate_sample_counts(
            scale=1.0,
            beatmaps=self.beatmaps,
            beatmapsets=self.beatmapsets,
            users_osu=self.users.get("osu", 0),
            users_taiko=self.users.get("taiko", 0),
            users_fruits=self.users.get("fruits", 0),
            users_mania=self.users.get("mania", 0),
            scores_best=self.scores.get("best", 0),
            scores_firsts=self.scores.get("firsts", 0),
            scores_recent=self.scores.get("recent", 0),
            beatmap_scores=self.beatmap_scores,
            beatmap_attributes=self.beatmap_attributes,
            use_minimal=False,
        )


@dataclass
class FetchReport:
    """Results from a fetch operation."""
    criteria: str
    results: dict[str, Any] = field(default_factory=dict)
    coverage: dict[str, Any] | None = None
    errors: list[str] = field(default_factory=list)

    def summary(self) -> dict:
        return {
            "criteria": self.criteria,
            "results": self.results,
            "errors": self.errors,
        }
