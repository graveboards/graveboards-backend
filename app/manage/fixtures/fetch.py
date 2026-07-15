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
from app.fixtures.criteria import Criteria, FetchCriteria, FetchReport, Source
from app.fixtures.criteria import SearchTestOverrides, TargetedOverrides
from app.fixtures.orchestrator import FixtureOrchestrator
from .config import FetchConfig

console = Console()
logger = get_logger(__name__)


async def cmd_fetch_fixtures(config: FetchConfig):
    """Fetch fixture data using the orchestrator with composable criteria."""
    rc = RedisClient()
    try:
        fetch_criteria = config.to_fetch_criteria()

        orchestrator = FixtureOrchestrator(fetch_criteria, rc)

        if config.dry_run:
            _print_dry_run(fetch_criteria)
            return

        report = await orchestrator.execute()
        _print_report(report)
    finally:
        await rc.aclose()


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
            (criteria.beatmaps or 0)
            + (criteria.beatmapsets or 0)
            + sum(criteria.users.values())
            + sum(criteria.scores.values())
            + (criteria.beatmap_scores or 0)
            + (criteria.beatmap_attributes or 0)
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
