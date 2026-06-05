import json
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.table import Table

from app.logging import get_logger
from app.fixtures.utils import (
    FIXTURES_DIR,
    load_metadata,
    save_metadata,
    get_all_fixture_files,
    RULESETS,
    SCORE_TYPES,
    calculate_sample_counts,
)
from app.fixtures.fetcher import FixtureDataFetcher
from app.redis import RedisClient

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


async def cmd_refresh_top_players(
        rulesets: Optional[list[str]] = None,
        count: int = 1000,
) -> None:
    rc = RedisClient()
    fetcher = FixtureDataFetcher(rc)
    fetcher.logger = logger

    if rulesets is None:
        rulesets = RULESETS

    console.print("\n[bold blue]Refreshing top players from osu! API...[/bold blue]")
    console.print(f"[bold]Rulesets:[/bold] {', '.join(rulesets)}")
    console.print(f"[bold]Count per ruleset:[/bold] {count}\n")

    fetched = await fetcher.fetch_top_players(rulesets=rulesets, count_per_ruleset=count)

    console.print("\n[bold green]Top players refresh complete![/bold green]\n")
    console.print("[bold]Fetched:[/bold]")
    table = Table(show_header=False)
    table.add_column("Ruleset")
    table.add_column("Count")
    for ruleset, player_ids in fetched.items():
        table.add_row(ruleset, str(len(player_ids)))
    console.print(table)
    console.print()


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
    sample_table = Table(show_header=False)
    sample_table.add_column("Category")
    sample_table.add_column("Count")

    add_counts_to_table(sample_counts, sample_table)
    console.print(sample_table)

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


def _validate_file(filepath: Path, errors: list[str]) -> None:
    try:
        with open(filepath) as f:
            data = json.load(f)
        if not isinstance(data, (dict, list)):
            errors.append(f"{filepath}: Invalid JSON structure")
    except json.JSONDecodeError as e:
        errors.append(f"{filepath}: JSON decode error - {e}")


async def cmd_validate_fixtures():
    fixtures = get_all_fixture_files()
    errors = []

    console.print("\n[bold]=== Validating Fixtures ===[/bold]\n")

    for category, files in fixtures.items():
        if isinstance(files, dict):
            for subcat, subfiles in files.items():
                for filepath in subfiles:
                    _validate_file(filepath, errors)
        else:
            for filepath in files:
                _validate_file(filepath, errors)

    if errors:
        console.print("[red]❌ Validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
    else:
        console.print("[green]✅ All fixtures are valid JSON with proper structure[/green]")

    console.print()


async def cmd_promote_fixtures(
        beatmaps: bool,
        beatmapsets: bool,
        users: bool,
        scores: bool,
        beatmap_scores: bool,
        beatmap_attributes: bool,
):
    from shutil import copy2, rmtree

    test_fixtures_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "osu"
    test_fixtures_dir.mkdir(parents=True, exist_ok=True)

    metadata = load_metadata()
    copied = 0
    current_time = datetime.now(timezone.utc).isoformat()

    console.print("\n[bold]=== Promoting Fixtures ===[/bold]\n")

    all_categories = not any([beatmaps, beatmapsets, users, scores, beatmap_scores, beatmap_attributes])

    categories_to_promote = []
    if all_categories or beatmaps:
        categories_to_promote.append(("beatmaps", "beatmaps", "beatmaps"))
    if all_categories or beatmapsets:
        categories_to_promote.append(("beatmapsets", "beatmapsets", "beatmapsets"))
    if all_categories or beatmap_scores:
        categories_to_promote.append(("beatmap_scores", "beatmap_scores", "beatmap_scores"))
    if all_categories or beatmap_attributes:
        categories_to_promote.append(("beatmap_attributes", "beatmap_attributes", "beatmap_attributes"))
    if all_categories or users:
        categories_to_promote.append(("users", "users", "users"))
    if all_categories or scores:
        categories_to_promote.append(("scores", "scores", "scores"))

    for src_name, dst_name, meta_name in categories_to_promote:
        src_path = FIXTURES_DIR / src_name
        dst_path = test_fixtures_dir / dst_name

        if src_name in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            if src_path.exists():
                count = len(list(src_path.glob("*.json")))
                for filepath in src_path.glob("*.json"):
                    copy2(filepath, dst_path / filepath.name)
                    copied += 1
                rmtree(src_path)
                metadata["promoted_fixtures"][meta_name] = {
                    "count": metadata["promoted_fixtures"][meta_name].get("count", 0) + count,
                    "last_promoted": current_time,
             }
        elif src_name in ["users", "scores"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            total_count = 0
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        sub_dst = dst_path / sub.name
                        sub_dst.mkdir(parents=True, exist_ok=True)
                        count = len(list(sub.glob("*.json")))
                        total_count += count
                        for filepath in sub.glob("*.json"):
                            copy2(filepath, sub_dst / filepath.name)
                            copied += 1
                        rmtree(sub)
                        if src_name == "users":
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_ruleset": {}}
                            if "per_ruleset" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_ruleset"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_ruleset"][sub.name] = metadata["promoted_fixtures"][meta_name]["per_ruleset"].get(sub.name, 0) + count
                        else:
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_type": {}}
                            if "per_type" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_type"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_type"][sub.name] = metadata["promoted_fixtures"][meta_name]["per_type"].get(sub.name, 0) + count
                src_path.rmdir()
                metadata["promoted_fixtures"][meta_name]["count"] = metadata["promoted_fixtures"][meta_name].get("count", 0) + total_count
                metadata["promoted_fixtures"][meta_name]["last_promoted"] = current_time

    if metadata.get("last_updated"):
        metadata["last_updated"] = None
        metadata["samples"] = _create_empty_samples()
    save_metadata(metadata)

    console.print(f"[green]✅ Promoted {copied} fixture files to tests/fixtures/osu/[/green]")
    console.print("   [dim]Instance fixtures cleaned up[/dim]\n")


