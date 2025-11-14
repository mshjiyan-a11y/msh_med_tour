"""add notifications table

Revision ID: d1e2f3a4b5c6
Revises: c5d6e7f8g9h0_add_quote_approval_table
Create Date: 2025-11-08 12:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'd1e2f3a4b5c6'
down_revision = 'c5d6e7f8g9h0'
branch_labels = None
depends_on = None

def upgrade():
    """Create notifications table and indexes if they don't already exist.
    This guards against partially-applied migrations in dev SQLite.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table('notifications'):
        op.create_table('notifications',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id'), nullable=True, index=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True, index=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('message', sa.Text(), nullable=True),
            sa.Column('level', sa.String(length=20), nullable=True),
            sa.Column('ntype', sa.String(length=50), nullable=True),
            sa.Column('link_url', sa.String(length=500), nullable=True),
            sa.Column('channel', sa.String(length=20), nullable=True),
            sa.Column('scheduled_for', sa.DateTime(), nullable=True),
            sa.Column('sent_at', sa.DateTime(), nullable=True),
            sa.Column('is_read', sa.Boolean(), nullable=False, server_default='0'),
            sa.Column('read_at', sa.DateTime(), nullable=True),
            sa.Column('meta_json', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True)
        )
        op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
        op.create_index('ix_notifications_is_read', 'notifications', ['is_read'])
        op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
        op.create_index('ix_notifications_distributor_id', 'notifications', ['distributor_id'])
    else:
        # Ensure indexes exist (SQLite supports IF NOT EXISTS)
        op.execute('CREATE INDEX IF NOT EXISTS ix_notifications_created_at ON notifications (created_at)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_notifications_is_read ON notifications (is_read)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_notifications_user_id ON notifications (user_id)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_notifications_distributor_id ON notifications (distributor_id)')


def downgrade():
    op.drop_index('ix_notifications_distributor_id', table_name='notifications')
    op.drop_index('ix_notifications_user_id', table_name='notifications')
    op.drop_index('ix_notifications_is_read', table_name='notifications')
    op.drop_index('ix_notifications_created_at', table_name='notifications')
    op.drop_table('notifications')
