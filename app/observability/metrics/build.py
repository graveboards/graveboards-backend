import os
from prometheus_client import Gauge

from app.version import __version__

graveboards_build_info = Gauge(
    "graveboards_build_info",
    "Build information for the Graveboards backend. Always 1; labels identify the version.",
    ["version", "commit"],
)


def get_commit_hash() -> str:
    """Return the git commit baked into the image at build time.

    Set via the GIT_COMMIT build arg (see Dockerfile); the running
    container has no .git directory and no git binary to introspect.
    """
    return os.environ.get("GIT_COMMIT", "unknown")


def set_build_info() -> tuple[str, str]:
    """Record build info as a metric and return (version, commit)."""
    commit = get_commit_hash()
    graveboards_build_info.labels(version=__version__, commit=commit).set(1)
    return __version__, commit
