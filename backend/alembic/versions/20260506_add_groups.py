"""add groups

Revision ID: 20260506_groups
Revises: 20260505_session_cgid
Create Date: 2026-05-06
"""

from alembic import op
import sqlalchemy as sa


revision = "20260506_groups"
down_revision = "20260505_session_cgid"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("owner_id", sa.Integer(), nullable=False),
        sa.Column("invite_code", sa.String(length=32), nullable=False),
        sa.Column("visibility", sa.String(length=20), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("invite_code"),
    )
    op.create_index(op.f("ix_groups_id"), "groups", ["id"], unique=False)
    op.create_index(op.f("ix_groups_invite_code"), "groups", ["invite_code"], unique=False)
    op.create_index(op.f("ix_groups_owner_id"), "groups", ["owner_id"], unique=False)

    op.create_table(
        "group_members",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("role", sa.String(length=20), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("muted_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", name="uq_group_members_group_user"),
    )
    op.create_index(op.f("ix_group_members_group_id"), "group_members", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_members_id"), "group_members", ["id"], unique=False)
    op.create_index(op.f("ix_group_members_user_id"), "group_members", ["user_id"], unique=False)

    op.create_table(
        "group_messages",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("message_type", sa.String(length=20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("metadata_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_group_messages_created_at"), "group_messages", ["created_at"], unique=False)
    op.create_index(op.f("ix_group_messages_group_id"), "group_messages", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_messages_id"), "group_messages", ["id"], unique=False)
    op.create_index(op.f("ix_group_messages_user_id"), "group_messages", ["user_id"], unique=False)

    op.create_table(
        "group_daily_snapshots",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("group_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("total_seconds", sa.Integer(), nullable=False),
        sa.Column("target_completed_count", sa.Integer(), nullable=False),
        sa.Column("target_total_count", sa.Integer(), nullable=False),
        sa.Column("streak_days", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["group_id"], ["groups.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("group_id", "user_id", "date", name="uq_group_daily_snapshots_group_user_date"),
    )
    op.create_index(op.f("ix_group_daily_snapshots_date"), "group_daily_snapshots", ["date"], unique=False)
    op.create_index(op.f("ix_group_daily_snapshots_group_id"), "group_daily_snapshots", ["group_id"], unique=False)
    op.create_index(op.f("ix_group_daily_snapshots_id"), "group_daily_snapshots", ["id"], unique=False)
    op.create_index(op.f("ix_group_daily_snapshots_user_id"), "group_daily_snapshots", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_group_daily_snapshots_user_id"), table_name="group_daily_snapshots")
    op.drop_index(op.f("ix_group_daily_snapshots_id"), table_name="group_daily_snapshots")
    op.drop_index(op.f("ix_group_daily_snapshots_group_id"), table_name="group_daily_snapshots")
    op.drop_index(op.f("ix_group_daily_snapshots_date"), table_name="group_daily_snapshots")
    op.drop_table("group_daily_snapshots")

    op.drop_index(op.f("ix_group_messages_user_id"), table_name="group_messages")
    op.drop_index(op.f("ix_group_messages_id"), table_name="group_messages")
    op.drop_index(op.f("ix_group_messages_group_id"), table_name="group_messages")
    op.drop_index(op.f("ix_group_messages_created_at"), table_name="group_messages")
    op.drop_table("group_messages")

    op.drop_index(op.f("ix_group_members_user_id"), table_name="group_members")
    op.drop_index(op.f("ix_group_members_id"), table_name="group_members")
    op.drop_index(op.f("ix_group_members_group_id"), table_name="group_members")
    op.drop_table("group_members")

    op.drop_index(op.f("ix_groups_owner_id"), table_name="groups")
    op.drop_index(op.f("ix_groups_invite_code"), table_name="groups")
    op.drop_index(op.f("ix_groups_id"), table_name="groups")
    op.drop_table("groups")
