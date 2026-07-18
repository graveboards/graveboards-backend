"""Add search performance indexes

Revision ID: 7b3d5e9f2a18
Revises: 4f8e2a1c9d30
Create Date: 2026-07-17 00:00:01.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b3d5e9f2a18'
down_revision: Union[str, Sequence[str], None] = '4f8e2a1c9d30'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_index('idx_beatmap_listings_snapshot', 'beatmap_listings', ['beatmap_snapshot_id'])
    op.create_index('idx_beatmap_snapshots_beatmap_id', 'beatmap_snapshots', ['beatmap_id'])
    op.create_index('idx_beatmapset_listings_snapshot', 'beatmapset_listings', ['beatmapset_snapshot_id'])
    op.create_index('idx_beatmapset_snapshots_beatmapset_id', 'beatmapset_snapshots', ['beatmapset_id'])
    op.create_index('idx_leaderboards_beatmap', 'leaderboards', ['beatmap_id'])
    op.create_index('idx_profiles_user_id', 'profiles', ['user_id'])
    op.create_index('idx_queue_rules_queue_active', 'queue_rules', ['queue_id', 'is_active'])
    op.create_index('idx_requests_beatmapset', 'requests', ['beatmapset_id'])
    op.create_index('idx_requests_queue_status', 'requests', ['queue_id', 'status'])
    op.create_index('idx_scores_leaderboard', 'scores', ['leaderboard_id'])
    op.create_index('idx_scores_user_beatmap', 'scores', ['user_id', 'beatmap_id'])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index('idx_scores_user_beatmap', table_name='scores')
    op.drop_index('idx_scores_leaderboard', table_name='scores')
    op.drop_index('idx_requests_queue_status', table_name='requests')
    op.drop_index('idx_requests_beatmapset', table_name='requests')
    op.drop_index('idx_queue_rules_queue_active', table_name='queue_rules')
    op.drop_index('idx_profiles_user_id', table_name='profiles')
    op.drop_index('idx_leaderboards_beatmap', table_name='leaderboards')
    op.drop_index('idx_beatmapset_snapshots_beatmapset_id', table_name='beatmapset_snapshots')
    op.drop_index('idx_beatmapset_listings_snapshot', table_name='beatmapset_listings')
    op.drop_index('idx_beatmap_snapshots_beatmap_id', table_name='beatmap_snapshots')
    op.drop_index('idx_beatmap_listings_snapshot', table_name='beatmap_listings')
