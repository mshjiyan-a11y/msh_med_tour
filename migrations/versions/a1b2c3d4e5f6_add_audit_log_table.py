"""add audit log table

Revision ID: a1b2c3d4e5f6
Revises: 2f397a996702
Create Date: 2025-11-07 12:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f6'
down_revision = '2f397a996702'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'audit_logs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=True),
        sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('action', sa.String(length=20), nullable=False),
        sa.Column('entity_type', sa.String(length=50), nullable=False),
        sa.Column('entity_id', sa.String(length=64), nullable=True),
        sa.Column('field', sa.String(length=100), nullable=True),
        sa.Column('old_value', sa.Text(), nullable=True),
        sa.Column('new_value', sa.Text(), nullable=True),
        sa.Column('note', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
    )
    op.create_index('ix_audit_logs_encounter_id', 'audit_logs', ['encounter_id'])
    op.create_index('ix_audit_logs_distributor_id', 'audit_logs', ['distributor_id'])
    op.create_index('ix_audit_logs_entity_type', 'audit_logs', ['entity_type'])

def downgrade():
    op.drop_index('ix_audit_logs_entity_type', table_name='audit_logs')
    op.drop_index('ix_audit_logs_distributor_id', table_name='audit_logs')
    op.drop_index('ix_audit_logs_encounter_id', table_name='audit_logs')
    op.drop_table('audit_logs')