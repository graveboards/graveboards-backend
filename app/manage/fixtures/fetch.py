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
    minimal: bool = False,
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
    targeted: bool = False,
    status: list[str] | None = None,
    difficulty_range: str | None = None,
    playcount_range: str | None = None,
    activity_tier: str | None = None,
    rulesets: list[str] | None = None,
    search_test: bool = False,
    archive: bool = False,
    top_players: bool = False,
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
            minimal=minimal,
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
            targeted=targeted,
            status=status,
            difficulty_range=difficulty_range,
            playcount_range=playcount_range,
            activity_tier=activity_tier,
            rulesets=rulesets,
            search_test=search_test,
            archive=archive,
            top_players=top_players,
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
    minimal: bool = False,
    targeted: bool = False,
    search_test: bool = False,
    archive: bool = False,
    top_players: bool = False,
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
    # Resolve criteria from explicit --criteria or legacy flags
    resolved_criteria = criteria
    if minimal:
        resolved_criteria = Criteria.MINIMAL
    elif search_test:
        resolved_criteria = Criteria.SEARCH_TEST
    elif targeted:
        resolved_criteria = Criteria.TARGETED

    # Resolve source from explicit --source or legacy flags
    src = source
    if archive:
        src = Source.ARCHIVE
    elif top_players:
        src = Source.TOP_PLAYERS

    # Build targeted overrides
    targeted_overrides = None
    if resolved_criteria == Criteria.TARGETED:
        targeted_overrides = TargetedOverrides(
            statuses=status,
            difficulty_range=difficulty_range,
            playcount_range=playcount_range,
            activity_tier=activity_tier,
            rulesets=rulesets,
        )

    # Build search-test overrides
    search_test_overrides = None
    if resolved_criteria == Criteria.SEARCH_TEST:
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
        criteria=resolved_criteria,
        source=src,
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
            criteria.beatmaps or 0 +
            criteria.beatmapsets or 0 +
            sum(criteria.users.values()) +
            sum(criteria.scores.values()) +
            criteria.beatmap_scores or 0 +
            criteria.beatmap_attributes or 0
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


def _print_coverage_gaps(fetcher: "SearchTestFixtureFetcher") -> None:
    """Print coverage gaps from metadata.json."""
    console.print("[bold]Coverage status from metadata.json:[/bold]")

    search_cov = fetcher.metadata.get("search_test_coverage", {})
    if not search_cov:
        console.print("  [yellow]No previous coverage data found.[/yellow]")
        console.print("  Will fetch all buckets from scratch.")
        return

    last_updated = search_cov.get("last_updated", "unknown")
    console.print(f"  Last updated: {last_updated}")
    console.print()

    gap_items = []
    full_items = []

    genres = search_cov.get("beatmapset_genres", [])
    if genres:
        sample = ', '.join(str(g) for g in genres[:5])
        full_items.append(f"genres ({len(genres)} total)")
        if len(genres) > 5:
            full_items.append(f"    samples: {sample}, ...")
        else:
            full_items.append(f"    values: {sample}")
    else:
        gap_items.append("beatmapset_genres")

    langs = search_cov.get("beatmapset_languages", [])
    if langs:
        sample = ', '.join(str(l) for l in langs[:5])
        full_items.append(f"languages ({len(langs)} total)")
        if len(langs) > 5:
            full_items.append(f"    samples: {sample}, ...")
        else:
            full_items.append(f"    values: {sample}")
    else:
        gap_items.append("beatmapset_languages")

    nsfw_true = search_cov.get("beatmapset_nsfw_true_ids", [])
    nsfw_false = search_cov.get("beatmapset_nsfw_false_ids", [])
    if nsfw_true and nsfw_false:
        full_items.append(f"nsfw (true: {len(nsfw_true)}, false: {len(nsfw_false)})")
    else:
        if not nsfw_true:
            gap_items.append("nsfw=true")
        if not nsfw_false:
            gap_items.append("nsfw=false")

    modes = search_cov.get("beatmap_modes", [])
    if modes:
        full_items.append(f"beatmap_modes ({len(modes)} total)")
        full_items.append(f"    values: {', '.join(str(m) for m in modes)}")
    else:
        gap_items.append("beatmap_modes")

    countries = search_cov.get("country_codes", [])
    if countries:
        full_items.append(f"countries ({len(countries)} total)")
        if len(countries) > 5:
            full_items.append(f"    samples: {', '.join(countries[:5])}, ...")
        else:
            full_items.append(f"    values: {', '.join(countries)}")
    else:
        gap_items.append("country_codes")

    restr = search_cov.get("restricted_users", {})
    restr_true = restr.get("true_ids", [])
    restr_false = restr.get("false_ids", [])
    if restr_true and restr_false:
        full_items.append(f"restricted (true: {len(restr_true)}, false: {len(restr_false)})")
    else:
        if not restr_true:
            gap_items.append("restricted=true")
        if not restr_false:
            gap_items.append("restricted=false")

    statuses = search_cov.get("beatmapset_statuses", [])
    if statuses:
        full_items.append(f"statuses ({len(statuses)} total)")
        if len(statuses) > 5:
            full_items.append(f"    samples: {', '.join(statuses[:5])}, ...")
        else:
            full_items.append(f"    values: {', '.join(statuses)}")
    else:
        gap_items.append("beatmapset_statuses")

    if full_items:
        console.print("  [green]Covered:[/green]")
        for item in full_items:
            console.print(f"    {item}")

    if gap_items:
        console.print("  [yellow]Gaps:[/yellow]")
        for item in gap_items:
            console.print(f"    - {item}")

    if not gap_items:
        console.print("\n  [green]All major buckets covered![/green]")


