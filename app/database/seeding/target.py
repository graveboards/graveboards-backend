from enum import StrEnum


class SeedTarget(StrEnum):
    """CLI-facing seed targets.

    Represents user-selectable seeding scopes.
    """
    ALL = "all"
    USERS = "users"
    BEATMAPS = "beatmaps"
    QUEUES = "queues"
    REQUESTS = "requests"


class SeederTarget(StrEnum):
    """Internal seeder targets used by the orchestration layer.

    Each member corresponds to a concrete ``Seeder`` implementation.
    """
    USER = "user"
    BEATMAP = "beatmap"
    QUEUE = "queue"
    REQUEST = "request"

    @property
    def seed_title(self) -> str:
        """Return the CLI-friendly display name for the target."""
        return SEEDER_TO_CLI[self].capitalize()


CLI_TO_SEEDER: dict[SeedTarget, SeederTarget] = {
    SeedTarget.USERS: SeederTarget.USER,
    SeedTarget.BEATMAPS: SeederTarget.BEATMAP,
    SeedTarget.QUEUES: SeederTarget.QUEUE,
    SeedTarget.REQUESTS: SeederTarget.REQUEST
}
"""Mapping from CLI ``SeedTarget`` to internal ``SeederTarget``."""

SEEDER_TO_CLI: dict[SeederTarget, SeedTarget] = {v: k for k, v in CLI_TO_SEEDER.items()}
"""Reverse mapping from internal ``SeederTarget`` to CLI ``SeedTarget``."""
