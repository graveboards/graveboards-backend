"""CLI command to generate queue and request fixtures.

Generates diverse queue and request fixtures for testing the search
engine's QUEUES and REQUESTS scopes, including varied names, descriptions,
visibility states, statuses, comments, and cross-entity relationships.

Usage:
    manage fixtures generate [--queue-count N] [--request-count N]

Examples:
    manage fixtures generate
    manage fixtures generate --queue-count 100 --request-count 200
"""
import random
from rich.console import Console
from rich.table import Table

from app.fixtures.queue_request_generator import QueueRequestFixtureGenerator
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


async def cmd_generate(
    queue_count: int = 50,
    request_count: int = 100,
):
    """Generate diverse queue and request fixtures for search testing."""
    console.print("[bold]Generating queue and request fixtures...[/bold]")
    console.print(f"  Queues: {queue_count}, Requests: {request_count}")
    console.print()

    generator = QueueRequestFixtureGenerator()

    queues = generator.generate_queues(count=queue_count)
    requests = generator.generate_requests(queues=queues, count=request_count)

    queues_path = generator.save_queues(queues)
    requests_path = generator.save_requests(requests)

    console.print(f"[green]Generated {len(queues)} queue fixtures[/green]")
    console.print(f"[green]Generated {len(requests)} request fixtures[/green]")
    console.print()

    result_table = Table(show_header=False)
    result_table.add_column("Category")
    result_table.add_column("Count")
    result_table.add_column("Path")

    result_table.add_row("queues", str(len(queues)), str(queues_path))
    result_table.add_row("requests", str(len(requests)), str(requests_path))

    console.print(result_table)
    console.print()

    console.print("[bold]Generated queue names:[/bold]")
    name_counts = {}
    for q in queues:
        name = q["name"]
        name_counts[name] = name_counts.get(name, 0) + 1
    for name, count in sorted(name_counts.items(), key=lambda x: -x[1])[:10]:
        console.print(f"  {name}: {count}")
    if len(name_counts) > 10:
        console.print(f"  ... and {len(name_counts) - 10} more unique names")

    console.print()
    console.print("[bold]Generated request statuses:[/bold]")
    status_names = {-1: "rejected", 0: "pending", 1: "accepted"}
    status_counts = {}
    for r in requests:
        status = r["status"]
        status_counts[status] = status_counts.get(status, 0) + 1
    for status_id, count in sorted(status_counts.items()):
        status_name = status_names.get(status_id, f"unknown({status_id})")
        console.print(f"  {status_name} ({status_id}): {count}")

    console.print()
    console.print(f"[bold]Seed data updated:[/bold]")
    console.print(f"  Queues: {queues_path / 'queues.json'} ({len(queues)} entries)")
    console.print(f"  Requests: {requests_path / 'requests.json'} ({len(requests)} entries)")
