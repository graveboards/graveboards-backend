import argparse
import logging

from app.database.status import STATUS_TARGETS
from app.database.seeding import SeedTarget
from app.logging import setup_logging
from .status import cmd_status
from .reset import cmd_reset
from .seed import cmd_seed


async def main():
    setup_logging(
        enabled_loggers=["manage", "database"],
        level_overrides={"database": logging.WARNING},
        no_debug=True
    )

    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)

    status_parser = subparsers.add_parser("status", help="View database status")
    status_parser.add_argument(
        "target",
        metavar="target",
        nargs="?",
        default="summary",
        choices=STATUS_TARGETS,
        help=f"What to show status for ({", ".join(STATUS_TARGETS)})"
    )

    reset_parser = subparsers.add_parser("reset", help="Reset database")
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

    seed_parser = subparsers.add_parser("seed", help="Seed database")
    seed_parser.add_argument(
        "target",
        metavar="target",
        type=SeedTarget,
        choices=list(SeedTarget),
        default=SeedTarget.ALL,
        help=f"What to seed in the database ({", ".join(SeedTarget)})"
    )

    args = parser.parse_args()

    match args.command:
        case "status":
            await cmd_status(args.target)
        case "reset":
            await cmd_reset(args.seed_target)
        case "seed":
            await cmd_seed(args.target)
