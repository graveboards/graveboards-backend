"""Reset subcommand parser."""

from app.database.seeding import SeedTarget


def build_reset_parser(subparsers):
    """Build the parser for the 'reset' subcommand."""
    reset_parser = subparsers.add_parser("reset", help="Reset database")
    reset_parser.add_argument(
        "--force", "-f",
        action="store_true",
        help="Skip confirmation prompt",
    )
    reset_parser.add_argument(
        "--seed", "-s",
        dest="seed_target",
        metavar="target",
        nargs="?",
        const=SeedTarget.ALL,
        type=SeedTarget,
        choices=list(SeedTarget),
        help="Seed after reset (optionally specify target)"
    )
    return reset_parser
