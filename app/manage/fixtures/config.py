"""CLI configuration dataclasses for fixture commands."""

from dataclasses import dataclass
from app.fixtures.criteria import (
    Criteria,
    Source,
    FetchCriteria,
    SearchTestOverrides,
    TargetedOverrides,
)


@dataclass
class FetchConfig:
    """Configuration for fixture fetch commands.

    Aggregates all CLI arguments into a single config object,
    then converts to FetchCriteria for the orchestrator.
    """

    criteria: str = Criteria.STANDARD
    source: str = Source.AUTO
    beatmaps: int = 0
    beatmapsets: int = 0
    users_osu: int = 0
    users_taiko: int = 0
    users_fruits: int = 0
    users_mania: int = 0
    scores_best: int = 0
    scores_firsts: int = 0
    scores_recent: int = 0
    beatmap_scores: int = 0
    beatmap_attributes: int = 0
    status: list[str] | None = None
    difficulty_range: str | None = None
    playcount_range: str | None = None
    activity_tier: str | None = None
    rulesets: list[str] | None = None
    force_fetch: bool = False
    no_progress: bool = False
    verbose: bool = False
    min_per_category: int = 1
    max_total: int = 500
    gaps: bool = False
    full: bool = False
    quick: bool = False
    fixtures_dir: str | None = None
    dry_run: bool = False
    concurrent: bool = False
    concurrency: int = 3
    exclude_ids: str | None = None

    def to_fetch_criteria(self) -> FetchCriteria:
        """Convert to FetchCriteria for the orchestrator."""
        # Build targeted overrides
        targeted_overrides = None
        if self.criteria == Criteria.TARGETED:
            targeted_overrides = TargetedOverrides(
                statuses=self.status,
                difficulty_range=self.difficulty_range,
                playcount_range=self.playcount_range,
                activity_tier=self.activity_tier,
                rulesets=self.rulesets,
            )

        # Build search-test overrides
        search_test_overrides = None
        if self.criteria == Criteria.SEARCH_TEST:
            search_test_overrides = SearchTestOverrides(
                quick=self.quick,
                min_per_category=self.min_per_category,
                max_total=self.max_total,
                gaps=self.gaps,
                full=self.full,
            )

        # Parse exclude IDs
        exclude_ids_list = []
        if self.exclude_ids:
            exclude_ids_list = [
                int(x.strip()) for x in self.exclude_ids.split(",") if x.strip().isdigit()
            ]

        return FetchCriteria(
            criteria=self.criteria,
            source=self.source,
            targeted=targeted_overrides,
            search_test=search_test_overrides,
            beatmaps=self.beatmaps,
            beatmapsets=self.beatmapsets,
            users={
                "osu": self.users_osu,
                "taiko": self.users_taiko,
                "fruits": self.users_fruits,
                "mania": self.users_mania,
            },
            scores={
                "best": self.scores_best,
                "firsts": self.scores_firsts,
                "recent": self.scores_recent,
            },
            beatmap_scores=self.beatmap_scores,
            beatmap_attributes=self.beatmap_attributes,
            force_fetch=self.force_fetch,
            no_progress=self.no_progress,
            verbose=self.verbose,
            fixtures_dir=self.fixtures_dir,
            dry_run=self.dry_run,
            concurrent=self.concurrent,
            concurrency=self.concurrency,
            exclude_ids=exclude_ids_list,
        )
