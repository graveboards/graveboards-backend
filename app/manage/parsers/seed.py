"""Seed subcommand parser."""

from app.database.seeding import SeedTarget
from app.database.seeding.profiles import list_profiles


def build_seed_parser(subparsers):
    """Build the parser for the 'seed' subcommand."""
    seed_parser = subparsers.add_parser(
        "seed",
        help="Seed database",
        description=(
            "Seed the database with fixtures from instance/fixtures/.\n\n"
            "By default, seeds only what's currently available.\n"
            "Use --ensure-fixtures to auto-fetch/generate missing data."
        ),
    )
    seed_parser.add_argument(
        "target",
        metavar="target",
        type=SeedTarget,
        choices=list(SeedTarget),
        default=SeedTarget.ALL,
        help=f"What to seed in the database ({', '.join(SeedTarget)})",
    )
    seed_parser.add_argument(
        "--ensure-fixtures",
        action="store_true",
        help="Auto-fetch/generate missing fixtures before seeding",
    )
    seed_parser.add_argument(
        "--profile",
        type=str,
        default="default",
        choices=list_profiles(),
        help=(
            "Seeding profile for --ensure-fixtures (default: default). "
            "Available: " + ", ".join(list_profiles())
        ),
    )
    return seed_parser
