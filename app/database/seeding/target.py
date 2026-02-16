from enum import StrEnum


class SeedTarget(StrEnum):
    ALL = "all"
    USERS = "users"
    BEATMAPS = "beatmaps"
    QUEUES = "queues"
    REQUESTS = "requests"


class SeederTarget(StrEnum):
    USER = "user"
    BEATMAP = "beatmap"
    QUEUE = "queue"
    REQUEST = "request"

    @property
    def seed_title(self) -> str:
        return SEEDER_TO_CLI[self].capitalize()


CLI_TO_SEEDER: dict[SeedTarget, SeederTarget] = {
    SeedTarget.USERS: SeederTarget.USER,
    SeedTarget.BEATMAPS: SeederTarget.BEATMAP,
    SeedTarget.QUEUES: SeederTarget.QUEUE,
    SeedTarget.REQUESTS: SeederTarget.REQUEST
}

SEEDER_TO_CLI: dict[SeederTarget, SeedTarget] = {v: k for k, v in CLI_TO_SEEDER.items()}
