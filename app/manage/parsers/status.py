"""Status subcommand parser."""

from app.database.status import STATUS_TARGETS


def build_status_parser(subparsers):
    """Build the parser for the 'status' subcommand."""
    status_parser = subparsers.add_parser("status", help="View database status")
    status_parser.add_argument(
        "target",
        metavar="target",
        nargs="?",
        default="summary",
        choices=STATUS_TARGETS,
        help=f"What to show status for ({', '.join(STATUS_TARGETS)})"
    )
    return status_parser
