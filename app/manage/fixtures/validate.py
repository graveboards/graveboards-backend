import json
from pathlib import Path
from rich.console import Console

from app.fixtures.utils import get_all_fixture_files
from app.logging import get_logger

console = Console()
logger = get_logger(__name__)


def _validate_file(filepath: Path, errors: list[str]) -> None:
    try:
        with open(filepath) as f:
            data = json.load(f)
        if not isinstance(data, (dict, list)):
            errors.append(f"{filepath}: Invalid JSON structure")
    except json.JSONDecodeError as e:
        errors.append(f"{filepath}: JSON decode error - {e}")


async def cmd_validate_fixtures():
    fixtures = get_all_fixture_files()
    errors = []

    console.print("\n[bold]=== Validating Fixtures ===[/bold]\n")

    for category, files in fixtures.items():
        if isinstance(files, dict):
            for subcat, subfiles in files.items():
                for filepath in subfiles:
                    _validate_file(filepath, errors)
        else:
            for filepath in files:
                _validate_file(filepath, errors)

    if errors:
        console.print("[red]❌ Validation failed:[/red]")
        for error in errors:
            console.print(f"  - {error}")
    else:
        console.print("[green]✅ All fixtures are valid JSON with proper structure[/green]")

    console.print()
