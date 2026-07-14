"""CLI command to fetch fixture data from the osu! API.

Uses the FixtureOrchestrator with composable criteria:
  --criteria {minimal, standard, targeted, search-test}
  --source {auto, archive, top-players}

Usage:
    manage fixtures fetch --criteria minimal
    manage fixtures fetch --criteria standard --beatmaps 50 --users-osu 20
    manage fixtures fetch --criteria targeted --status ranked --difficulty easy
    manage fixtures fetch --criteria search-test
    manage fixtures fetch --criteria search-test --archive --quick
"""
from rich.console import Console
from rich.table import Table

from app.redis import RedisClient
from app.logging import get_logger
from app.fixtures.search_test_fetcher import SearchTestFixtureFetcher
from app.fixtures.orchestrator import (
    Criteria,
    FetchCriteria,
    FetchReport,
    FixtureOrchestrator,
    Source,
    SearchTestOverrides,
    TargetedOverrides,
)

console = Console()
logger = get_logger(__name__)


async def cmd_fetch_fixtures(
    criteria: str = Criteria.STANDARD,
    source: str = Source.AUTO,
    beatmaps: int | None = None,
    beatmapsets: int | None = None,
    users_osu: int | None = None,
    users_taiko: int | None = None,
    users_fruits: int | None = None,
    users_mania: int | None = None,
    scores_best: int | None = None,
    scores_firsts: int | None = None,
    scores_recent: int | None = None,
    beatmap_scores: int | None = None,
    beatmap_attributes: int | None = None,
    status: list[str] | None = None,
    difficulty_range: str | None = None,
    playcount_range: str | None = None,
    activity_tier: str | None = None,
    rulesets: list[str] | None = None,
    force_fetch: bool = False,
    no_progress: bool = False,
    verbose: bool = False,
    min_per_category: int = 1,
    max_total: int = 500,
    gaps: bool = False,
    full: bool = False,
    quick: bool = False,
    fixtures_dir: str | None = None,
    dry_run: bool = False,
    concurrent: bool = False,
    concurrency: int = 3,
    exclude_ids: str | None = None,
):
    """Fetch fixture data using the orchestrator with composable criteria."""
    rc = RedisClient()
    try:
        fetch_criteria = _build_criteria(
            criteria=criteria,
            source=source,
            beatmaps=beatmaps,
            beatmapsets=beatmapsets,
            users_osu=users_osu,
            users_taiko=users_taiko,
            users_fruits=users_fruits,
            users_mania=users_mania,
            scores_best=scores_best,
            scores_firsts=scores_firsts,
            scores_recent=scores_recent,
            beatmap_scores=beatmap_scores,
            beatmap_attributes=beatmap_attributes,
            status=status,
            difficulty_range=difficulty_range,
            playcount_range=playcount_range,
            activity_tier=activity_tier,
            rulesets=rulesets,
            force_fetch=force_fetch,
            no_progress=no_progress,
            verbose=verbose,
            min_per_category=min_per_category,
            max_total=max_total,
            gaps=gaps,
            full=full,
            quick=quick,
            fixtures_dir=fixtures_dir,
            dry_run=dry_run,
            concurrent=concurrent,
            concurrency=concurrency,
            exclude_ids=exclude_ids,
        )

        orchestrator = FixtureOrchestrator(fetch_criteria, rc)
        
        if dry_run:
            _print_dry_run(fetch_criteria)
            return
        
        report = await orchestrator.execute()
        _print_report(report)
    finally:
        await rc.aclose()


def _build_criteria(
    criteria: str,
    source: str,
    force_fetch: bool = False,
    no_progress: bool = False,
    verbose: bool = False,
    beatmaps: int | None = None,
    beatmapsets: int | None = None,
    users_osu: int | None = None,
    users_taiko: int | None = None,
    users_fruits: int | None = None,
    users_mania: int | None = None,
    scores_best: int | None = None,
    scores_firsts: int | None = None,
    scores_recent: int | None = None,
    beatmap_scores: int | None = None,
    beatmap_attributes: int | None = None,
    status: list[str] | None = None,
    difficulty_range: str | None = None,
    playcount_range: str | None = None,
    activity_tier: str | None = None,
    rulesets: list[str] | None = None,
    min_per_category: int = 1,
    max_total: int = 500,
    gaps: bool = False,
    full: bool = False,
    quick: bool = False,
    fixtures_dir: str | None = None,
    dry_run: bool = False,
    concurrent: bool = False,
    concurrency: int = 3,
    exclude_ids: str | None = None,
) -> FetchCriteria:
    """Build FetchCriteria from CLI arguments."""
    # Build targeted overrides
    targeted_overrides = None
    if criteria == Criteria.TARGETED:
        targeted_overrides = TargetedOverrides(
            statuses=status,
            difficulty_range=difficulty_range,
            playcount_range=playcount_range,
            activity_tier=activity_tier,
            rulesets=rulesets,
        )

    # Build search-test overrides
    search_test_overrides = None
    if criteria == Criteria.SEARCH_TEST:
        search_test_overrides = SearchTestOverrides(
            quick=quick,
            min_per_category=min_per_category,
            max_total=max_total,
            gaps=gaps,
            full=full,
        )

    exclude_ids_list = []
    if exclude_ids:
        exclude_ids_list = [int(x.strip()) for x in exclude_ids.split(",") if x.strip().isdigit()]

    return FetchCriteria(
        criteria=criteria,
        source=source,
        targeted=targeted_overrides,
        search_test=search_test_overrides,
        beatmaps=beatmaps or 0,
        beatmapsets=beatmapsets or 0,
        users={
            "osu": users_osu or 0,
            "taiko": users_taiko or 0,
            "fruits": users_fruits or 0,
            "mania": users_mania or 0,
        },
        scores={
            "best": scores_best or 0,
            "firsts": scores_firsts or 0,
            "recent": scores_recent or 0,
        },
        beatmap_scores=beatmap_scores or 0,
        beatmap_attributes=beatmap_attributes or 0,
        force_fetch=force_fetch,
        no_progress=no_progress,
        verbose=verbose,
        fixtures_dir=fixtures_dir,
        dry_run=dry_run,
        concurrent=concurrent,
        concurrency=concurrency,
        exclude_ids=exclude_ids_list,
    )


