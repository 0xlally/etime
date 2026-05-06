"""add quick start templates

Revision ID: 20260506_add_quick_start_templates
Revises: 20260506_add_groups
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_add_quick_start_templates"
down_revision = "20260506_add_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "quick_start_templates",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("category_id", sa.Integer(), nullable=False),
        sa.Column("duration_seconds", sa.Integer(), nullable=True),
        sa.Column("note_template", sa.String(length=500), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("color", sa.String(length=7), nullable=True),
        sa.Column("icon", sa.String(length=50), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_quick_start_templates_category_id"), "quick_start_templates", ["category_id"], unique=False)
    op.create_index(op.f("ix_quick_start_templates_id"), "quick_start_templates", ["id"], unique=False)
    op.create_index(op.f("ix_quick_start_templates_user_id"), "quick_start_templates", ["user_id"], unique=False)
    op.create_index("ix_quick_start_templates_user_sort", "quick_start_templates", ["user_id", "sort_order"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_quick_start_templates_user_sort", table_name="quick_start_templates")
    op.drop_index(op.f("ix_quick_start_templates_user_id"), table_name="quick_start_templates")
    op.drop_index(op.f("ix_quick_start_templates_id"), table_name="quick_start_templates")
    op.drop_index(op.f("ix_quick_start_templates_category_id"), table_name="quick_start_templates")
    op.drop_table("quick_start_templates")
