import subprocess
from pathlib import Path

from app.config import PROJECT_ROOT
from app.logging import get_logger


def run_migrations() -> None:
    """Run all pending Alembic migrations."""
    logger = get_logger(__name__)

    before = current()
    logger.info(f"Running migrations (current revision: {before or 'none'})")

    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )

    # Alembic's own logger (configured in alembic.ini) writes each
    # "Running upgrade x -> y" step to stderr regardless of exit code.
    for line in result.stderr.splitlines():
        if line.strip():
            logger.info(f"[alembic] {line}")

    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")

    after = current()
    if after == before:
        logger.info(f"No pending migrations (current revision: {after or 'none'})")
    else:
        logger.info(f"Migrations applied; now at revision: {after or 'none'}")


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
