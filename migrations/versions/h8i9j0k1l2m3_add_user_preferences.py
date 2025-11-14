"""add user preferences

Revision ID: h8i9j0k1l2m3
Revises: g7h8i9j0k1l2
Create Date: 2025-11-08 14:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'h8i9j0k1l2m3'
down_revision = 'g7h8i9j0k1l2'
branch_labels = None
depends_on = None

def upgrade():
    op.add_column('users', sa.Column('theme', sa.String(length=20), nullable=True, server_default='light'))
    op.add_column('users', sa.Column('language', sa.String(length=10), nullable=True, server_default='tr'))


def downgrade():
    op.drop_column('users', 'language')
    op.drop_column('users', 'theme')
