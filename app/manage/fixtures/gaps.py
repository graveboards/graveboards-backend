"""CLI command for identifying fixture gaps.

Usage:
    manage fixtures gaps [--category CATEGORY] [--format FORMAT]

Examples:
    manage fixtures gaps
    manage fixtures gaps --category beatmaps
    manage fixtures gaps --format json
"""

import argparse
import json
from datetime import datetime, timezone
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich.box import SIMPLE_HEAD

from tests.fixtures.health import get_category_gaps, get_incomplete_categories
from app.fixtures.utils import RULESETS, SCORE_TYPES


console = Console()


def format_percentage(value: float) -> str:
    """Format a percentage with color coding."""
    if value >= 100:
        return f"[green]{value:.1f}%[/green]"
    elif value >= 80:
        return f"[yellow]{value:.1f}%[/yellow]"
    else:
        return f"[red]{value:.1f}%[/red]"


async def cmd_fixture_gaps(
    category: str | None = None,
    format_type: str = "text"
) -> None:
    """Show missing fixture categories and gaps.
    
    Args:
        category: Specific category to check (None for all)
        format_type: Output format (text or json)
    """
    if category:
        gaps = get_category_gaps()
        category_gaps = [g for g in gaps if g["category"] == category]
        
        if format_type == "json":
            result = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "category": category,
                "gaps": category_gaps
            }
            console.print(json.dumps(result, indent=2))
        else:
            if not category_gaps:
                console.print(f"[green]✅ No gaps found for '{category}'[/green]")
                return
            
            title = Text(f"Gaps for Category: {category}", style="bold magenta")
            title.append("\n", style="")
            title.append("Missing fixture coverage", style="dim")
            console.print(Panel(title, box=SIMPLE_HEAD))
            
            for gap in category_gaps:
                table = Table(show_header=False)
                table.add_column("Metric", style="cyan")
                table.add_column("Value", style="white")
                
                table.add_row("Category", gap["category"])
                table.add_row("Expected Count", str(gap["expected_count"]))
                table.add_row("Actual Count", str(gap["actual_count"]))
                table.add_row("Missing Count", str(gap["missing_count"]))
                table.add_row("Coverage", format_percentage(gap["coverage_percentage"]))
                
                console.print(table)
                
                if gap.get("expected_files"):
                    console.print("\n[bold]Expected Files:[/bold]")
                    for filename in gap["expected_files"][:20]:
                        console.print(f"  {filename}")
                    if len(gap["expected_files"]) > 20:
                        console.print(f"  ... and {len(gap['expected_files']) - 20} more")
    else:
        gaps = get_category_gaps()
        incomplete = get_incomplete_categories()
        
        if format_type == "json":
            result = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "total_gaps": len(gaps),
                "incomplete_categories": len(incomplete),
                "gaps": gaps
            }
            console.print(json.dumps(result, indent=2))
        else:
            if not gaps:
                console.print("[green]✅ No gaps found - all fixture categories are complete![/green]")
                return
            
            title = Text("Fixture Gaps Report", style="bold magenta")
            title.append("\n", style="")
            title.append(f"Found {len(gaps)} categories with missing fixtures", style="dim")
            console.print(Panel(title, box=SIMPLE_HEAD))
            
            gap_table = Table(box=SIMPLE_HEAD)
            gap_table.add_column("Category", style="cyan")
            gap_table.add_column("Missing", style="red")
            gap_table.add_column("Coverage", style="white")
            gap_table.add_column("Files", style="white")
            
            for gap in gaps:
                gap_table.add_row(
                    gap["category"],
                    str(gap["missing_count"]),
                    format_percentage(gap["coverage_percentage"]),
                    f"{gap['actual_count']}/{gap['expected_count']}"
                )
            
            console.print(gap_table)
            
            console.print("\n[bold yellow]Detailed Gap Information:[/bold yellow]")
            for gap in gaps:
                console.print(f"\n[bold]{gap['category']}[/bold]")
                console.print(f"  Expected: {gap['expected_count']}")
                console.print(f"  Actual: {gap['actual_count']}")
                console.print(f"  Missing: {gap['missing_count']}")
                console.print(f"  Coverage: {format_percentage(gap['coverage_percentage'])}")
                
                if gap.get("expected_files"):
                    missing_count = gap['expected_count'] - gap['actual_count']
                    if missing_count <= 10:
                        console.print("  Missing files:")
                        console.print(f"    {', '.join(gap['expected_files'][-missing_count:])}")
                    else:
                        console.print(f"  Missing {missing_count} files (list truncated)")


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Show missing fixture categories and gaps"
    )
    parser.add_argument(
        "--category", "-c",
        choices=["beatmaps", "beatmapsets", "users", "scores", "beatmap_scores", "beatmap_attributes"],
        help="Specific category to check"
    )
    parser.add_argument(
        "--format", "-f",
        dest="format_type",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)"
    )
    
    args = parser.parse_args()
    cmd_fixture_gaps(
        category=args.category,
        format_type=args.format_type
    )


if __name__ == "__main__":
    main()
