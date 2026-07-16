import subprocess
from pathlib import Path

from app.config import PROJECT_ROOT


def run_migrations() -> None:
    """Run all pending Alembic migrations."""
    result = subprocess.run(
        ["alembic", "upgrade", "head"],
        cwd=str(PROJECT_ROOT),
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Alembic migration failed: {result.stderr}")


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
