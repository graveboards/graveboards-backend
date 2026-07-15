"""CLI command to extract user IDs from beatmapset fixtures and fetch those users.

This command reads beatmapset fixtures to extract unique owner user IDs,
then fetches those users from the osu! API. This ensures that all users
referenced by beatmapsets are available for seeding.

Usage:
    manage fixtures fetch-users-from-beatmapsets
"""

import json
from pathlib import Path
from rich.console import Console
from rich.table import Table

from app.config import PROJECT_ROOT
from app.redis import RedisClient
from app.logging import get_logger
from app.fixtures.orchestrator import FixtureOrchestrator
from app.fixtures.criteria import FetchCriteria

console = Console()
logger = get_logger(__name__)

FIXTURES_DIR = PROJECT_ROOT / "instance" / "fixtures"


async def cmd_fetch_users_from_beatmapsets():
    """Extract user IDs from beatmapset fixtures and fetch those users."""
    bms_path = FIXTURES_DIR / "beatmapsets"

    if not bms_path.exists():
        console.print("[red]Error: No beatmapset fixtures found.[/red]")
        console.print("Run `fixtures fetch --criteria minimal --beatmapsets 30` first.")
        return

    # Extract unique owner user IDs from beatmapset fixtures
    owner_ids: set[int] = set()
    for f in sorted(bms_path.glob("beatmapset_*.json")):
        try:
            with open(f) as fh:
                data = json.load(fh)
            user_id = data.get("user_id")
            if user_id:
                owner_ids.add(user_id)
        except (json.JSONDecodeError, KeyError):
            continue

    if not owner_ids:
        console.print("[yellow]No owner user IDs found in beatmapset fixtures.[/yellow]")
        return

    # Sort for deterministic ordering
    user_ids = sorted(owner_ids)

    console.print(f"[bold]Found {len(user_ids)} unique beatmapset owner(s):[/bold]")
    for uid in user_ids[:10]:
        console.print(f"  - {uid}")
    if len(user_ids) > 10:
        console.print(f"  ... and {len(user_ids) - 10} more")
    console.print()

    # Fetch these users
    console.print(f"[bold]Fetching {len(user_ids)} user(s) from osu! API...[/bold]")
    console.print()

    rc = RedisClient()
    try:
        criteria = FetchCriteria()
        orchestrator = FixtureOrchestrator(criteria, rc)
        report = await orchestrator.fetch_users_by_ids(user_ids, ruleset="osu")

        fetched_count = report.results.get("users", {}).get("osu", 0)
        console.print()
        console.print(f"[green]Successfully fetched {fetched_count} user(s).[/green]")
    except Exception as e:
        console.print(f"[red]Error fetching users: {e}[/red]")
        import traceback

        console.print(traceback.format_exc())
    finally:
        await rc.aclose()
