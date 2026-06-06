from shutil import rmtree

from rich.console import Console

from app.fixtures.utils import FIXTURES_DIR, load_metadata, save_metadata, RULESETS, create_empty_samples, create_empty_promoted_fixtures
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def cmd_wipe_fixtures(
    clear_failed_ids: bool = False,
    clear_top_player_ids: bool = False,
    clear_promoted: bool = False,
    force: bool = False,
):
    if not force:
        from rich.prompt import Prompt
        response = Prompt.ask("This will delete all fixture files and reset metadata. Continue?", choices=["y", "n"], default="n")
        if response != "y":
            console.print("[dim]Aborted.[/dim]")
            return

    console.print("\n[bold blue]Wiping fixtures...[/bold blue]\n")

    metadata = load_metadata()

    if FIXTURES_DIR.exists():
        for sub_dir in FIXTURES_DIR.iterdir():
            if sub_dir.is_dir():
                rmtree(sub_dir)
                console.print(f"[green]✅ Deleted: {sub_dir.name}[/green]")

    metadata["samples"] = create_empty_samples()
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
        metadata["promoted_fixtures"] = create_empty_promoted_fixtures()
    save_metadata(metadata)

    console.print("[green]✅ Fixtures wiped![/green]\n")
