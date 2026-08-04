"""add category sort order

Revision ID: 20260804_category_sort
Revises: 20260506_calendar_tasks
Create Date: 2026-08-04
"""

from alembic import op
import sqlalchemy as sa


revision = "20260804_category_sort"
down_revision = "20260506_calendar_tasks"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "categories",
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
    )

    connection = op.get_bind()
    rows = connection.execute(sa.text(
        "SELECT id, user_id FROM categories "
        "ORDER BY user_id ASC, created_at DESC, id DESC"
    )).fetchall()
    positions: dict[int, int] = {}
    for category_id, user_id in rows:
        position = positions.get(user_id, 0)
        connection.execute(
            sa.text("UPDATE categories SET sort_order = :position WHERE id = :category_id"),
            {"position": position, "category_id": category_id},
        )
        positions[user_id] = position + 1

    op.create_index(
        "ix_categories_user_sort",
        "categories",
        ["user_id", "sort_order"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_categories_user_sort", table_name="categories")
    op.drop_column("categories", "sort_order")
