"""CLI command to reconcile fixture metadata with disk state.

Usage:
    manage fixtures reconcile [--category CATEGORY] [--dry-run]

Examples:
    manage fixtures reconcile
    manage fixtures reconcile --category beatmaps
    manage fixtures reconcile --dry-run
"""

import argparse
import json
from pathlib import Path
from typing import Optional
import asyncio

from app.fixtures.reader import FixtureReader
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE_HEAD

console = Console()


async def cmd_reconcile(category: Optional[str] = None, dry_run: bool = False) -> None:
    """Reconcile fixture metadata counts with actual disk state.

    Args:
        category: Specific category to reconcile (None for all)
        dry_run: Show changes without applying them
    """
    manager = FixtureReader()

    if category:
        categories = [category]
    else:
        categories = [
            "beatmaps",
            "beatmapsets",
            "beatmap_scores",
            "beatmap_attributes",
            "users",
            "scores",
        ]

    changes = []

    for cat in categories:
        cat_changes = await manager.refresh_category_metadata(cat, dry_run=dry_run)
        changes.extend(cat_changes)

    if not changes:
        console.print("[green]No changes needed. Metadata is already in sync with disk.[/green]")
        return

    if dry_run:
        console.print(Panel(f"[yellow]Dry run: {len(changes)} change(s) would be made[/yellow]"))
    else:
        console.print(Panel(f"[green]Reconciled {len(changes)} fixture(s) from disk[/green]"))

    table = Table(box=SIMPLE_HEAD)
    table.add_column("Category", style="cyan")
    table.add_column("Action", style="white")
    table.add_column("Fixture ID", style="white")
    table.add_column("Disk Count", style="white")
    table.add_column("Old Meta Count", style="white")

    for change in changes[:20]:
        table.add_row(
            change["category"],
            change["action"],
            (
                change["fixture_id"][:8] + "..."
                if len(change["fixture_id"]) > 8
                else change["fixture_id"]
            ),
            str(change["disk_count"]),
            str(change.get("old_meta_count", "N/A")),
        )

    if len(changes) > 20:
        table.add_row(f"... and {len(changes) - 20} more", "", "", "", "")

    console.print(table)


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Reconcile fixture metadata with disk state")
    parser.add_argument(
        "--category",
        "-c",
        choices=[
            "beatmaps",
            "beatmapsets",
            "users",
            "scores",
            "beatmap_scores",
            "beatmap_attributes",
        ],
        help="Specific category to reconcile",
    )
    parser.add_argument("--dry-run", action="store_true", help="Show changes without applying them")

    args = parser.parse_args()
    asyncio.run(cmd_reconcile(category=args.category, dry_run=args.dry_run))


if __name__ == "__main__":
    main()
