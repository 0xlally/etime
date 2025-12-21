"""Add session time indexes

Revision ID: 004
Revises: 003
Create Date: 2025-12-21 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index('ix_sessions_start_time', 'sessions', ['start_time'], unique=False)
    op.create_index('ix_sessions_end_time', 'sessions', ['end_time'], unique=False)
    op.create_index('ix_sessions_user_start_time', 'sessions', ['user_id', 'start_time'], unique=False)


def downgrade() -> None:
    op.drop_index('ix_sessions_user_start_time', table_name='sessions')
    op.drop_index('ix_sessions_end_time', table_name='sessions')
    op.drop_index('ix_sessions_start_time', table_name='sessions')
