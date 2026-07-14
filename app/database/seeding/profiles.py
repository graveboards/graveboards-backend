"""Seeding profiles for configuring default fixture counts.

Profiles define the default counts for fetching/generating fixtures,
making it easy to adjust defaults in one place.

Usage:
    from app.database.seeding.profiles import SeedProfile, get_profile
    
    profile = get_profile("default")
    print(profile.beatmapsets_count)  # 30
"""
from dataclasses import dataclass
from typing import Literal


@dataclass(frozen=True)
class SeedProfile:
    """Defines default counts for seeding operations."""
    name: str
    beatmapsets_count: int = 30
    users_per_ruleset: int = 0  # Fetched from beatmapset owners, not random
    queue_count: int = 10
    request_count: int = 100
    
    def __repr__(self) -> str:
        return (
            f"SeedProfile(name={self.name!r}, "
            f"beatmapsets={self.beatmapsets_count}, "
            f"queues={self.queue_count}, "
            f"requests={self.request_count})"
        )


# Built-in profiles
PROFILES: dict[str, SeedProfile] = {
    "default": SeedProfile(
        name="default",
        beatmapsets_count=30,
        queue_count=10,
        request_count=100,
    ),
    "minimal": SeedProfile(
        name="minimal",
        beatmapsets_count=10,
        queue_count=5,
        request_count=25,
    ),
    "comprehensive": SeedProfile(
        name="comprehensive",
        beatmapsets_count=100,
        queue_count=30,
        request_count=300,
    ),
}


def get_profile(name: str) -> SeedProfile:
    """Get a profile by name, or raise KeyError if not found."""
    if name not in PROFILES:
        available = ", ".join(PROFILES.keys())
        raise KeyError(
            f"Unknown profile {name!r}. Available profiles: {available}"
        )
    return PROFILES[name]


def list_profiles() -> list[str]:
    """List all available profile names."""
    return list(PROFILES.keys())
