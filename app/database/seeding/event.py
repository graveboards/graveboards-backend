from dataclasses import dataclass
from .target import SeederTarget


@dataclass(slots=True)
class SeedEvent:
    """Progress event emitted during seeding.

    Attributes:
        target:
            ``SeederTarget`` currently being processed.
        current:
            Number of items processed so far.
        total_items:
            Total items expected for this target.
    """

    target: SeederTarget
    current: int
    total_items: int
