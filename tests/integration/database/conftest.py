"""
Comprehensive tests for _resolve_or_create with complex beatmap/beatmapset/snapshot relationships.

These tests exercise the full cascade of nested relationships:
- User -> Beatmapset (FK)
- Beatmapset -> Beatmap (1:N)
- Beatmapset -> BeatmapsetSnapshot (1:N)
- Beatmap -> BeatmapSnapshot (1:N)
- BeatmapSnapshot <-> BeatmapsetSnapshot (M2M via association table)
- BeatmapsetSnapshot -> Profile (via user_id)
- BeatmapSnapshot -> BeatmapTag (M2M)
- BeatmapSnapshot -> Profile (M2M via owner_profiles)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from app.database.db import PostgresqlDB


@pytest.fixture
def db() -> PostgresqlDB:
    from app.database.db import PostgresqlDB

    return PostgresqlDB()
