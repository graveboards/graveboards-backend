from rich.console import Console
from rich.table import Table

from app.fixtures.utils import RULESETS, SCORE_TYPES, calculate_sample_counts
from app.fixtures.fetcher import FixtureDataFetcher
from app.redis import RedisClient
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


def _create_empty_samples() -> dict:
    return {
        "beatmaps": {"count": 0, "last_fetched": None},
        "beatmapsets": {"count": 0, "last_fetched": None},
        "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_fetched": None},
        "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_fetched": None},
        "beatmap_scores": {"count": 0, "last_fetched": None},
        "beatmap_attributes": {"count": 0, "last_fetched": None},
    }


def _create_empty_promoted_fixtures() -> dict:
    return {
        "beatmaps": {"count": 0, "last_promoted": None},
        "beatmapsets": {"count": 0, "last_promoted": None},
        "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_promoted": None},
        "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_promoted": None},
        "beatmap_scores": {"count": 0, "last_promoted": None},
        "beatmap_attributes": {"count": 0, "last_promoted": None},
    }


def _add_counts_to_table(counts: dict, table: Table) -> None:
    for category, count in counts.items():
        if isinstance(count, dict):
            for subcat, subcount in count.items():
                table.add_row(f"{category}.{subcat}", str(subcount))
        else:
            table.add_row(category, str(count))


async def cmd_fetch_fixtures(
    scale: float,
    beatmaps: int | None,
    beatmapsets: int | None,
    users_osu: int | None,
    users_taiko: int | None,
    users_fruits: int | None,
    users_mania: int | None,
    scores_best: int | None,
    scores_firsts: int | None,
    scores_recent: int | None,
    beatmap_scores: int | None,
    beatmap_attributes: int | None,
    use_minimal: bool,
    beatmaps_range_min: int | None,
    beatmaps_range_max: int | None,
    beatmapsets_range_min: int | None,
    beatmapsets_range_max: int | None,
    users_range_min: int | None,
    users_range_max: int | None,
):
    rc = RedisClient()
    id_ranges = {}
    if beatmaps_range_min or beatmaps_range_max:
        id_ranges["beatmaps"] = {
            "min": beatmaps_range_min or 1,
            "max": beatmaps_range_max or 1000000,
        }
    if beatmapsets_range_min or beatmapsets_range_max:
        id_ranges["beatmapsets"] = {
            "min": beatmapsets_range_min or 1,
            "max": beatmapsets_range_max or 100000,
        }
    if users_range_min or users_range_max:
        id_ranges["users"] = {
            "min": users_range_min or 1,
            "max": users_range_max or 10000000,
        }
    fetcher = FixtureDataFetcher(rc, id_ranges=id_ranges if id_ranges else None)
    fetcher.logger = logger

    sample_counts = calculate_sample_counts(
        scale=scale,
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
        use_minimal=use_minimal,
    )

    console.print("\n[bold blue]Fetching fixture data from osu! API...[/bold blue]")
    console.print(f"\n[bold]Sample counts:[/bold]")
    sample_table = Table(show_header=False)
    sample_table.add_column("Category")
    sample_table.add_column("Count")

    _add_counts_to_table(sample_counts, sample_table)
    console.print(sample_table)

    results = await fetcher.fetch_all(sample_counts)

    console.print("\n[bold green]Fixture data fetch complete![/bold green]")
    console.print("\n[bold]Results:[/bold]")
    result_table = Table(show_header=False)
    result_table.add_column("Category")
    result_table.add_column("Count")

    _add_counts_to_table(results, result_table)
    console.print(result_table)
    console.print()
