"""Initial schema from SQLAlchemy models

Revision ID: 4f8e2a1c9d30
Revises:
Create Date: 2026-07-17 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4f8e2a1c9d30'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # --- Tables with no FK dependencies on other app tables ---

    op.create_table(
        'roles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_roles')),
        sa.UniqueConstraint('name', name=op.f('uq_roles_name')),
    )

    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), nullable=False),
        sa.Column('user_id', sa.Integer()),
        sa.Column('action', sa.String(100), nullable=False),
        sa.Column('entity_type', sa.String(50)),
        sa.Column('entity_id', sa.String(100)),
        sa.Column('details', sa.JSON()),
        sa.Column('ip_address', sa.String(45)),
        sa.Column('user_agent', sa.Text()),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_audit_logs')),
    )
    op.create_index('idx_audit_timestamp', 'audit_logs', [sa.text('timestamp DESC')])
    op.create_index('idx_audit_action', 'audit_logs', ['action'])
    op.create_index('idx_audit_entity', 'audit_logs', ['entity_type', 'entity_id'])

    op.create_table(
        'beatmap_tags',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('ruleset_id', sa.Integer()),
        sa.Column('description', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmap_tags')),
    )

    op.create_table(
        'beatmapset_tags',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmapset_tags')),
        sa.UniqueConstraint('name', name=op.f('uq_beatmapset_tags_name')),
    )

    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_users')),
    )

    # --- Tables depending on users, roles ---

    op.create_table(
        'profiles',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_restricted', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('account_history', sa.JSON()),
        sa.Column('active_tournament_banners', sa.JSON()),
        sa.Column('avatar_url', sa.String()),
        sa.Column('badges', sa.JSON()),
        sa.Column('beatmap_playcounts_count', sa.Integer()),
        sa.Column('comments_count', sa.Integer()),
        sa.Column('country_code', sa.String(2)),
        sa.Column('country', sa.JSON()),
        sa.Column('cover', sa.JSON()),
        sa.Column('daily_challenge_user_stats', sa.JSON()),
        sa.Column('default_group', sa.String()),
        sa.Column('discord', sa.String()),
        sa.Column('favourite_beatmapset_count', sa.Integer()),
        sa.Column('follower_count', sa.Integer()),
        sa.Column('graveyard_beatmapset_count', sa.Integer()),
        sa.Column('groups', sa.JSON()),
        sa.Column('guest_beatmapset_count', sa.Integer()),
        sa.Column('has_supported', sa.Boolean()),
        sa.Column('interests', sa.String()),
        sa.Column('is_active', sa.Boolean()),
        sa.Column('is_bot', sa.Boolean()),
        sa.Column('is_deleted', sa.Boolean()),
        sa.Column('is_online', sa.Boolean()),
        sa.Column('is_supporter', sa.Boolean()),
        sa.Column('join_date', sa.DateTime(timezone=True)),
        sa.Column('kudosu', sa.JSON()),
        sa.Column('location', sa.String()),
        sa.Column('last_visit', sa.DateTime(timezone=True)),
        sa.Column('loved_beatmapset_count', sa.Integer()),
        sa.Column('mapping_follower_count', sa.Integer()),
        sa.Column('matchmaking_stats', sa.JSON()),
        sa.Column('max_blocks', sa.Integer()),
        sa.Column('max_friends', sa.Integer()),
        sa.Column('monthly_playcounts', sa.JSON()),
        sa.Column('nominated_beatmapset_count', sa.Integer()),
        sa.Column('occupation', sa.String()),
        sa.Column('page', sa.JSON()),
        sa.Column('pending_beatmapset_count', sa.Integer()),
        sa.Column('playmode', sa.String()),
        sa.Column('playstyle', sa.JSON()),
        sa.Column('pm_friends_only', sa.Boolean()),
        sa.Column('post_count', sa.Integer()),
        sa.Column('previous_usernames', sa.JSON()),
        sa.Column('profile_colour', sa.String()),
        sa.Column('profile_hue', sa.Integer()),
        sa.Column('profile_order', sa.JSON()),
        sa.Column('rank_highest', sa.JSON()),
        sa.Column('rank_history', sa.JSON()),
        sa.Column('ranked_and_approved_beatmapset_count', sa.Integer()),
        sa.Column('ranked_beatmapset_count', sa.Integer()),
        sa.Column('replays_watched_counts', sa.JSON()),
        sa.Column('scores_best_count', sa.Integer()),
        sa.Column('scores_first_count', sa.Integer()),
        sa.Column('scores_pinned_count', sa.Integer()),
        sa.Column('scores_recent_count', sa.Integer()),
        sa.Column('statistics', sa.JSON()),
        sa.Column('support_level', sa.Integer()),
        sa.Column('team', sa.JSON()),
        sa.Column('title', sa.String()),
        sa.Column('title_url', sa.String()),
        sa.Column('twitter', sa.String()),
        sa.Column('user_achievements', sa.JSON()),
        sa.Column('username', sa.String()),
        sa.Column('website', sa.String()),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_profiles')),
        sa.UniqueConstraint('user_id', name=op.f('uq_profiles_user_id')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_profiles_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('hashed_key', sa.String(64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_api_keys')),
        sa.UniqueConstraint('hashed_key', name=op.f('uq_api_keys_hashed_key')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_api_keys_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('access_token_enc', sa.LargeBinary(), nullable=False),
        sa.Column('refresh_token_enc', sa.LargeBinary()),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_revoked', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_oauth_tokens')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_oauth_tokens_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'score_fetcher_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('last_fetch', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_score_fetcher_tasks')),
        sa.UniqueConstraint('user_id', name=op.f('uq_score_fetcher_tasks_user_id')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_score_fetcher_tasks_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'profile_fetcher_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('last_fetch', sa.DateTime(timezone=True)),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_profile_fetcher_tasks')),
        sa.UniqueConstraint('user_id', name=op.f('uq_profile_fetcher_tasks_user_id')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_profile_fetcher_tasks_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'user_role_association',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('role_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('user_id', 'role_id', name=op.f('pk_user_role_association')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_user_role_association_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['role_id'], ['roles.id'], name=op.f('fk_user_role_association_role_id_roles'), ondelete='CASCADE'),
    )

    # --- beatmapsets, beatmaps ---

    op.create_table(
        'beatmapsets',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmapsets')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_beatmapsets_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'beatmaps',
        sa.Column('id', sa.Integer(), autoincrement=False, nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmaps')),
        sa.ForeignKeyConstraint(['beatmapset_id'], ['beatmapsets.id'], name=op.f('fk_beatmaps_beatmapset_id_beatmapsets')),
    )

    # --- beatmap_snapshots ---

    op.create_table(
        'beatmap_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('beatmap_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('ar', sa.Float(), nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.Column('bpm', sa.Float(), nullable=False),
        sa.Column('checksum', sa.String(32), nullable=False),
        sa.Column('count_circles', sa.Integer(), nullable=False),
        sa.Column('count_sliders', sa.Integer(), nullable=False),
        sa.Column('count_spinners', sa.Integer(), nullable=False),
        sa.Column('cs', sa.Float(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('difficulty_rating', sa.Float(), nullable=False),
        sa.Column('drain', sa.Float(), nullable=False),
        sa.Column('failtimes', sa.JSON(), nullable=False),
        sa.Column('hit_length', sa.Integer(), nullable=False),
        sa.Column('is_scoreable', sa.Boolean(), nullable=False),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_combo', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('mode_int', sa.Integer(), nullable=False),
        sa.Column('passcount', sa.Integer(), nullable=False),
        sa.Column('playcount', sa.Integer(), nullable=False),
        sa.Column('ranked', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('total_length', sa.Integer(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmap_snapshots')),
        sa.UniqueConstraint('checksum', name=op.f('uq_beatmap_snapshots_checksum')),
        sa.UniqueConstraint('beatmap_id', 'snapshot_number', name=op.f('uq_beatmap_snapshots_beatmap_snapshot_number')),
        sa.ForeignKeyConstraint(['beatmap_id'], ['beatmaps.id'], name=op.f('fk_beatmap_snapshots_beatmap_id_beatmaps')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_beatmap_snapshots_user_id_users')),
    )

    # --- beatmapset_snapshots ---

    op.create_table(
        'beatmapset_snapshots',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('snapshot_number', sa.Integer(), nullable=False),
        sa.Column('snapshot_date', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('checksum', sa.String(32), nullable=False),
        sa.Column('verified', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('artist', sa.String(), nullable=False),
        sa.Column('artist_unicode', sa.String(), nullable=False),
        sa.Column('availability', sa.JSON(), nullable=False),
        sa.Column('bpm', sa.Float(), nullable=False),
        sa.Column('can_be_hyped', sa.Boolean(), nullable=False),
        sa.Column('covers', sa.JSON()),
        sa.Column('creator', sa.String(), nullable=False),
        sa.Column('current_nominations', sa.JSON(), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True)),
        sa.Column('description', sa.JSON(), nullable=False),
        sa.Column('discussion_enabled', sa.Boolean(), nullable=False),
        sa.Column('discussion_locked', sa.Boolean(), nullable=False),
        sa.Column('favourite_count', sa.Integer(), nullable=False),
        sa.Column('genre', sa.JSON()),
        sa.Column('hype', sa.JSON()),
        sa.Column('is_scoreable', sa.Boolean(), nullable=False),
        sa.Column('language', sa.JSON()),
        sa.Column('last_updated', sa.DateTime(timezone=True), nullable=False),
        sa.Column('legacy_thread_url', sa.String()),
        sa.Column('nominations_summary', sa.JSON(), nullable=False),
        sa.Column('nsfw', sa.Boolean(), nullable=False),
        sa.Column('offset', sa.Integer(), nullable=False),
        sa.Column('pack_tags', sa.ARRAY(sa.String()), nullable=False),
        sa.Column('play_count', sa.Integer(), nullable=False),
        sa.Column('preview_url', sa.String(), nullable=False),
        sa.Column('ranked', sa.Integer(), nullable=False),
        sa.Column('ranked_date', sa.DateTime(timezone=True)),
        sa.Column('rating', sa.Float(), nullable=False),
        sa.Column('ratings', sa.ARRAY(sa.Integer()), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('spotlight', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('storyboard', sa.Boolean(), nullable=False),
        sa.Column('submitted_date', sa.DateTime(timezone=True)),
        sa.Column('tags', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('title_unicode', sa.String(), nullable=False),
        sa.Column('track_id', sa.Integer()),
        sa.Column('video', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmapset_snapshots')),
        sa.UniqueConstraint('checksum', name=op.f('uq_beatmapset_snapshots_checksum')),
        sa.UniqueConstraint('beatmapset_id', 'snapshot_number', name=op.f('uq_beatmapset_snapshots_beatmapset_snapshot_number')),
        sa.ForeignKeyConstraint(['beatmapset_id'], ['beatmapsets.id'], name=op.f('fk_beatmapset_snapshots_beatmapset_id_beatmapsets'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_beatmapset_snapshots_user_id_users'), ondelete='CASCADE'),
    )

    # --- association tables ---

    op.create_table(
        'beatmap_snapshot_beatmapset_snapshot_association',
        sa.Column('beatmap_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_snapshot_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('beatmap_snapshot_id', 'beatmapset_snapshot_id', name=op.f('pk_beatmap_snapshot_beatmapset_snapshot_association')),
        sa.ForeignKeyConstraint(['beatmap_snapshot_id'], ['beatmap_snapshots.id'], name=op.f('fk_beatmap_snapshot_beatmapset_snapshot_association_beatmap_snapshot_id_beatmap_snapshots')),
        sa.ForeignKeyConstraint(['beatmapset_snapshot_id'], ['beatmapset_snapshots.id'], name=op.f('fk_beatmap_snapshot_beatmapset_snapshot_association_beatmapset_snapshot_id_beatmapset_snapshots')),
    )

    op.create_table(
        'beatmapset_tag_beatmapset_snapshot_association',
        sa.Column('beatmapset_tag_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_snapshot_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('beatmapset_tag_id', 'beatmapset_snapshot_id', name=op.f('pk_beatmapset_tag_beatmapset_snapshot_association')),
        sa.ForeignKeyConstraint(['beatmapset_tag_id'], ['beatmapset_tags.id'], name=op.f('fk_beatmapset_tag_beatmapset_snapshot_association_beatmapset_tag_id_beatmapset_tags'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmapset_snapshot_id'], ['beatmapset_snapshots.id'], name=op.f('fk_beatmapset_tag_beatmapset_snapshot_association_beatmapset_snapshot_id_beatmapset_snapshots'), ondelete='CASCADE'),
    )

    op.create_table(
        'beatmap_tag_beatmap_snapshot_association',
        sa.Column('beatmap_tag_id', sa.Integer(), nullable=False),
        sa.Column('beatmap_snapshot_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('beatmap_tag_id', 'beatmap_snapshot_id', name=op.f('pk_beatmap_tag_beatmap_snapshot_association')),
        sa.ForeignKeyConstraint(['beatmap_tag_id'], ['beatmap_tags.id'], name=op.f('fk_beatmap_tag_beatmap_snapshot_association_beatmap_tag_id_beatmap_tags'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmap_snapshot_id'], ['beatmap_snapshots.id'], name=op.f('fk_beatmap_tag_beatmap_snapshot_association_beatmap_snapshot_id_beatmap_snapshots'), ondelete='CASCADE'),
    )

    op.create_table(
        'beatmap_snapshot_owner_association',
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('beatmap_snapshot_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('profile_id', 'beatmap_snapshot_id', name=op.f('pk_beatmap_snapshot_owner_association')),
        sa.ForeignKeyConstraint(['profile_id'], ['profiles.id'], name=op.f('fk_beatmap_snapshot_owner_association_profile_id_profiles'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmap_snapshot_id'], ['beatmap_snapshots.id'], name=op.f('fk_beatmap_snapshot_owner_association_beatmap_snapshot_id_beatmap_snapshots'), ondelete='CASCADE'),
    )

    # --- listings, leaderboards, scores ---

    op.create_table(
        'beatmap_listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('beatmap_id', sa.Integer(), nullable=False),
        sa.Column('beatmap_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmap_listings')),
        sa.UniqueConstraint('beatmap_id', name=op.f('uq_beatmap_listings_beatmap_id')),
        sa.UniqueConstraint('beatmap_snapshot_id', name=op.f('uq_beatmap_listings_beatmap_snapshot_id')),
        sa.ForeignKeyConstraint(['beatmap_id'], ['beatmaps.id'], name=op.f('fk_beatmap_listings_beatmap_id_beatmaps')),
        sa.ForeignKeyConstraint(['beatmap_snapshot_id'], ['beatmap_snapshots.id'], name=op.f('fk_beatmap_listings_beatmap_snapshot_id_beatmap_snapshots')),
    )

    op.create_table(
        'beatmapset_listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_beatmapset_listings')),
        sa.UniqueConstraint('beatmapset_id', name=op.f('uq_beatmapset_listings_beatmapset_id')),
        sa.UniqueConstraint('beatmapset_snapshot_id', name=op.f('uq_beatmapset_listings_beatmapset_snapshot_id')),
        sa.ForeignKeyConstraint(['beatmapset_id'], ['beatmapsets.id'], name=op.f('fk_beatmapset_listings_beatmapset_id_beatmapsets'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmapset_snapshot_id'], ['beatmapset_snapshots.id'], name=op.f('fk_beatmapset_listings_beatmapset_snapshot_id_beatmapset_snapshots'), ondelete='CASCADE'),
    )

    op.create_table(
        'leaderboards',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('beatmap_id', sa.Integer(), nullable=False),
        sa.Column('beatmap_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('frozen', sa.Boolean(), server_default=sa.text('false')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_leaderboards')),
        sa.UniqueConstraint('beatmap_snapshot_id', name=op.f('uq_leaderboards_beatmap_snapshot_id')),
        sa.ForeignKeyConstraint(['beatmap_id'], ['beatmaps.id'], name=op.f('fk_leaderboards_beatmap_id_beatmaps')),
        sa.ForeignKeyConstraint(['beatmap_snapshot_id'], ['beatmap_snapshots.id'], name=op.f('fk_leaderboards_beatmap_snapshot_id_beatmap_snapshots')),
    )

    op.create_table(
        'scores',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('beatmap_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.Column('leaderboard_id', sa.Integer(), nullable=False),
        sa.Column('accuracy', sa.Float(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('max_combo', sa.Integer(), nullable=False),
        sa.Column('mode', sa.String(), nullable=False),
        sa.Column('mode_int', sa.Integer(), nullable=False),
        sa.Column('mods', sa.JSON(), nullable=False),
        sa.Column('perfect', sa.Boolean(), nullable=False),
        sa.Column('pp', sa.Float()),
        sa.Column('rank', sa.String(), nullable=False),
        sa.Column('score', sa.Integer(), nullable=False),
        sa.Column('statistics', sa.JSON(), nullable=False),
        sa.Column('type', sa.String(), nullable=False),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_scores')),
        sa.UniqueConstraint('user_id', 'beatmap_id', 'created_at', name=op.f('uq_scores_user_beatmap_created_at')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_scores_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmap_id'], ['beatmaps.id'], name=op.f('fk_scores_beatmap_id_beatmaps')),
        sa.ForeignKeyConstraint(['beatmapset_id'], ['beatmapsets.id'], name=op.f('fk_scores_beatmapset_id_beatmapsets')),
        sa.ForeignKeyConstraint(['leaderboard_id'], ['leaderboards.id'], name=op.f('fk_scores_leaderboard_id_leaderboards')),
    )

    # --- queues, queue_rules, requests ---

    op.create_table(
        'queues',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('is_open', sa.Boolean(), server_default=sa.text('true')),
        sa.Column('visibility', sa.Integer(), server_default=sa.text('0')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_queues')),
        sa.UniqueConstraint('user_id', 'name', name=op.f('uq_queues_user_id_name')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_queues_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'queue_manager_association',
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint('queue_id', 'user_id', name=op.f('pk_queue_manager_association')),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], name=op.f('fk_queue_manager_association_queue_id_queues'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_queue_manager_association_user_id_users'), ondelete='CASCADE'),
    )

    op.create_table(
        'queue_rules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('config', sa.JSON(), server_default="{}", nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_public', sa.Boolean(), nullable=False),
        sa.Column('version', sa.String(10), server_default=sa.text("'1.0'")),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_queue_rules')),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], name=op.f('fk_queue_rules_queue_id_queues'), ondelete='CASCADE'),
    )

    op.create_table(
        'requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_id', sa.Integer(), nullable=False),
        sa.Column('beatmapset_snapshot_id', sa.Integer(), nullable=False),
        sa.Column('queue_id', sa.Integer(), nullable=False),
        sa.Column('comment', sa.Text()),
        sa.Column('mv_checked', sa.Boolean(), server_default=sa.text('false')),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('status', sa.Integer(), server_default=sa.text('0')),
        sa.Column('rejection_reason', sa.Text()),
        sa.PrimaryKeyConstraint('id', name=op.f('pk_requests')),
        sa.UniqueConstraint('beatmapset_id', 'queue_id', name=op.f('uq_requests_beatmapset_id_queue_id')),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name=op.f('fk_requests_user_id_users'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmapset_id'], ['beatmapsets.id'], name=op.f('fk_requests_beatmapset_id_beatmapsets'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['beatmapset_snapshot_id'], ['beatmapset_snapshots.id'], name=op.f('fk_requests_beatmapset_snapshot_id_beatmapset_snapshots'), ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['queue_id'], ['queues.id'], name=op.f('fk_requests_queue_id_queues'), ondelete='CASCADE'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('requests')
    op.drop_table('queue_rules')
    op.drop_table('queue_manager_association')
    op.drop_table('queues')
    op.drop_table('scores')
    op.drop_table('leaderboards')
    op.drop_table('beatmapset_listings')
    op.drop_table('beatmap_listings')
    op.drop_table('beatmap_snapshot_owner_association')
    op.drop_table('beatmap_tag_beatmap_snapshot_association')
    op.drop_table('beatmapset_tag_beatmapset_snapshot_association')
    op.drop_table('beatmap_snapshot_beatmapset_snapshot_association')
    op.drop_table('beatmapset_snapshots')
    op.drop_table('beatmap_snapshots')
    op.drop_table('beatmaps')
    op.drop_table('beatmapsets')
    op.drop_table('user_role_association')
    op.drop_table('profile_fetcher_tasks')
    op.drop_table('score_fetcher_tasks')
    op.drop_table('oauth_tokens')
    op.drop_table('api_keys')
    op.drop_table('profiles')
    op.drop_table('users')
    op.drop_table('beatmapset_tags')
    op.drop_table('beatmap_tags')
    op.drop_table('audit_logs')
    op.drop_table('roles')
