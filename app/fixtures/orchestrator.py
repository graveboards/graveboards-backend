"""Unified fixture fetch orchestrator.

Composes ID sources, coverage strategies, and the fetch pipeline into a
single declarative interface. The CLI passes a FetchCriteria and the
orchestrator handles the rest.

Usage:
    criteria = FetchCriteria(criteria="search-test", source="archive")
    orchestrator = FixtureOrchestrator(criteria, rc)
    report = await orchestrator.execute()
"""
from dataclasses import dataclass, field
from typing import Any

from app.redis import RedisClient
from app.fixtures.utils import calculate_sample_counts
from app.fixtures.fetcher import FixtureDataFetcher
from app.fixtures.targeted_fetcher import TargetedFixtureFetcher
from app.fixtures.search_test_fetcher import SearchTestFixtureFetcher
from app.fixtures.id_source import IDSource, create_id_source
from app.logging import get_logger

logger = get_logger(__name__)


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


class FixtureOrchestrator:
    """Coordinates fixture fetching based on declarative criteria.

    Resolves the ID source, creates the appropriate fetcher for the
    criteria profile, executes the pipeline, and returns a report.
    """

    def __init__(self, criteria: FetchCriteria, rc: RedisClient):
        self.criteria = criteria
        self.rc = rc
        self.id_source: IDSource | None = None
        self.fetcher: FixtureDataFetcher | None = None

    async def execute(self) -> FetchReport:
        """Run the full fetch pipeline."""
        report = FetchReport(criteria=self.criteria.criteria)

        try:
            self.id_source = create_id_source(
                self.criteria.source,
                rc=self.rc if self.criteria.source == Source.AUTO else None,
            )
            has_ids = await self.id_source.resolve()
            if not has_ids:
                logger.warning("No ID sources available, falling back to random guessing")

            self.fetcher = self._create_fetcher()

            if self.criteria.is_search_test:
                report = await self._execute_search_test()
            elif self.criteria.is_targeted:
                report = await self._execute_targeted()
            else:
                report = await self._execute_standard()

        except Exception as e:
            logger.error(f"Fetch orchestrator error: {e}")
            report.errors.append(str(e))

        return report

    def _create_fetcher(self) -> FixtureDataFetcher:
        """Create the appropriate fetcher for the criteria profile."""
        fixtures_dir = None
        if self.criteria.fixtures_dir:
            from pathlib import Path
            fixtures_dir = Path(self.criteria.fixtures_dir)

        if self.criteria.is_search_test:
            fetcher = SearchTestFixtureFetcher(
                self.rc, fixtures_dir=fixtures_dir, exclude_ids=self.criteria.exclude_ids
            )
        elif self.criteria.is_targeted:
            fetcher = TargetedFixtureFetcher(
                self.rc, fixtures_dir=fixtures_dir, exclude_ids=self.criteria.exclude_ids
            )
        else:
            fetcher = FixtureDataFetcher(
                self.rc,
                force_fetch=self.criteria.force_fetch,
                fixtures_dir=fixtures_dir,
                exclude_ids=self.criteria.exclude_ids,
            )

        fetcher.logger = get_logger(__name__)

        if self.id_source:
            fetcher.id_source = self.id_source

        return fetcher

    async def _execute_standard(self) -> FetchReport:
        """Execute standard/minimal fetch: hit counts for each data type."""
        from app.fixtures.fetcher import ProgressBar
        
        sample_counts = self.criteria.resolve_sample_counts()
        progress = ProgressBar(no_progress=self.criteria.no_progress)
        progress.start()
        
        try:
            if self.criteria.concurrent:
                await self._execute_concurrent(sample_counts, progress)
            else:
                async for event in self.fetcher.fetch_all(sample_counts):
                    progress.update(event.category, event.current, event.total)
        finally:
            progress.stop()
        
        results = self.fetcher.last_fetch_results
        return FetchReport(criteria=self.criteria.criteria, results=results)
    
    async def _execute_concurrent(self, sample_counts: dict, progress: "ProgressBar") -> None:
        """Execute fetches concurrently for independent categories."""
        import asyncio
        
        users = sample_counts.get("users", {})
        scores = sample_counts.get("scores", {})
        
        beatmaps_count = sample_counts.get("beatmaps", 0)
        beatmapsets_count = sample_counts.get("beatmapsets", 0)
        users_osu = users.get("osu", 0)
        users_taiko = users.get("taiko", 0)
        users_fruits = users.get("fruits", 0)
        users_mania = users.get("mania", 0)
        scores_best = scores.get("best", 0)
        scores_firsts = scores.get("firsts", 0)
        scores_recent = scores.get("recent", 0)
        beatmap_scores_count = sample_counts.get("beatmap_scores", 0)
        beatmap_attributes_count = sample_counts.get("beatmap_attributes", 0)
        
        semaphore = asyncio.Semaphore(self.criteria.concurrency)
        
        async def limited_fetch(coroutine):
            async with semaphore:
                async for event in coroutine:
                    progress.update(event.category, event.current, event.total)
        
        tasks = []
        
        if beatmaps_count > 0:
            tasks.append(limited_fetch(self.fetcher.fetch_beatmaps(beatmaps_count)))
        if beatmapsets_count > 0:
            tasks.append(limited_fetch(self.fetcher.fetch_beatmapsets(beatmapsets_count)))
        if users_osu > 0 or users_taiko > 0 or users_fruits > 0 or users_mania > 0:
            tasks.append(limited_fetch(
                self.fetcher.fetch_users(users_osu, users_taiko, users_fruits, users_mania)
            ))
        
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
        
        if scores_best > 0 or scores_firsts > 0 or scores_recent > 0:
            async for event in self.fetcher.fetch_scores(scores_best, scores_firsts, scores_recent):
                progress.update(event.category, event.current, event.total)
        
        if beatmap_scores_count > 0:
            async for event in self.fetcher.fetch_beatmap_scores(beatmap_scores_count):
                progress.update(event.category, event.current, event.total)
        
        if beatmap_attributes_count > 0:
            async for event in self.fetcher.fetch_beatmap_attributes(beatmap_attributes_count):
                progress.update(event.category, event.current, event.total)

    async def _execute_targeted(self) -> FetchReport:
        """Execute targeted fetch: criterion-based coverage."""
        targeted = self.criteria.targeted
        if not targeted.rulesets:
            targeted.rulesets = ["osu"]

        if isinstance(self.fetcher, TargetedFixtureFetcher):
            self.fetcher.set_targeted_fetch(
                statuses=targeted.statuses,
                difficulty_range=targeted.difficulty_range,
                playcount_range=targeted.playcount_range,
                activity_tier=targeted.activity_tier,
                rulesets=targeted.rulesets,
            )

        async for _ in self.fetcher.fetch_targeted():
            pass

        results = self.fetcher.get_last_results()
        return FetchReport(criteria=self.criteria.criteria, results=results)

    async def _execute_search_test(self) -> FetchReport:
        """Execute search-test fetch: coverage-gated rounds."""
        from app.manage.fixtures.fetch import _print_coverage_gaps

        st = self.criteria.search_test
        if st.quick:
            st.min_per_category = 1
            st.max_total = 20

        if st.gaps:
            _print_coverage_gaps(self.fetcher)
            return FetchReport(criteria=self.criteria.criteria)

        if st.full:
            self.fetcher.logger.info(
                f"Search test fetch: full mode, max {st.max_total} API calls"
            )
            coverage = await self.fetcher.ensure_search_test_coverage(
                min_per_category=st.min_per_category,
                max_total=st.max_total,
                skip_covered=False,
            )
        else:
            _print_coverage_gaps(self.fetcher)
            self.fetcher.logger.info(
                f"Starting search test fetch: max {st.max_total} API calls, "
                f"min {st.min_per_category} per category (skip covered)"
            )
            coverage = await self.fetcher.ensure_search_test_coverage(
                min_per_category=st.min_per_category,
                max_total=st.max_total,
                skip_covered=True,
            )

        return FetchReport(criteria=self.criteria.criteria, coverage=coverage)
