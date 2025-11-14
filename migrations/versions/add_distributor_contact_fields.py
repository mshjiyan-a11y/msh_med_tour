"""Add distributor contact and social media fields

Revision ID: add_contact_fields
Revises: 8cdc3cbd0586
Create Date: 2025-11-06 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_contact_fields'
down_revision = '8cdc3cbd0586'
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to distributors table
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('website', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('facebook', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('instagram', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('twitter', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('linkedin', sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column('whatsapp', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('hospital_license', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('tax_number', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('city', sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column('country', sa.String(length=100), nullable=True))


def downgrade():
    # Remove added columns
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.drop_column('country')
        batch_op.drop_column('city')
        batch_op.drop_column('tax_number')
        batch_op.drop_column('hospital_license')
        batch_op.drop_column('whatsapp')
        batch_op.drop_column('linkedin')
        batch_op.drop_column('twitter')
        batch_op.drop_column('instagram')
        batch_op.drop_column('facebook')
        batch_op.drop_column('website')
