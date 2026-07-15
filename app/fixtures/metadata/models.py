"""Typed metadata models for fixture tracking."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class SampleCount:
    """Sample count tracking for a single category."""

    count: int = 0
    last_fetched: Optional[str] = None


@dataclass
class UsersSample:
    """Sample counts for users, broken down by ruleset."""

    count: int = 0
    per_ruleset: dict[str, int] = field(
        default_factory=lambda: {"osu": 0, "taiko": 0, "fruits": 0, "mania": 0}
    )
    last_fetched: Optional[str] = None


@dataclass
class ScoresSample:
    """Sample counts for scores, broken down by type."""

    count: int = 0
    per_type: dict[str, int] = field(default_factory=lambda: {"best": 0, "firsts": 0, "recent": 0})
    last_fetched: Optional[str] = None


@dataclass
class Samples:
    """All sample count tracking."""

    beatmaps: SampleCount = field(default_factory=SampleCount)
    beatmapsets: SampleCount = field(default_factory=SampleCount)
    users: UsersSample = field(default_factory=UsersSample)
    scores: ScoresSample = field(default_factory=ScoresSample)
    beatmap_scores: SampleCount = field(default_factory=SampleCount)
    beatmap_attributes: SampleCount = field(default_factory=SampleCount)
    queues: SampleCount = field(default_factory=SampleCount)
    requests: SampleCount = field(default_factory=SampleCount)

    def to_dict(self) -> dict:
        """Convert to dictionary format for JSON serialization."""
        return {
            "beatmaps": {"count": self.beatmaps.count, "last_fetched": self.beatmaps.last_fetched},
            "beatmapsets": {
                "count": self.beatmapsets.count,
                "last_fetched": self.beatmapsets.last_fetched,
            },
            "users": {
                "count": self.users.count,
                "per_ruleset": self.users.per_ruleset,
                "last_fetched": self.users.last_fetched,
            },
            "scores": {
                "count": self.scores.count,
                "per_type": self.scores.per_type,
                "last_fetched": self.scores.last_fetched,
            },
            "beatmap_scores": {
                "count": self.beatmap_scores.count,
                "last_fetched": self.beatmap_scores.last_fetched,
            },
            "beatmap_attributes": {
                "count": self.beatmap_attributes.count,
                "last_fetched": self.beatmap_attributes.last_fetched,
            },
            "queues": {"count": self.queues.count, "last_fetched": self.queues.last_fetched},
            "requests": {"count": self.requests.count, "last_fetched": self.requests.last_fetched},
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Samples":
        """Create from dictionary format."""
        if not data:
            return cls()
        return cls(
            beatmaps=SampleCount(**data.get("beatmaps", {})),
            beatmapsets=SampleCount(**data.get("beatmapsets", {})),
            users=UsersSample(**data.get("users", {})),
            scores=ScoresSample(**data.get("scores", {})),
            beatmap_scores=SampleCount(**data.get("beatmap_scores", {})),
            beatmap_attributes=SampleCount(**data.get("beatmap_attributes", {})),
            queues=SampleCount(**data.get("queues", {})),
            requests=SampleCount(**data.get("requests", {})),
        )


@dataclass
class PromotedFixture:
    """Promotion tracking for a single category."""

    count: int = 0
    last_promoted: Optional[str] = None


@dataclass
class PromotedUsers:
    """Promotion tracking for users."""

    count: int = 0
    per_ruleset: dict[str, int] = field(
        default_factory=lambda: {"osu": 0, "taiko": 0, "fruits": 0, "mania": 0}
    )
    last_promoted: Optional[str] = None


@dataclass
class PromotedScores:
    """Promotion tracking for scores."""

    count: int = 0
    per_type: dict[str, int] = field(default_factory=lambda: {"best": 0, "firsts": 0, "recent": 0})
    last_promoted: Optional[str] = None


@dataclass
class PromotedFixtures:
    """All promotion tracking."""

    beatmaps: PromotedFixture = field(default_factory=PromotedFixture)
    beatmapsets: PromotedFixture = field(default_factory=PromotedFixture)
    users: PromotedUsers = field(default_factory=PromotedUsers)
    scores: PromotedScores = field(default_factory=PromotedScores)
    beatmap_scores: PromotedFixture = field(default_factory=PromotedFixture)
    beatmap_attributes: PromotedFixture = field(default_factory=PromotedFixture)
    queues: PromotedFixture = field(default_factory=PromotedFixture)
    requests: PromotedFixture = field(default_factory=PromotedFixture)

    def to_dict(self) -> dict:
        """Convert to dictionary format for JSON serialization."""
        return {
            "beatmaps": {
                "count": self.beatmaps.count,
                "last_promoted": self.beatmaps.last_promoted,
            },
            "beatmapsets": {
                "count": self.beatmapsets.count,
                "last_promoted": self.beatmapsets.last_promoted,
            },
            "users": {
                "count": self.users.count,
                "per_ruleset": self.users.per_ruleset,
                "last_promoted": self.users.last_promoted,
            },
            "scores": {
                "count": self.scores.count,
                "per_type": self.scores.per_type,
                "last_promoted": self.scores.last_promoted,
            },
            "beatmap_scores": {
                "count": self.beatmap_scores.count,
                "last_promoted": self.beatmap_scores.last_promoted,
            },
            "beatmap_attributes": {
                "count": self.beatmap_attributes.count,
                "last_promoted": self.beatmap_attributes.last_promoted,
            },
            "queues": {"count": self.queues.count, "last_promoted": self.queues.last_promoted},
            "requests": {
                "count": self.requests.count,
                "last_promoted": self.requests.last_promoted,
            },
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PromotedFixtures":
        """Create from dictionary format."""
        if not data:
            return cls()
        return cls(
            beatmaps=PromotedFixture(**data.get("beatmaps", {})),
            beatmapsets=PromotedFixture(**data.get("beatmapsets", {})),
            users=PromotedUsers(**data.get("users", {})),
            scores=PromotedScores(**data.get("scores", {})),
            beatmap_scores=PromotedFixture(**data.get("beatmap_scores", {})),
            beatmap_attributes=PromotedFixture(**data.get("beatmap_attributes", {})),
            queues=PromotedFixture(**data.get("queues", {})),
            requests=PromotedFixture(**data.get("requests", {})),
        )


@dataclass
class TargetedFileMetadata:
    """Metadata for a single targeted fixture file."""

    filepath: str = ""
    fetched_at: Optional[str] = None
    # Optional fields depending on type
    status: Optional[str] = None
    ruleset: Optional[str] = None
    difficulty_rating: Optional[float] = None
    playcount: Optional[int] = None
    activity_level: Optional[str] = None
    rank: Optional[str] = None
    mods: list[int] = field(default_factory=list)
    visibility: Optional[int] = None
    is_open: Optional[bool] = None
    mv_checked: Optional[bool] = None


@dataclass
class TargetedMetadata:
    """Targeted fixture metadata with coverage tracking."""

    beatmaps: dict = field(
        default_factory=lambda: {
            "by_status": {},
            "by_ruleset": {},
            "by_difficulty": {},
            "by_playcount": {},
            "file_metadata": {},
        }
    )
    beatmapsets: dict = field(default_factory=lambda: {"by_status": {}, "file_metadata": {}})
    users: dict = field(
        default_factory=lambda: {"by_activity": {}, "per_ruleset": {}, "file_metadata": {}}
    )
    scores: dict = field(
        default_factory=lambda: {"by_rank": {}, "by_mods": {}, "file_metadata": {}}
    )
    queues: dict = field(
        default_factory=lambda: {"by_visibility": {}, "by_is_open": {}, "file_metadata": {}}
    )
    requests: dict = field(
        default_factory=lambda: {"by_status": {}, "by_mv_checked": {}, "file_metadata": {}}
    )

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "beatmaps": self.beatmaps,
            "beatmapsets": self.beatmapsets,
            "users": self.users,
            "scores": self.scores,
            "queues": self.queues,
            "requests": self.requests,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TargetedMetadata":
        """Create from dictionary format."""
        if not data:
            return cls()
        return cls(
            beatmaps=data.get("beatmaps", {}),
            beatmapsets=data.get("beatmapsets", {}),
            users=data.get("users", {}),
            scores=data.get("scores", {}),
            queues=data.get("queues", {}),
            requests=data.get("requests", {}),
        )


@dataclass
class SearchTestCoverage:
    """Search test coverage tracking."""

    beatmapset_genres: list[int] = field(default_factory=list)
    beatmapset_languages: list[int] = field(default_factory=list)
    beatmapset_nsfw_true_ids: list[int] = field(default_factory=list)
    beatmapset_nsfw_false_ids: list[int] = field(default_factory=list)
    beatmapset_statuses: list[str] = field(default_factory=list)
    beatmapset_titles: list[str] = field(default_factory=list)
    beatmapset_artists: list[str] = field(default_factory=list)
    beatmapset_creators: list[str] = field(default_factory=list)
    beatmapset_sources: list[str] = field(default_factory=list)
    beatmapset_tags: list[str] = field(default_factory=list)
    beatmap_modes: list[int] = field(default_factory=list)
    beatmap_statuses: list[str] = field(default_factory=list)
    beatmap_difficulties: dict[str, list[int]] = field(default_factory=dict)
    beatmap_playcounts: dict[str, list[int]] = field(default_factory=dict)
    beatmap_versions: list[str] = field(default_factory=list)
    beatmap_bpm: dict[str, list[int]] = field(default_factory=dict)
    beatmap_accuracy: dict[str, list[int]] = field(default_factory=dict)
    beatmap_hit_lengths: dict[str, list[int]] = field(default_factory=dict)
    beatmap_max_combos: dict[str, list[int]] = field(default_factory=dict)
    beatmap_drain: dict[str, list[int]] = field(default_factory=dict)
    beatmap_ar: dict[str, list[int]] = field(default_factory=dict)
    beatmap_cs: dict[str, list[int]] = field(default_factory=dict)
    country_codes: list[str] = field(default_factory=list)
    restricted_users: dict[str, list[int]] = field(
        default_factory=lambda: {"true_ids": [], "false_ids": []}
    )
    last_updated: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary format."""
        return {
            "beatmapset_genres": self.beatmapset_genres,
            "beatmapset_languages": self.beatmapset_languages,
            "beatmapset_nsfw_true_ids": self.beatmapset_nsfw_true_ids,
            "beatmapset_nsfw_false_ids": self.beatmapset_nsfw_false_ids,
            "beatmapset_statuses": self.beatmapset_statuses,
            "beatmapset_titles": self.beatmapset_titles,
            "beatmapset_artists": self.beatmapset_artists,
            "beatmapset_creators": self.beatmapset_creators,
            "beatmapset_sources": self.beatmapset_sources,
            "beatmapset_tags": self.beatmapset_tags,
            "beatmap_modes": self.beatmap_modes,
            "beatmap_statuses": self.beatmap_statuses,
            "beatmap_difficulties": self.beatmap_difficulties,
            "beatmap_playcounts": self.beatmap_playcounts,
            "beatmap_versions": self.beatmap_versions,
            "beatmap_bpm": self.beatmap_bpm,
            "beatmap_accuracy": self.beatmap_accuracy,
            "beatmap_hit_lengths": self.beatmap_hit_lengths,
            "beatmap_max_combos": self.beatmap_max_combos,
            "beatmap_drain": self.beatmap_drain,
            "beatmap_ar": self.beatmap_ar,
            "beatmap_cs": self.beatmap_cs,
            "country_codes": self.country_codes,
            "restricted_users": self.restricted_users,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "SearchTestCoverage":
        """Create from dictionary format."""
        if not data:
            return cls()
        return cls(
            beatmapset_genres=data.get("beatmapset_genres", []),
            beatmapset_languages=data.get("beatmapset_languages", []),
            beatmapset_nsfw_true_ids=data.get("beatmapset_nsfw_true_ids", []),
            beatmapset_nsfw_false_ids=data.get("beatmapset_nsfw_false_ids", []),
            beatmapset_statuses=data.get("beatmapset_statuses", []),
            beatmapset_titles=data.get("beatmapset_titles", []),
            beatmapset_artists=data.get("beatmapset_artists", []),
            beatmapset_creators=data.get("beatmapset_creators", []),
            beatmapset_sources=data.get("beatmapset_sources", []),
            beatmapset_tags=data.get("beatmapset_tags", []),
            beatmap_modes=data.get("beatmap_modes", []),
            beatmap_statuses=data.get("beatmap_statuses", []),
            beatmap_difficulties=data.get("beatmap_difficulties", {}),
            beatmap_playcounts=data.get("beatmap_playcounts", {}),
            beatmap_versions=data.get("beatmap_versions", []),
            beatmap_bpm=data.get("beatmap_bpm", {}),
            beatmap_accuracy=data.get("beatmap_accuracy", {}),
            beatmap_hit_lengths=data.get("beatmap_hit_lengths", {}),
            beatmap_max_combos=data.get("beatmap_max_combos", {}),
            beatmap_drain=data.get("beatmap_drain", {}),
            beatmap_ar=data.get("beatmap_ar", {}),
            beatmap_cs=data.get("beatmap_cs", {}),
            country_codes=data.get("country_codes", []),
            restricted_users=data.get("restricted_users", {"true_ids": [], "false_ids": []}),
            last_updated=data.get("last_updated"),
        )


@dataclass
class Metadata:
    """Top-level metadata container with all sections."""

    last_updated: Optional[str] = None
    samples: Samples = field(default_factory=Samples)
    promoted_fixtures: PromotedFixtures = field(default_factory=PromotedFixtures)
    targeted: TargetedMetadata = field(default_factory=TargetedMetadata)
    search_test_coverage: SearchTestCoverage = field(default_factory=SearchTestCoverage)
    failed_ids: dict = field(
        default_factory=lambda: {
            "beatmaps": [],
            "beatmapsets": [],
            "users": {"osu": [], "taiko": [], "fruits": [], "mania": []},
        }
    )
    top_player_ids: dict[str, list[int]] = field(
        default_factory=lambda: {"osu": [], "taiko": [], "fruits": [], "mania": []}
    )
    id_ranges: dict = field(
        default_factory=lambda: {
            "beatmaps": {"min": 1, "max": 5800000},
            "beatmapsets": {"min": 1, "max": 2600000},
            "users": {"min": 1, "max": 40000000},
        }
    )
    rulesets: list[str] = field(default_factory=lambda: ["osu", "taiko", "fruits", "mania"])
    source: str = "osu.ppy.sh/api/v2"

    def to_dict(self) -> dict:
        """Convert to dictionary format for JSON serialization."""
        return {
            "last_updated": self.last_updated,
            "samples": self.samples.to_dict(),
            "promoted_fixtures": self.promoted_fixtures.to_dict(),
            "targeted": self.targeted.to_dict(),
            "search_test_coverage": self.search_test_coverage.to_dict(),
            "failed_ids": self.failed_ids,
            "top_player_ids": self.top_player_ids,
            "id_ranges": self.id_ranges,
            "rulesets": self.rulesets,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Metadata":
        """Create from dictionary format."""
        if not data:
            return cls()
        return cls(
            last_updated=data.get("last_updated"),
            samples=Samples.from_dict(data.get("samples", {})),
            promoted_fixtures=PromotedFixtures.from_dict(data.get("promoted_fixtures", {})),
            targeted=TargetedMetadata.from_dict(data.get("targeted", {})),
            search_test_coverage=SearchTestCoverage.from_dict(data.get("search_test_coverage", {})),
            failed_ids=data.get("failed_ids", {}),
            top_player_ids=data.get("top_player_ids", {}),
            id_ranges=data.get("id_ranges", {}),
            rulesets=data.get("rulesets", []),
            source=data.get("source", "osu.ppy.sh/api/v2"),
        )
