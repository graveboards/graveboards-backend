from rich.console import Console
from rich.columns import Columns
from rich.console import Group
from rich.panel import Panel
from rich.table import Table
from rich import box

from app.fixtures.utils import TEST_FIXTURES_DIR, load_metadata, FIXTURES_DIR, RULESETS, SCORE_TYPES
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def cmd_list_fixtures():
    metadata = load_metadata()

    def count_files(path):
        return len(list(path.glob("*.json"))) if path.exists() else 0

    def get_instance_counts():
        counts = {}
        for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            path = FIXTURES_DIR / category
            counts[category] = count_files(path)

        users_path = FIXTURES_DIR / "users"
        if users_path.exists():
            counts["users"] = {r: count_files(users_path / r) for r in RULESETS}
        else:
            counts["users"] = {r: 0 for r in RULESETS}

        scores_path = FIXTURES_DIR / "scores"
        if scores_path.exists():
            counts["scores"] = {t: count_files(scores_path / t) for t in SCORE_TYPES}
        else:
            counts["scores"] = {t: 0 for t in SCORE_TYPES}

        return counts

    def get_promoted_counts():
        counts = {}
        for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            path = TEST_FIXTURES_DIR / category
            counts[category] = count_files(path)

        users_path = TEST_FIXTURES_DIR / "users"
        if users_path.exists():
            counts["users"] = {r: count_files(users_path / r) for r in RULESETS}
        else:
            counts["users"] = {r: 0 for r in RULESETS}

        scores_path = TEST_FIXTURES_DIR / "scores"
        if scores_path.exists():
            counts["scores"] = {t: count_files(scores_path / t) for t in SCORE_TYPES}
        else:
            counts["scores"] = {t: 0 for t in SCORE_TYPES}

        return counts

    sample_metadata = metadata.get("samples", {})
    promoted_metadata = metadata.get("promoted_fixtures", {})

    instance_counts = get_instance_counts()
    promoted_counts = get_promoted_counts()

    def create_table(fixture_counts, is_promoted=False):
        table = Table(box=box.SQUARE, padding=0)
        table.add_column("Category", style="bold cyan", width=12)
        table.add_column("Meta", style="magenta", width=8)
        table.add_column("Disk", style="yellow", width=8)
        table.add_column("Sync", style="", width=6)

        metadata_source = promoted_metadata if is_promoted else sample_metadata

        for category in ["beatmaps", "beatmapsets", "beatmap_scores", "beatmap_attributes"]:
            meta_count = metadata_source.get(category, {}).get("count", 0)
            disk_count = fixture_counts.get(category, 0)
            sync = "[green]✓[/green]" if meta_count == disk_count else "[red]✗[/red]"
            table.add_row(category, str(meta_count), str(disk_count), sync)

        users_meta = metadata_source.get("users", {}).get("count", 0)
        users_disk = sum(fixture_counts.get("users", {}).values())
        users_sync = "[green]✓[/green]" if users_meta == users_disk else "[red]✗[/red]"
        table.add_row("[b]users[/b]", str(users_meta), str(users_disk), users_sync)

        for ruleset in RULESETS:
            rule_meta = metadata_source.get("users", {}).get("per_ruleset", {}).get(ruleset, 0)
            rule_disk = fixture_counts.get("users", {}).get(ruleset, 0)
            rule_sync = "[green]✓[/green]" if rule_meta == rule_disk else "[red]✗[/red]"
            table.add_row(f"  {ruleset}", str(rule_meta), str(rule_disk), rule_sync)

        scores_meta = metadata_source.get("scores", {}).get("count", 0)
        scores_disk = sum(fixture_counts.get("scores", {}).values())
        scores_sync = "[green]✓[/green]" if scores_meta == scores_disk else "[red]✗[/red]"
        table.add_row("[b]scores[/b]", str(scores_meta), str(scores_disk), scores_sync)

        for score_type in SCORE_TYPES:
            type_meta = metadata_source.get("scores", {}).get("per_type", {}).get(score_type, 0)
            type_disk = fixture_counts.get("scores", {}).get(score_type, 0)
            type_sync = "[green]✓[/green]" if type_meta == type_disk else "[red]✗[/red]"
            table.add_row(f"  {score_type}", str(type_meta), str(type_disk), type_sync)

        return table

    header_table = Table(show_header=False, box=None, padding=(0, 1))
    header_table.add_column(justify="center")
    header_table.add_row("")
    header_table.add_row("[bold]=== Fixture Data Status ===[/bold]")
    header_table.add_row(f"Last updated: {metadata.get('last_updated', 'Never')}")
    header_table.add_row(f"Source: {metadata.get('source', 'N/A')}")
    header_table.add_row("")

    header_panel = Panel(header_table, box=box.ROUNDED, padding=(0, 2), expand=False)

    instance_table = create_table(instance_counts, is_promoted=False)
    instance_panel = Panel(instance_table, title="[bold cyan]Transient (instance/)[/bold cyan]", box=box.ROUNDED, padding=(0, 0))

    promoted_table = create_table(promoted_counts, is_promoted=True)
    promoted_panel = Panel(promoted_table, title="[bold cyan]Promoted (tests/)[/bold cyan]", box=box.ROUNDED, padding=(0, 0))

    header_group = Group(header_panel)

    side_by_side = Columns([instance_panel, promoted_panel], equal=True, padding=(0, 1))

    console.print(Group(header_group, side_by_side))
