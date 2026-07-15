"""Unified fixture fetch orchestrator.

Composes ID sources, coverage strategies, and the fetch pipeline into a
single declarative interface. The CLI passes a FetchCriteria and the
orchestrator handles the rest.

Usage:
    criteria = FetchCriteria(criteria="search-test", source="archive")
    orchestrator = FixtureOrchestrator(criteria, rc)
    report = await orchestrator.execute()
"""
from app.redis import RedisClient
from app.fixtures.criteria import FetchCriteria, FetchReport, Criteria, Source, TargetedOverrides, SearchTestOverrides
from app.fixtures.fetcher import FixtureDataFetcher
from app.fixtures.targeted_fetcher import TargetedFixtureFetcher
from app.fixtures.search_test_fetcher import SearchTestFixtureFetcher
from app.fixtures.id_source import IDSource, create_id_source
from app.fixtures.failed_id_store import FailedIdStore
from app.logging import get_logger

logger = get_logger(__name__)


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
        self.failed_id_store = FailedIdStore(self.rc)

        try:
            self.id_source = create_id_source(
                self.criteria.source,
                rc=self.rc if self.criteria.source == Source.AUTO else None,
                failed_id_store=self.failed_id_store,
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
                self.rc, fixtures_dir=fixtures_dir, exclude_ids=self.criteria.exclude_ids,
                failed_id_store=self.failed_id_store,
            )
        elif self.criteria.is_targeted:
            fetcher = TargetedFixtureFetcher(
                self.rc, fixtures_dir=fixtures_dir, exclude_ids=self.criteria.exclude_ids,
                failed_id_store=self.failed_id_store,
            )
        else:
            fetcher = FixtureDataFetcher(
                self.rc,
                force_fetch=self.criteria.force_fetch,
                fixtures_dir=fixtures_dir,
                exclude_ids=self.criteria.exclude_ids,
                failed_id_store=self.failed_id_store,
            )

        fetcher.logger = get_logger(__name__)

        if self.id_source:
            fetcher.id_source = self.id_source

        return fetcher

    async def _execute_standard(self) -> FetchReport:
        """Execute standard/minimal fetch: hit counts for each data type."""
        from app.fixtures.progress import ProgressBar
        
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
        """Execute search-test fetch: coverage-gated rounds.

        Modes:
            --gaps       Show coverage gaps and exit (no fetching)
            --full       Re-fetch all buckets from scratch (skip_covered=False)
            default      Incremental: skip already-covered buckets (skip_covered=True)
            --quick      Same as default but with min_per_category=1, max_total=20

        The adaptive fetch loop prioritizes rare buckets (NSFW, restricted users)
        over common ones, and actions that fill multiple buckets at once.
        """
        from app.fixtures.display import print_coverage_gaps

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

    async def fetch_users_by_ids(
        self,
        user_ids: list[int],
        ruleset: str = "osu",
    ) -> FetchReport:
        """Fetch specific users by their IDs (e.g., beatmapset owners)."""
        from app.fixtures.progress import ProgressBar
        
        report = FetchReport(criteria="users-by-ids")
        self.failed_id_store = FailedIdStore(self.rc)
        
        try:
            self.id_source = create_id_source(
                self.criteria.source,
                rc=self.rc if self.criteria.source == Source.AUTO else None,
                failed_id_store=self.failed_id_store,
            )
            await self.id_source.resolve()
            
            self.fetcher = FixtureDataFetcher(
                self.rc,
                force_fetch=self.criteria.force_fetch,
                fixtures_dir=self.criteria.fixtures_dir,
                exclude_ids=self.criteria.exclude_ids,
                failed_id_store=self.failed_id_store,
            )
            self.fetcher.logger = get_logger(__name__)
            
            if self.id_source:
                self.fetcher.id_source = self.id_source
            
            progress = ProgressBar(no_progress=self.criteria.no_progress)
            progress.start()
            
            try:
                async for event in self.fetcher.fetch_users_by_ids(user_ids, ruleset):
                    progress.update(event.category, event.current, event.total)
            finally:
                progress.stop()
            
            results = self.fetcher.last_fetch_results
            results["failed_user_ids"] = self.fetcher._failed_user_ids
            return FetchReport(criteria=report.criteria, results=results)
        except Exception as e:
            logger.error(f"Fetch users by IDs error: {e}")
            report.errors.append(str(e))
            return report
