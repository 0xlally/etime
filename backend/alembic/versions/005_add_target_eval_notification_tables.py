"""Add targets, evaluations, notifications, punishments, audit logs

Revision ID: 005
Revises: 004
Create Date: 2025-12-21 18:25:00
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'work_targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('period', sa.String(length=20), nullable=False),
        sa.Column('target_seconds', sa.Integer(), nullable=False),
        sa.Column('include_category_ids', sa.JSON(), nullable=True),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_targets_id'), 'work_targets', ['id'], unique=False)
    op.create_index(op.f('ix_work_targets_user_id'), 'work_targets', ['user_id'], unique=False)

    op.create_table(
        'admin_audit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('admin_user_id', sa.Integer(), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('target_type', sa.String(length=50), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('detail_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_admin_audit_logs_id'), 'admin_audit_logs', ['id'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_admin_user_id'), 'admin_audit_logs', ['admin_user_id'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_action'), 'admin_audit_logs', ['action'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_target_id'), 'admin_audit_logs', ['target_id'], unique=False)
    op.create_index(op.f('ix_admin_audit_logs_created_at'), 'admin_audit_logs', ['created_at'], unique=False)

    op.create_table(
        'notifications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notifications_id'), 'notifications', ['id'], unique=False)
    op.create_index(op.f('ix_notifications_user_id'), 'notifications', ['user_id'], unique=False)

    op.create_table(
        'work_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('period_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('period_end', sa.DateTime(timezone=True), nullable=False),
        sa.Column('actual_seconds', sa.Integer(), nullable=False),
        sa.Column('target_seconds', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('deficit_seconds', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['target_id'], ['work_targets.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_work_evaluations_id'), 'work_evaluations', ['id'], unique=False)
    op.create_index(op.f('ix_work_evaluations_user_id'), 'work_evaluations', ['user_id'], unique=False)
    op.create_index(op.f('ix_work_evaluations_target_id'), 'work_evaluations', ['target_id'], unique=False)

    op.create_table(
        'punishment_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('evaluation_id', sa.Integer(), nullable=False),
        sa.Column('rule_type', sa.String(length=50), nullable=False),
        sa.Column('payload_json', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['evaluation_id'], ['work_evaluations.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_punishment_events_id'), 'punishment_events', ['id'], unique=False)
    op.create_index(op.f('ix_punishment_events_user_id'), 'punishment_events', ['user_id'], unique=False)
    op.create_index(op.f('ix_punishment_events_evaluation_id'), 'punishment_events', ['evaluation_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_punishment_events_evaluation_id'), table_name='punishment_events')
    op.drop_index(op.f('ix_punishment_events_user_id'), table_name='punishment_events')
    op.drop_index(op.f('ix_punishment_events_id'), table_name='punishment_events')
    op.drop_table('punishment_events')

    op.drop_index(op.f('ix_work_evaluations_target_id'), table_name='work_evaluations')
    op.drop_index(op.f('ix_work_evaluations_user_id'), table_name='work_evaluations')
    op.drop_index(op.f('ix_work_evaluations_id'), table_name='work_evaluations')
    op.drop_table('work_evaluations')

    op.drop_index(op.f('ix_notifications_user_id'), table_name='notifications')
    op.drop_index(op.f('ix_notifications_id'), table_name='notifications')
    op.drop_table('notifications')

    op.drop_index(op.f('ix_admin_audit_logs_created_at'), table_name='admin_audit_logs')
    op.drop_index(op.f('ix_admin_audit_logs_target_id'), table_name='admin_audit_logs')
    op.drop_index(op.f('ix_admin_audit_logs_action'), table_name='admin_audit_logs')
    op.drop_index(op.f('ix_admin_audit_logs_admin_user_id'), table_name='admin_audit_logs')
    op.drop_index(op.f('ix_admin_audit_logs_id'), table_name='admin_audit_logs')
    op.drop_table('admin_audit_logs')

    op.drop_index(op.f('ix_work_targets_user_id'), table_name='work_targets')
    op.drop_index(op.f('ix_work_targets_id'), table_name='work_targets')
    op.drop_table('work_targets')
