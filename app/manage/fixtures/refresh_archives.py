"""CLI command to refresh archive data from osu.sh.

Usage:
    manage fixtures refresh-archives [--force]

Examples:
    manage fixtures refresh-archives
    manage fixtures refresh-archives --force
"""

import argparse
import asyncio

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

from app.fixtures.archives import refresh_archive_index, load_archive_index, cleanup_archives
from app.fixtures.id_source import ArchiveIDSource
from app.redis import RedisClient
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def cmd_refresh_archives(force: bool = False) -> None:
    """Refresh archive index and extract player IDs from osu.sh archives.

    Args:
        force: Force refresh even if recently updated
    """
    rc = RedisClient()
    try:
        index = load_archive_index()

        if not force and index.last_updated:
            from datetime import datetime

            time_since_update = (datetime.now() - index.last_updated).total_seconds()

            if time_since_update < 3600:  # 1 hour cooldown
                console.print(
                    f"[yellow]Archives were updated {time_since_update:.0f}s ago. Skipping refresh. Use --force to force update.[/yellow]"
                )
                return

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            task = progress.add_task("Fetching archive index from osu.sh...", total=None)

            archive_index = await refresh_archive_index()

            progress.update(task, description=f"Indexed {len(archive_index.archives)} archives")

        console.print(
            Panel(
                f"[green]Archive index refreshed![/green]\n"
                f"Total archives: {len(archive_index.archives)}\n"
                f"Last updated: {archive_index.last_updated.strftime('%Y-%m-%d %H:%M:%S') if archive_index.last_updated else 'N/A'}\n"
                f"Ruleset coverage: {', '.join(archive_index.ruleset_archives.keys())}",
                title="Archive Refresh",
                border_style="green",
            )
        )

        console.print("\n[bold blue]Extracting player IDs from latest archives...[/bold blue]")

        source = ArchiveIDSource(allow_download=True, pre_load=True)
        await source.resolve()

        total_ids = sum(len(ids) for ids in source.player_ids.values())

        console.print(f"[green]Extracted {total_ids} player IDs from archives[/green]")

        for ruleset, ids in source.player_ids.items():
            console.print(f"  {ruleset}: {len(ids)} IDs")

        console.print(f"  beatmaps: {len(source.beatmap_ids)} IDs")

        deleted = cleanup_archives()
        if deleted > 0:
            console.print(f"[dim]Cleaned up {deleted} tar.bz2 archive file(s)[/dim]")

        console.print("\n[bold green]Archive refresh complete![/bold green]")

    finally:
        await rc.aclose()


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Refresh fixture archive index from osu.sh")
    parser.add_argument(
        "--force", "-f", action="store_true", help="Force refresh even if recently updated"
    )

    args = parser.parse_args()
    asyncio.run(cmd_refresh_archives(force=getattr(args, "force", False)))


if __name__ == "__main__":
    main()
