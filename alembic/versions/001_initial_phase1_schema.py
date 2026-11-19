"""Initial Phase 1 schema: users, oauth_tokens, emails, calendar, sync_states

Revision ID: 001_initial_phase1
Revises: 
Create Date: 2026-11-19 15:30:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '001_initial_phase1'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('is_owner', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. oauth_tokens table
    op.create_table(
        'oauth_tokens',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('provider', sa.String(length=50), nullable=False),
        sa.Column('encrypted_access_token', sa.Text(), nullable=False),
        sa.Column('encrypted_refresh_token', sa.Text(), nullable=True),
        sa.Column('token_uri', sa.String(length=255), nullable=False),
        sa.Column('scopes', sa.Text(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_oauth_tokens_user_id'), 'oauth_tokens', ['user_id'])
    op.create_index(op.f('ix_oauth_tokens_provider'), 'oauth_tokens', ['provider'])

    # 3. email_messages table
    op.create_table(
        'email_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('message_id', sa.String(length=128), nullable=False),
        sa.Column('thread_id', sa.String(length=128), nullable=True),
        sa.Column('sender_name', sa.String(length=255), nullable=True),
        sa.Column('sender_email', sa.String(length=255), nullable=False),
        sa.Column('recipient', sa.Text(), nullable=True),
        sa.Column('cc', sa.Text(), nullable=True),
        sa.Column('bcc', sa.Text(), nullable=True),
        sa.Column('subject', sa.Text(), nullable=True),
        sa.Column('snippet', sa.Text(), nullable=True),
        sa.Column('body_text', sa.Text(), nullable=True),
        sa.Column('body_html', sa.Text(), nullable=True),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('labels', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=64), nullable=True),
        sa.Column('is_read', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('has_attachments', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_email_messages_user_id'), 'email_messages', ['user_id'])
    op.create_index(op.f('ix_email_messages_message_id'), 'email_messages', ['message_id'])
    op.create_index(op.f('ix_email_messages_thread_id'), 'email_messages', ['thread_id'])
    op.create_index(op.f('ix_email_messages_sender_email'), 'email_messages', ['sender_email'])
    op.create_index(op.f('ix_email_messages_received_at'), 'email_messages', ['received_at'])
    op.create_index(op.f('ix_email_messages_category'), 'email_messages', ['category'])
    op.create_index('idx_user_msg_id', 'email_messages', ['user_id', 'message_id'], unique=True)
    op.create_index('idx_user_received_at', 'email_messages', ['user_id', 'received_at'])

    # 4. calendar_events table
    op.create_table(
        'calendar_events',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('event_id', sa.String(length=255), nullable=False),
        sa.Column('calendar_id', sa.String(length=255), nullable=False, server_default='primary'),
        sa.Column('summary', sa.String(length=512), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('location', sa.String(length=512), nullable=True),
        sa.Column('start_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('end_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_all_day', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('status', sa.String(length=64), nullable=False, server_default='confirmed'),
        sa.Column('organizer_email', sa.String(length=255), nullable=True),
        sa.Column('attendees', sa.Text(), nullable=True),
        sa.Column('recurrence', sa.Text(), nullable=True),
        sa.Column('html_link', sa.String(length=512), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_calendar_events_user_id'), 'calendar_events', ['user_id'])
    op.create_index(op.f('ix_calendar_events_event_id'), 'calendar_events', ['event_id'])
    op.create_index(op.f('ix_calendar_events_start_time'), 'calendar_events', ['start_time'])
    op.create_index(op.f('ix_calendar_events_end_time'), 'calendar_events', ['end_time'])
    op.create_index('idx_user_event_id', 'calendar_events', ['user_id', 'event_id'], unique=True)
    op.create_index('idx_user_event_time', 'calendar_events', ['user_id', 'start_time', 'end_time'])

    # 5. sync_states table
    op.create_table(
        'sync_states',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('service_name', sa.String(length=50), nullable=False),
        sa.Column('sync_token', sa.String(length=512), nullable=True),
        sa.Column('history_id', sa.String(length=128), nullable=True),
        sa.Column('last_sync_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_sync_completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('sync_status', sa.String(length=32), nullable=False, server_default='idle'),
        sa.Column('items_synced', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_sync_states_user_id'), 'sync_states', ['user_id'])
    op.create_index('idx_user_service', 'sync_states', ['user_id', 'service_name'], unique=True)


def downgrade() -> None:
    op.drop_table('sync_states')
    op.drop_table('calendar_events')
    op.drop_table('email_messages')
    op.drop_table('oauth_tokens')
    op.drop_table('users')
