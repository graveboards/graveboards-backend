from enum import Enum
from typing import Literal

ScopeLiteral = Literal["beatmaps", "beatmapsets", "scores", "queues", "requests"]


class Scope(Enum):
    """Top-level search scope.

    Represents the primary resource type targeted by a query.
    """
    BEATMAPS = "beatmaps"
    BEATMAPSETS = "beatmapsets"
    SCORES = "scores"
    QUEUES = "queues"
    REQUESTS = "requests"

    @classmethod
    def from_name(cls, name: str) -> "Scope":
        """Resolve a scope from its string name.

        Args:
            name:
                Case-insensitive scope name.

        Returns:
            Matching ``Scope``.

        Raises:
            ValueError:
                If no matching scope exists.
        """
        for member_name, member in cls.__members__.items():
            if name.upper() == member_name:
                return member

        raise ValueError(f"No Scope exists by the name of '{name}'")
