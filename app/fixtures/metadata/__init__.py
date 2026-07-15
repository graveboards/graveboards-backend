"""Metadata subpackage for typed metadata models and store."""

from .models import (
    Metadata,
    Samples,
    SampleCount,
    UsersSample,
    ScoresSample,
    PromotedFixtures,
    PromotedFixture,
    PromotedUsers,
    PromotedScores,
    TargetedMetadata,
    TargetedFileMetadata,
    SearchTestCoverage,
)
from .store import MetadataStore, FixtureMetadataManager

__all__ = [
    "Metadata",
    "Samples",
    "SampleCount",
    "UsersSample",
    "ScoresSample",
    "PromotedFixtures",
    "PromotedFixture",
    "PromotedUsers",
    "PromotedScores",
    "TargetedMetadata",
    "TargetedFileMetadata",
    "SearchTestCoverage",
    "MetadataStore",
    "FixtureMetadataManager",
]
