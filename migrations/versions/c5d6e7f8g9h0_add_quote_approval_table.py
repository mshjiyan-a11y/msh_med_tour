"""add quote approval table

Revision ID: c5d6e7f8g9h0
Revises: b3c4d5e6f7g8
Create Date: 2025-11-07 15:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'c5d6e7f8g9h0'
down_revision = 'b3c4d5e6f7g8'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'quote_approvals',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=False, unique=True),
        sa.Column('token', sa.String(length=64), unique=True, nullable=False),
        sa.Column('status', sa.String(length=20), server_default='pending', nullable=False),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('approved_by_name', sa.String(length=100), nullable=True),
        sa.Column('approved_by_email', sa.String(length=120), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now())
    )
    op.create_index('ix_quote_approvals_encounter_id', 'quote_approvals', ['encounter_id'])
    op.create_index('ix_quote_approvals_token', 'quote_approvals', ['token'])

def downgrade():
    op.drop_index('ix_quote_approvals_token', table_name='quote_approvals')
    op.drop_index('ix_quote_approvals_encounter_id', table_name='quote_approvals')
    op.drop_table('quote_approvals')
