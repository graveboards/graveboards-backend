from enum import Enum
from typing import Literal

ScopeLiteral = Literal["beatmaps", "beatmapsets", "scores", "queues", "requests"]


class Scope(Enum):
    BEATMAPS = "beatmaps"
    BEATMAPSETS = "beatmapsets"
    SCORES = "scores"
    QUEUES = "queues"
    REQUESTS = "requests"

    @classmethod
    def from_name(cls, name: str) -> "Scope":
        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No Scope exists by the name of '{name}'")
