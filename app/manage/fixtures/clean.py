import json
import os
import tempfile
from pathlib import Path
from shutil import rmtree

from rich.console import Console

from app.fixtures.paths import FIXTURES_DIR
from app.fixtures.metadata_io import load_metadata, save_metadata, create_empty_samples, create_empty_promoted_fixtures
from app.fixtures.constants import RULESETS
from app.fixtures.failed_id_store import FailedIdStore
from app.redis import RedisClient

console = Console()


def _atomic_save_metadata(metadata: dict, metadata_path: Path) -> None:
    """Save metadata atomically by writing to a temp file then renaming."""
    fd, tmp_path = tempfile.mkstemp(dir=metadata_path.parent, suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(metadata, f, indent=2, default=str)
        Path(tmp_path).replace(metadata_path)
    except Exception:
        Path(tmp_path).unlink(missing_ok=True)
        raise


async def cmd_clean_fixtures(
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

    console.print("\n[bold blue]Cleaning fixtures...[/bold blue]\n")

    metadata = load_metadata()

    deleted_count = 0
    if FIXTURES_DIR.exists():
        for sub_dir in FIXTURES_DIR.iterdir():
            if sub_dir.is_dir():
                rmtree(sub_dir)
                console.print(f"[green]✅ Deleted: {sub_dir.name}[/green]")
                deleted_count += 1

    metadata["samples"] = create_empty_samples()
    metadata.pop("search_test_coverage", None)
    metadata.pop("targeted", None)
    if clear_failed_ids:
        rc = RedisClient()
        store = FailedIdStore(rc)
        await store.clear_all()
        await rc.aclose()
        console.print("[green]✅ Failed IDs cleared from Redis[/green]")
    if clear_top_player_ids:
        metadata["top_player_ids"] = {r: [] for r in RULESETS}
    if clear_promoted:
        if metadata.get("promoted_fixtures", {}).get("beatmaps", {}).get("count", 0) > 0:
            console.print(
                "[yellow]⚠️  WARNING: Removing promoted fixture metadata while fixture files still exist on disk![/yellow]")
            console.print("   This will cause metadata to be out of sync with actual fixture state.")
        metadata["promoted_fixtures"] = create_empty_promoted_fixtures()

    if deleted_count > 0:
        _atomic_save_metadata(metadata, FIXTURES_DIR / "metadata.json")
    else:
        save_metadata(metadata)

    console.print("[green]✅ Fixtures cleaned![/green]\n")
