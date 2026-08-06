"""Metadata subpackage for typed metadata models and store."""

from __future__ import annotations

from .models import (
    Metadata,
    PromotedFixture,
    PromotedFixtures,
    PromotedScores,
    PromotedUsers,
    SampleCount,
    Samples,
    ScoresSample,
    SearchTestCoverage,
    TargetedFileMetadata,
    TargetedMetadata,
    UsersSample,
)
from .store import FixtureMetadataManager, MetadataStore

__all__ = [
    "FixtureMetadataManager",
    "Metadata",
    "MetadataStore",
    "PromotedFixture",
    "PromotedFixtures",
    "PromotedScores",
    "PromotedUsers",
    "SampleCount",
    "Samples",
    "ScoresSample",
    "SearchTestCoverage",
    "TargetedFileMetadata",
    "TargetedMetadata",
    "UsersSample",
]