def _print_coverage_report(coverage: dict) -> None:
    """Print the full coverage report as a table."""
    console.print("\n[bold]Search test fixture coverage:[/bold]")

    table = Table(show_header=True, header_style="bold")
    table.add_column("Category")
    table.add_column("Status")
    table.add_column("Details")

    _add_row(table, "Beatmapset Genres", "OK" if coverage.get("beatmapset_genres") else "MISSING",
             str(len(coverage.get("beatmapset_genres", {}))))
    _add_row(table, "Beatmapset Languages", "OK" if coverage.get("beatmapset_languages") else "MISSING",
             str(len(coverage.get("beatmapset_languages", {}))))
    nsfw = coverage.get("beatmapset_nsfw", {})
    _add_row(table, "Beatmapset NSFW", "OK" if nsfw.get("true", {}).get("count", 0) > 0 and nsfw.get("false", {}).get("count", 0) > 0 else "PARTIAL",
             f"true:{nsfw.get('true', {}).get('count', 0)}, false:{nsfw.get('false', {}).get('count', 0)}")
    _add_row(table, "Beatmapset Statuses", "OK" if coverage.get("beatmapset_statuses") else "MISSING",
             str(len(coverage.get("beatmapset_statuses", []))))
    _add_row(table, "Beatmapset Ratings", "OK" if any(coverage.get("beatmapset_ratings", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmapset_ratings', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmapset Favourites", "OK" if any(coverage.get("beatmapset_favourite_counts", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmapset_favourite_counts', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmapset Play Counts", "OK" if any(coverage.get("beatmapset_play_counts", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmapset_play_counts', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmapset Has Description", "OK" if coverage.get("beatmapset_has_description") else "MISSING", "")
    _add_row(table, "Beatmapset Has Pack Tags", "OK" if coverage.get("beatmapset_has_pack_tags") else "MISSING", "")
    _add_row(table, "Beatmapset Video", "OK" if coverage.get("beatmapset_videos") else "MISSING", "")
    _add_row(table, "Beatmapset Storyboard", "OK" if coverage.get("beatmapset_storyboards") else "MISSING", "")
    _add_row(table, "Beatmapset Hype", "OK" if coverage.get("beatmapset_hype") else "MISSING", "")
    _add_row(table, "Beatmapset Nominations", "OK" if coverage.get("beatmapset_nominations") else "MISSING", "")
    _add_row(table, "Beatmapset SR Gaps", "OK" if coverage.get("beatmapset_sr_gaps") else "MISSING", "")
    _add_row(table, "Beatmapset Hit Lengths", "OK" if coverage.get("beatmapset_hit_lengths") else "MISSING", "")

    bm_modes = coverage.get("beatmap_modes", {})
    _add_row(table, "Beatmap Modes", "OK" if bm_modes else "MISSING",
             str(len(bm_modes)))
    bm_diffs = coverage.get("beatmap_difficulties", {})
    _add_row(table, "Beatmap Difficulties", "OK" if any(bm_diffs.get(c, {}).get("count", 0) > 0 for c in ("easy", "medium", "hard", "expert")) else "MISSING",
             ", ".join(f"{c}:{bm_diffs.get(c, {}).get('count', 0)}" for c in ("easy", "medium", "hard", "expert")))
    bm_pc = coverage.get("beatmap_playcounts", {})
    _add_row(table, "Beatmap Playcounts", "OK" if any(bm_pc.get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{bm_pc.get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap BPM", "OK" if any(coverage.get("beatmap_bpm", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_bpm', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap Accuracy", "OK" if any(coverage.get("beatmap_accuracy", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_accuracy', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap Versions", "OK" if coverage.get("beatmap_versions") else "MISSING",
             str(len(coverage.get("beatmap_versions", []))))
    _add_row(table, "Beatmap Max Combos", "OK" if any(coverage.get("beatmap_max_combos", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_max_combos', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap Drain", "OK" if any(coverage.get("beatmap_drain", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_drain', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap AR", "OK" if any(coverage.get("beatmap_ar", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_ar', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))
    _add_row(table, "Beatmap CS", "OK" if any(coverage.get("beatmap_cs", {}).get(c, {}).get("count", 0) > 0 for c in ("low", "medium", "high")) else "MISSING",
             ", ".join(f"{c}:{coverage.get('beatmap_cs', {}).get(c, {}).get('count', 0)}" for c in ("low", "medium", "high")))

    cc = coverage.get("country_codes", {})
    _add_row(table, "Country Codes", "OK" if cc else "MISSING", str(len(cc)))
    restr = coverage.get("restricted_users", {})
    _add_row(table, "Restricted Users", "OK" if restr.get("true", {}).get("count", 0) > 0 and restr.get("false", {}).get("count", 0) > 0 else "PARTIAL",
             f"true:{restr.get('true', {}).get('count', 0)}, false:{restr.get('false', {}).get('count', 0)}")


def _add_row(table, category: str, status: str, details: str) -> None:
    if status == "OK":
        style = "green"
    elif status == "PARTIAL":
        style = "yellow"
    else:
        style = "red"
    table.add_row(f"[{style}]{category}[/{style}]", f"[{style}]{status}[/{style}]", details)
