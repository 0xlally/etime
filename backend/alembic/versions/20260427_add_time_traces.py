"""add time traces

Revision ID: 20260427_add_time_traces
Revises: 20251224_add_session_effective
Create Date: 2026-04-27
"""

from alembic import op
import sqlalchemy as sa


revision = "20260427_add_time_traces"
down_revision = "20251224_add_session_effective"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "time_traces",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_time_traces_id"), "time_traces", ["id"], unique=False)
    op.create_index(op.f("ix_time_traces_user_id"), "time_traces", ["user_id"], unique=False)
    op.create_index(op.f("ix_time_traces_created_at"), "time_traces", ["created_at"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_time_traces_created_at"), table_name="time_traces")
    op.drop_index(op.f("ix_time_traces_user_id"), table_name="time_traces")
    op.drop_index(op.f("ix_time_traces_id"), table_name="time_traces")
    op.drop_table("time_traces")
