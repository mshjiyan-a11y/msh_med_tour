"""add_discount_and_currency_support

Revision ID: 2f397a996702
Revises: 48cd6e121798
Create Date: 2025-11-07 21:04:41.224839

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2f397a996702'
down_revision = '48cd6e121798'
branch_labels = None
depends_on = None


def upgrade():
    # Add default_currency to distributors
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.add_column(sa.Column('default_currency', sa.String(length=3), nullable=True, server_default='EUR'))
    
    # Add discount fields to dental_procedures
    with op.batch_alter_table('dental_procedures', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))
    
    # Add discount fields to eye_treatment_selections
    with op.batch_alter_table('eye_treatment_selections', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))
    
    # Add discount fields to aesthetic_procedures
    with op.batch_alter_table('aesthetic_procedures', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))
    
    # Add discount fields to bariatric_surgeries
    with op.batch_alter_table('bariatric_surgeries', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))
    
    # Add discount fields to ivf_treatments
    with op.batch_alter_table('ivf_treatments', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))
    
    # Add discount fields to checkup_packages
    with op.batch_alter_table('checkup_packages', schema=None) as batch_op:
        batch_op.add_column(sa.Column('discount_enabled', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('discounted_price', sa.Float(), nullable=True))


def downgrade():
    with op.batch_alter_table('checkup_packages', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('ivf_treatments', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('bariatric_surgeries', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('aesthetic_procedures', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('eye_treatment_selections', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('dental_procedures', schema=None) as batch_op:
        batch_op.drop_column('discounted_price')
        batch_op.drop_column('discount_enabled')
    
    with op.batch_alter_table('distributors', schema=None) as batch_op:
        batch_op.drop_column('default_currency')
