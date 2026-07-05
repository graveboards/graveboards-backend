"""Seed subcommand parser."""

from app.database.seeding import SeedTarget


def build_seed_parser(subparsers):
    """Build the parser for the 'seed' subcommand."""
    seed_parser = subparsers.add_parser("seed", help="Seed database")
    seed_parser.add_argument(
        "target",
        metavar="target",
        type=SeedTarget,
        choices=list(SeedTarget),
        default=SeedTarget.ALL,
        help=f"What to seed in the database ({', '.join(SeedTarget)})"
    )
    return seed_parser
