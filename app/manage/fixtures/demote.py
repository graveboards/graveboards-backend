from datetime import datetime, timezone

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
    current_time = datetime.now(timezone.utc).isoformat()

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

    copied = _move_fixture_files(
        categories=categories_to_demote,
        src_base="tests",
        dst_base="instance",
        metadata=metadata,
        action="demote",
    )

    # Calculate missing files (files that don't exist in source)
    from app.fixtures.paths import (
        TEST_FIXTURES_DIR,
        QUEUE_TEST_FIXTURES_DIR,
        REQUEST_TEST_FIXTURES_DIR,
    )

    missing = 0
    for category in categories_to_demote:
        if category == "queues":
            src_path = QUEUE_TEST_FIXTURES_DIR
        elif category == "requests":
            src_path = REQUEST_TEST_FIXTURES_DIR
        else:
            src_path = TEST_FIXTURES_DIR / category

        if category in [
            "beatmaps",
            "beatmapsets",
            "beatmap_scores",
            "beatmap_attributes",
            "queues",
            "requests",
        ]:
            if src_path.exists():
                for f in src_path.glob("*.json"):
                    if not f.exists():
                        missing += 1
        elif category in ["users", "scores"]:
            if src_path.exists():
                for sub in src_path.iterdir():
                    if sub.is_dir():
                        for f in sub.glob("*.json"):
                            if not f.exists():
                                missing += 1

    save_metadata(metadata)

    if missing > 0:
        console.print(f"  [yellow]⚠️ {missing} file(s) already missing, skipped[/yellow]")
    console.print(f"[green]✅ Demoted {copied} fixture files from tests/fixtures/[/green]")