def _print_dry_run(criteria: FetchCriteria) -> None:
    """Print what would be fetched without making any API calls."""
    console.print("[bold]Dry Run — What would be fetched:[/bold]\n")
    console.print(f"  Criteria: {criteria.criteria}")
    console.print(f"  Source: {criteria.source}")
    
    if criteria.is_standard or criteria.is_minimal:
        console.print(f"  Would fetch:")
        if criteria.beatmaps:
            console.print(f"    - {criteria.beatmaps} beatmaps (via random IDs)")
        if criteria.beatmapsets:
            console.print(f"    - {criteria.beatmapsets} beatmapsets (via random IDs)")
        users = criteria.users
        if users.get("osu"):
            console.print(f"    - {users['osu']} osu users")
        if users.get("taiko"):
            console.print(f"    - {users['taiko']} taiko users")
        if users.get("fruits"):
            console.print(f"    - {users['fruits']} fruits users")
        if users.get("mania"):
            console.print(f"    - {users['mania']} mania users")
        scores = criteria.scores
        if scores.get("best"):
            console.print(f"    - {scores['best']} best scores")
        if scores.get("firsts"):
            console.print(f"    - {scores['firsts']} firsts scores")
        if scores.get("recent"):
            console.print(f"    - {scores['recent']} recent scores")
        if criteria.beatmap_scores:
            console.print(f"    - {criteria.beatmap_scores} beatmap scores")
        if criteria.beatmap_attributes:
            console.print(f"    - {criteria.beatmap_attributes} beatmap attributes")
        
        total = (
            (criteria.beatmaps or 0) +
            (criteria.beatmapsets or 0) +
            sum(criteria.users.values()) +
            sum(criteria.scores.values()) +
            (criteria.beatmap_scores or 0) +
            (criteria.beatmap_attributes or 0)
        )
        console.print(f"\n  Estimated API calls: ~{total}")
    
    elif criteria.is_targeted:
        console.print("  Would fetch targeted fixtures based on:")
        if criteria.targeted.statuses:
            console.print(f"    - Statuses: {', '.join(criteria.targeted.statuses)}")
        if criteria.targeted.difficulty_range:
            console.print(f"    - Difficulty: {criteria.targeted.difficulty_range}")
        if criteria.targeted.playcount_range:
            console.print(f"    - Playcount: {criteria.targeted.playcount_range}")
        if criteria.targeted.activity_tier:
            console.print(f"    - Activity: {criteria.targeted.activity_tier}")
        if criteria.targeted.rulesets:
            console.print(f"    - Rulesets: {', '.join(criteria.targeted.rulesets)}")
    
    elif criteria.is_search_test:
        st = criteria.search_test
        console.print(f"  Would fetch search-test coverage:")
        console.print(f"    - Max total API calls: {st.max_total}")
        console.print(f"    - Min per category: {st.min_per_category}")
        if st.full:
            console.print(f"    - Mode: full (skip_covered=False)")
        else:
            console.print(f"    - Mode: incremental (skip_covered=True)")


def _print_report(report: FetchReport) -> None:
    """Print fetch results to the console."""
    if report.errors:
        for error in report.errors:
            console.print(f"[red]Error:[/red] {error}")

    if report.criteria == Criteria.SEARCH_TEST and report.coverage:
        _print_coverage_report(report.coverage)
        return

    if not report.results:
        return

    console.print("\n[bold]Results:[/bold]")
    result_table = Table(show_header=False)
    result_table.add_column("Category")
    result_table.add_column("Count")

    for category, count in report.results.items():
        if isinstance(count, dict):
            for subcat, subcount in count.items():
                result_table.add_row(f"{category}.{subcat}", str(subcount))
        else:
            result_table.add_row(category, str(count))

    console.print(result_table)
    console.print()


def _print_coverage_gaps(fetcher) -> None:
    """Print coverage gaps from metadata.json (delegated to display module)."""
    from app.fixtures.display import print_coverage_gaps
    print_coverage_gaps(fetcher)


def _print_coverage_report(coverage: dict) -> None:
    """Print the full coverage report as a table (delegated to display module)."""
    from app.fixtures.display import print_coverage_report
    print_coverage_report(coverage)
