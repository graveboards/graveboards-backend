from dataclasses import dataclass
from .target import SeederTarget


@dataclass(slots=True)
class SeedEvent:
    target: SeederTarget
    current: int
    total_items: int
