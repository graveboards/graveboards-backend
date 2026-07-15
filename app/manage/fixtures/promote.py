from datetime import datetime, timezone

from rich.console import Console
from rich.prompt import Prompt

from app.fixtures.metadata_io import create_empty_samples, load_metadata, save_metadata
from .helpers import get_categories_to_process
from .move_helpers import _move_fixture_files

console = Console()


async def cmd_promote_fixtures(
    beatmaps: bool,
    beatmapsets: bool,
    users: bool,
    scores: bool,
    beatmap_scores: bool,
    beatmap_attributes: bool,
    queues: bool = False,
    requests: bool = False,
    force: bool = False,
):
    if not force:
        response = Prompt.ask(
            "This will move fixture files and delete the originals. Continue?",
            choices=["y", "n"],
            default="n",
        )
        if response != "y":
            console.print("[dim]Aborted.[/dim]")
            return

    metadata = load_metadata()
    current_time = datetime.now(timezone.utc).isoformat()

    console.print("\n[bold]=== Promoting Fixtures ===[/bold]\n")

    categories_to_promote = get_categories_to_process(
        beatmaps=beatmaps,
        beatmapsets=beatmapsets,
        users=users,
        scores=scores,
        beatmap_scores=beatmap_scores,
        beatmap_attributes=beatmap_attributes,
        queues=queues,
        requests=requests,
    )

    copied, missing = _move_fixture_files(
        categories=categories_to_promote,
        src_base="instance",
        dst_base="tests",
        metadata=metadata,
    )

    metadata["samples"] = create_empty_samples()
    metadata["last_updated"] = current_time
    save_metadata(metadata)

    if missing > 0:
        console.print(f"  [yellow]⚠️ {missing} file(s) already missing, skipped[/yellow]")
    console.print(f"[green]✅ Promoted {copied} fixture files to tests/fixtures/[/green]")
    console.print("   [dim]Instance fixtures cleaned up[/dim]\n")
