import json
from pathlib import Path

from rich.console import Console
from rich.table import Table

from app.logging import get_logger
from app.fixtures.utils import (
    FIXTURES_DIR,
    load_metadata,
    save_metadata,
    get_all_fixture_files,
    wipe_all_fixtures,
    RULESETS,
    SCORE_TYPES,
    calculate_sample_counts,
)
from app.fixtures.fetcher import FixtureDataFetcher
from app.redis import RedisClient

console = Console()
logger = get_logger(__name__)


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

    def add_counts_to_table(counts: dict, table: Table) -> None:
        for category, count in counts.items():
            if isinstance(count, dict):
                for subcat, subcount in count.items():
                    table.add_row(f"{category}.{subcat}", str(subcount))
            else:
                table.add_row(category, str(count))

    console.print("\n[bold blue]Fetching fixture data from osu! API...[/bold blue]")
    console.print(f"\n[bold]Sample counts:[/bold]")
    table = Table(show_header=False)
    table.add_column("Category")
    table.add_column("Count")
    
    add_counts_to_table(sample_counts, table)
    console.print(table)

    results = await fetcher.fetch_all(sample_counts)

    console.print("\n[bold green]Fixture data fetch complete![/bold green]")
    console.print("\n[bold]Results:[/bold]")
    result_table = Table(show_header=False)
    result_table.add_column("Category")
    result_table.add_column("Count")
    
    add_counts_to_table(results, result_table)
    console.print(result_table)
    console.print()


async def cmd_list_fixtures():
    metadata = load_metadata()

    console.print("\n[bold]=== Fixture Data Status ===[/bold]\n")
    console.print(f"Last updated: {metadata.get('last_updated', 'Never')}")
    console.print(f"Source: {metadata.get('source', 'N/A')}")

    console.print("\n[bold]Sample Counts[/bold]")
    samples = metadata.get("samples", {})

    console.print(f"\nBeatmaps: {samples.get('beatmaps', {}).get('count', 0)}")
    console.print(f"Beatmapsets: {samples.get('beatmapsets', {}).get('count', 0)}")

    users = samples.get("users", {})
    console.print(f"\nUsers (total: {users.get('count', 0)}):")
    for ruleset in RULESETS:
        count = users.get("per_ruleset", {}).get(ruleset, 0)
        console.print(f"  [cyan]{ruleset}:[/cyan] {count}")

    scores = samples.get("scores", {})
    console.print(f"\nScores (total: {scores.get('count', 0)}):")
    for score_type in SCORE_TYPES:
        count = scores.get("per_type", {}).get(score_type, 0)
        console.print(f"  [cyan]{score_type}:[/cyan] {count}")

    console.print(f"\nBeatmap Scores: {samples.get('beatmap_scores', {}).get('count', 0)}")
    console.print(f"Beatmap Attributes: {samples.get('beatmap_attributes', {}).get('count', 0)}")

    console.print("\n[bold]Fixture Files[/bold]")
    fixtures = get_all_fixture_files()

    for category, files in fixtures.items():
        if isinstance(files, dict):
            console.print(f"\n[yellow]{category.upper()}:[/yellow]")
            for subcat, subfiles in files.items():
                console.print(f"  {subcat}/: {len(subfiles)} files")
        else:
            console.print(f"\n[yellow]{category.upper()}:[/yellow] {len(files)} files")

    console.print()


async def cmd_validate_fixtures():
    fixtures = get_all_fixture_files()
    errors = []

    console.print("\n[bold]=== Validating Fixtures ===[/bold]\n")

    for category, files in fixtures.items():
        if isinstance(files, dict):
            for subcat, subfiles in files.items():
                for filepath in subfiles:
                    try:
                        with open(filepath) as f:
                            data = json.load(f)
                        if not isinstance(data, dict):
                            errors.append(f"{filepath}: Invalid JSON structure")
                    except json.JSONDecodeError as e:
                        errors.append(f"{filepath}: JSON decode error - {e}")
        else:
            for filepath in files:
                try:
                    with open(filepath) as f:
                        data = json.load(f)
                    if not isinstance(data, dict):
                        errors.append(f"{filepath}: Invalid JSON structure")
                except json.JSONDecodeError as e:
                    errors.append(f"{filepath}: JSON decode error - {e}")

    if errors:
        console.print("[red]❌ Validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
    else:
        console.print("[green]✅ All fixtures are valid JSON with proper structure[/green]")

    console.print()


async def cmd_promote_fixtures():
    from shutil import copy2

    test_fixtures_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "osu"
    test_fixtures_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_metadata()
    copied = 0

    console.print("\n[bold]=== Promoting Fixtures ===[/bold]\n")

    for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
        src_path = FIXTURES_DIR / category
        dst_path = test_fixtures_dir / category
        dst_path.mkdir(parents=True, exist_ok=True)

        if src_path.exists():
            for filepath in src_path.glob("*.json"):
                copy2(filepath, dst_path / filepath.name)
                copied += 1
            src_path.unlink(missing_ok=True)

    for category in ["users", "scores"]:
        src_path = FIXTURES_DIR / category
        dst_path = test_fixtures_dir / category
        dst_path.mkdir(parents=True, exist_ok=True)

        if src_path.exists():
            for sub in src_path.iterdir():
                if sub.is_dir():
                    sub_dst = dst_path / sub.name
                    sub_dst.mkdir(parents=True, exist_ok=True)
                    for filepath in sub.glob("*.json"):
                        copy2(filepath, sub_dst / filepath.name)
                        copied += 1
                    sub.unlink(missing_ok=True)

    if metadata.get("last_updated"):
        metadata["last_updated"] = None
        metadata["samples"] = {
            "beatmaps": {"count": 0, "last_fetched": None},
            "beatmapsets": {"count": 0, "last_fetched": None},
            "users": {"count": 0, "per_ruleset": {r: 0 for r in RULESETS}, "last_fetched": None},
            "scores": {"count": 0, "per_type": {t: 0 for t in SCORE_TYPES}, "last_fetched": None},
            "beatmap_scores": {"count": 0, "last_fetched": None},
            "beatmap_attributes": {"count": 0, "last_fetched": None},
        }
        save_metadata(metadata)

    console.print(f"[green]✅ Promoted {copied} fixture files to tests/fixtures/osu/[/green]")
    console.print("   [dim]Instance fixtures cleaned up[/dim]\n")


async def cmd_wipe_fixtures(clear_failed_ids: bool = False):
    wipe_all_fixtures(clear_failed_ids=clear_failed_ids)
    console.print("[green]✅ All fixtures wiped[/green]\n")
