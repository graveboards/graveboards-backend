from rich.console import Console
from rich.table import Table
from rich.live import Live
from rich.panel import Panel
from rich.progress import (
    Progress,
    BarColumn,
    TextColumn,
    TimeRemainingColumn,
    TaskID,
    TimeElapsedColumn
)

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


def _create_progress_tasks(progress, sample_counts: dict) -> tuple[dict[str, TaskID], int]:
    tasks: dict[str, TaskID] = {}
    total_items = 0

    if sample_counts.get("beatmaps", 0) > 0:
        tasks["beatmaps"] = progress.add_task("Beatmaps", total=sample_counts["beatmaps"])
        total_items += sample_counts["beatmaps"]

    if sample_counts.get("beatmapsets", 0) > 0:
        tasks["beatmapsets"] = progress.add_task("Beatmapsets", total=sample_counts["beatmapsets"])
        total_items += sample_counts["beatmapsets"]

    users = sample_counts.get("users", {})
    user_total = sum(users.values())
    if user_total > 0:
        tasks["users"] = progress.add_task("Users", total=user_total)
        total_items += user_total

    scores = sample_counts.get("scores", {})
    scores_total = sum(scores.values())
    if scores_total > 0:
        tasks["scores"] = progress.add_task("Scores", total=scores_total)
        total_items += scores_total

    if sample_counts.get("beatmap_scores", 0) > 0:
        tasks["beatmap_scores"] = progress.add_task("Beatmap Scores", total=sample_counts["beatmap_scores"])
        total_items += sample_counts["beatmap_scores"]

    if sample_counts.get("beatmap_attributes", 0) > 0:
        tasks["beatmap_attributes"] = progress.add_task("Beatmap Attributes", total=sample_counts["beatmap_attributes"])
        total_items += sample_counts["beatmap_attributes"]

    return tasks, total_items


def _process_fetch_events(fetcher, progress, tasks, overall_task, overall_progress, sample_counts, use_live: bool):
    if use_live:
        progress_table = Table.grid()
        panel = Panel.fit(
            progress,
            title="Fetching Fixtures",
            border_style="green",
            padding=(1, 3)
        )
        progress_table.add_row(panel)

        with Live(progress_table, refresh_per_second=20):
            async for event in fetcher.fetch_all(sample_counts):
                category = event.category
                if category in tasks:
                    progress.update(tasks[category], completed=event.current)
                else:
                    for task_category in tasks.keys():
                        if task_category in category:
                            progress.update(tasks[task_category], completed=event.current)
                            break
                overall_progress += 1
                progress.update(overall_task, completed=overall_progress)

            panel.title = "Fetching Completed"
            panel.border_style = "dim green"
    else:
        async for event in fetcher.fetch_all(sample_counts):
            category = event.category
            if category in tasks:
                progress.update(tasks[category], completed=event.current)
            else:
                for task_category in tasks.keys():
                    if task_category in category:
                        progress.update(tasks[task_category], completed=event.current)
                        break
            overall_progress += 1
            progress.update(overall_task, completed=overall_progress)

        progress.stop()


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
    no_progress: bool,
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

    progress = Progress(
        TextColumn("[bold blue]{task.description}"),
        TextColumn("[white]({task.completed}/{task.total})"),
        BarColumn(pulse_style="dim"),
        "[progress.percentage]{task.percentage:>3.0f}%",
        TimeRemainingColumn(compact=True),
        TimeElapsedColumn()
    )

    tasks, total_items = _create_progress_tasks(progress, sample_counts)
    overall_task = progress.add_task("Total", total=total_items)
    overall_progress = 0

    logger.info("Fetching fixture data from osu! API...")

    _process_fetch_events(fetcher, progress, tasks, overall_task, overall_progress, sample_counts, use_live=not no_progress)

    results = fetcher.last_fetch_results
    logger.info(f"Fixture data fetch complete: {results}")

    console.print("\n[bold]Results:[/bold]")
    result_table = Table(show_header=False)
    result_table.add_column("Category")
    result_table.add_column("Count")

    _add_counts_to_table(results, result_table)
    console.print(result_table)
    console.print()