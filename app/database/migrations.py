import subprocess
from pathlib import Path

from app.config import PROJECT_ROOT
from app.logging import get_logger


def run_migrations() -> None:
    """Run all pending Alembic migrations.

    On a fresh database (no alembic_version table) `alembic current` fails
    because there is nothing to report.  `alembic upgrade head` handles both
    cases — it creates the schema from scratch on a fresh DB and applies only
    pending migrations on an existing one — so we detect the fresh-DB case
    from the failure of `current()` and log accordingly.
    """
    logger = get_logger(__name__)

    current_result = subprocess.run(
        ["alembic", "current"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if current_result.returncode == 0 and current_result.stdout.strip():
        before = current_result.stdout.strip()
        logger.info(f"Running migrations (current revision: {before})")
    else:
        before = None
        logger.info("No existing migration state detected — running initial migrations")

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    if result.returncode != 0:
        # Don't also dump this line-by-line below - the exception's own
        # traceback is logged once, in full, by whoever catches it.
        raise RuntimeError(f"Alembic migration failed:\n{result.stderr.strip()}")

    # Alembic's own logger (configured in alembic.ini) writes each
    # "Running upgrade x -> y" step to stderr regardless of exit code. Log it
    # as one multi-line block rather than one log record per line, so it
    # reads as a single entry instead of a wall of individually timestamped
    # lines.
    output = result.stderr.strip()
    if output:
        logger.info(f"[alembic]\n{output}")

    after_result = subprocess.run(
        ["alembic", "current"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    after = after_result.stdout.strip() if after_result.returncode == 0 else "unknown"

    if before is None:
        logger.info(f"Initial migrations applied; now at revision: {after}")
    elif after == before:
        logger.info(f"No pending migrations (current revision: {after})")
    else:
        logger.info(f"Migrations applied; now at revision: {after}")


def downgrade(revision: str = "-1") -> None:
    """Rollback migrations."""
    result = subprocess.run(
        ["alembic", "downgrade", revision],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic downgrade failed: {result.stderr}")


def history() -> list[str]:
    """Return migration history."""
    result = subprocess.run(
        ["alembic", "history"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip().splitlines()


def current() -> str:
    """Return current revision."""
    result = subprocess.run(
        ["alembic", "current"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def stamp(revision: str) -> None:
    """Mark DB as current without running migrations."""
    result = subprocess.run(
        ["alembic", "stamp", revision],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic stamp failed: {result.stderr}")
