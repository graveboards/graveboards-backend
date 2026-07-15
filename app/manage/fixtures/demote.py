from rich.console import Console
from rich.prompt import Confirm

from app.fixtures.metadata_io import load_metadata, save_metadata
from .helpers import get_categories_to_process
from .move_helpers import _move_fixture_files

console = Console()


async def cmd_demote_fixtures(
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
        response = Confirm.ask(
            "This will move fixture files back to instance fixtures. Continue?", default=False
        )
        if not response:
            console.print("[dim]Aborted.[/dim]")
            return

    metadata = load_metadata()

    console.print("\n[bold]=== Demoting Fixtures ===[/bold]\n")

    categories_to_demote = get_categories_to_process(
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
        categories=categories_to_demote,
        src_base="tests",
        dst_base="instance",
        metadata=metadata,
    )

    save_metadata(metadata)

    if missing > 0:
        console.print(f"  [yellow]⚠️ {missing} file(s) already missing, skipped[/yellow]")
    console.print(f"[green]✅ Demoted {copied} fixture files from tests/fixtures/[/green]")
