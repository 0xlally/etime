"""add client generated id to sessions

Revision ID: 20260505_session_cgid
Revises: 20260427_add_time_traces
Create Date: 2026-05-05
"""

from alembic import op
import sqlalchemy as sa


revision = "20260505_session_cgid"
down_revision = "20260427_add_time_traces"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("sessions", sa.Column("client_generated_id", sa.String(length=100), nullable=True))
    op.create_index(
        "uq_sessions_user_client_generated_id",
        "sessions",
        ["user_id", "client_generated_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_sessions_user_client_generated_id", table_name="sessions")
    op.drop_column("sessions", "client_generated_id")