async def cmd_demote_fixtures(
        beatmaps: bool,
        beatmapsets: bool,
        users: bool,
        scores: bool,
        beatmap_scores: bool,
        beatmap_attributes: bool,
):
    from shutil import copy2

    test_fixtures_dir = Path(__file__).resolve().parent.parent.parent / "tests" / "fixtures" / "osu"

    moved = 0
    current_time = datetime.now(timezone.utc).isoformat()

    console.print("\n[bold]=== Demoting Fixtures ===[/bold]\n")

    all_categories = not any([beatmaps, beatmapsets, users, scores, beatmap_scores, beatmap_attributes])

    categories_to_demote = []
    if all_categories or beatmaps:
        categories_to_demote.append(("beatmaps", "beatmaps", "beatmaps"))
    if all_categories or beatmapsets:
        categories_to_demote.append(("beatmapsets", "beatmapsets", "beatmapsets"))
    if all_categories or beatmap_scores:
        categories_to_demote.append(("beatmap_scores", "beatmap_scores", "beatmap_scores"))
    if all_categories or beatmap_attributes:
        categories_to_demote.append(("beatmap_attributes", "beatmap_attributes", "beatmap_attributes"))
    if all_categories or users:
        categories_to_demote.append(("users", "users", "users"))
    if all_categories or scores:
        categories_to_demote.append(("scores", "scores", "scores"))

    metadata = load_metadata()

    for src_name, dst_name, meta_name in categories_to_demote:
        src_path = test_fixtures_dir / src_name
        dst_path = FIXTURES_DIR / dst_name

        if src_name in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            if src_path.exists():
                count = len(list(src_path.glob("*.json")))
                for filepath in src_path.glob("*.json"):
                    copy2(filepath, dst_path / filepath.name)
                    moved += 1
                    filepath.unlink(missing_ok=True)
                metadata["promoted_fixtures"][meta_name]["count"] = max(0, metadata["promoted_fixtures"][meta_name].get("count", 0) - count)
                metadata["promoted_fixtures"][meta_name]["last_promoted"] = current_time
                metadata["samples"][meta_name]["count"] = metadata["samples"][meta_name].get("count", 0) + count
        elif src_name in ["users", "scores"]:
            dst_path.mkdir(parents=True, exist_ok=True)
            total_count = 0
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        sub_dst = dst_path / sub.name
                        sub_dst.mkdir(parents=True, exist_ok=True)
                        count = len(list(sub.glob("*.json")))
                        total_count += count
                        for filepath in sub.glob("*.json"):
                            copy2(filepath, sub_dst / filepath.name)
                            moved += 1
                            filepath.unlink(missing_ok=True)
                        if src_name == "users":
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_ruleset": {}}
                            if "per_ruleset" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_ruleset"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_ruleset"][sub.name] = max(0, metadata["promoted_fixtures"][meta_name]["per_ruleset"].get(sub.name, 0) - count)
                            metadata["samples"]["users"]["per_ruleset"][sub.name] = metadata["samples"]["users"]["per_ruleset"].get(sub.name, 0) + count
                        else:
                            if meta_name not in metadata["promoted_fixtures"]:
                                metadata["promoted_fixtures"][meta_name] = {"count": 0, "per_type": {}}
                            if "per_type" not in metadata["promoted_fixtures"][meta_name]:
                                metadata["promoted_fixtures"][meta_name]["per_type"] = {}
                            metadata["promoted_fixtures"][meta_name]["per_type"][sub.name] = max(0, metadata["promoted_fixtures"][meta_name]["per_type"].get(sub.name, 0) - count)
                            metadata["samples"]["scores"]["per_type"][sub.name] = metadata["samples"]["scores"]["per_type"].get(sub.name, 0) + count
                metadata["promoted_fixtures"][meta_name]["count"] = max(0, metadata["promoted_fixtures"][meta_name].get("count", 0) - total_count)
                metadata["promoted_fixtures"][meta_name]["last_promoted"] = current_time
                metadata["samples"][meta_name]["count"] = metadata["samples"][meta_name].get("count", 0) + total_count

    save_metadata(metadata)

    console.print(f"[green]✅ Demoted {moved} fixture files from tests/fixtures/osu/[/green]")


async def cmd_wipe_fixtures(
        clear_failed_ids: bool = False,
        clear_top_player_ids: bool = False,
        clear_promoted: bool = False,
):
    from shutil import rmtree

    console.print("\n[bold blue]Wiping fixtures...[/bold blue]\n")

    metadata = load_metadata()

    if FIXTURES_DIR.exists():
        for sub_dir in FIXTURES_DIR.iterdir():
            if sub_dir.is_dir():
                rmtree(sub_dir)
                console.print(f"[green]✅ Deleted: {sub_dir.name}[/green]")

    metadata["samples"] = _create_empty_samples()
    if clear_failed_ids:
        metadata["failed_ids"] = {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {r: [] for r in RULESETS},
        }
    if clear_top_player_ids:
        metadata["top_player_ids"] = {r: [] for r in RULESETS}
    if clear_promoted:
        if metadata.get("promoted_fixtures", {}).get("beatmaps", {}).get("count", 0) > 0:
            console.print(
                "[yellow]⚠️  WARNING: Removing promoted fixture metadata while fixture files still exist on disk![/yellow]")
            console.print("   This will cause metadata to be out of sync with actual fixture state.")
        metadata["promoted_fixtures"] = _create_empty_promoted_fixtures()
    save_metadata(metadata)

    console.print("[green]✅ Fixtures wiped![/green]\n")
