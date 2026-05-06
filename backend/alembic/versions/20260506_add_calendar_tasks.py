"""add calendar tasks

Revision ID: 20260506_calendar_tasks
Revises: 20260506_quick_templates
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_calendar_tasks"
down_revision = "20260506_quick_templates"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "calendar_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=160), nullable=False),
        sa.Column("description", sa.String(length=1000), nullable=True),
        sa.Column("category_id", sa.Integer(), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False),
        sa.Column("estimated_seconds", sa.Integer(), nullable=True),
        sa.Column("scheduled_start", sa.DateTime(timezone=True), nullable=True),
        sa.Column("scheduled_end", sa.DateTime(timezone=True), nullable=True),
        sa.Column("reminder_enabled", sa.Boolean(), nullable=False),
        sa.Column("reminder_minutes_before", sa.Integer(), nullable=True),
        sa.Column("reminder_fired_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("converted_session_id", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["converted_session_id"], ["sessions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_calendar_tasks_category_id"), "calendar_tasks", ["category_id"], unique=False)
    op.create_index(op.f("ix_calendar_tasks_id"), "calendar_tasks", ["id"], unique=False)
    op.create_index(op.f("ix_calendar_tasks_scheduled_start"), "calendar_tasks", ["scheduled_start"], unique=False)
    op.create_index(op.f("ix_calendar_tasks_user_id"), "calendar_tasks", ["user_id"], unique=False)
    op.create_index("ix_calendar_tasks_user_scheduled_start", "calendar_tasks", ["user_id", "scheduled_start"], unique=False)
    op.create_index("ix_calendar_tasks_user_status", "calendar_tasks", ["user_id", "status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_calendar_tasks_user_status", table_name="calendar_tasks")
    op.drop_index("ix_calendar_tasks_user_scheduled_start", table_name="calendar_tasks")
    op.drop_index(op.f("ix_calendar_tasks_user_id"), table_name="calendar_tasks")
    op.drop_index(op.f("ix_calendar_tasks_scheduled_start"), table_name="calendar_tasks")
    op.drop_index(op.f("ix_calendar_tasks_id"), table_name="calendar_tasks")
    op.drop_index(op.f("ix_calendar_tasks_category_id"), table_name="calendar_tasks")
    op.drop_table("calendar_tasks")
