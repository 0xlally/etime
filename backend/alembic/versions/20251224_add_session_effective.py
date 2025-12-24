"""add effective seconds and multiplier to sessions

Revision ID: 20251224_add_session_effective
Revises: 005_add_target_eval_notification_tables
Create Date: 2025-12-24
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20251224_add_session_effective'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('sessions', sa.Column('effectiveness_multiplier', sa.Float(), server_default='1.0', nullable=True))
    op.add_column('sessions', sa.Column('effective_seconds', sa.Integer(), nullable=True))

    # Backfill existing rows
    op.execute(
        "UPDATE sessions SET effectiveness_multiplier = 1.0 WHERE effectiveness_multiplier IS NULL"
    )
    op.execute(
        "UPDATE sessions SET effective_seconds = duration_seconds WHERE effective_seconds IS NULL AND duration_seconds IS NOT NULL"
    )


def downgrade() -> None:
    op.drop_column('sessions', 'effective_seconds')
    op.drop_column('sessions', 'effectiveness_multiplier')
