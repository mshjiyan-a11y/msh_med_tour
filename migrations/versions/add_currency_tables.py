"""
Migration: Add currency rate tables and multi-currency support
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


# revision identifiers
revision = 'add_currency_tables'
down_revision = '787a6fe4b3f4'  # After is_bot_message migration
branch_labels = None
depends_on = None


def upgrade():
    # Create currency_rates table
    op.create_table('currency_rates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('distributor_id', sa.Integer(), nullable=False),
        sa.Column('base_currency', sa.String(length=3), nullable=False),
        sa.Column('target_currency', sa.String(length=3), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('source', sa.String(length=50), nullable=True),
        sa.Column('last_updated', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('is_manual', sa.Boolean(), nullable=True, default=False),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('distributor_id', 'base_currency', 'target_currency', name='_currency_pair_uc')
    )
    
    # Create price_list_items table
    op.create_table('price_list_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('distributor_id', sa.Integer(), nullable=False),
        sa.Column('category', sa.String(length=50), nullable=False),
        sa.Column('service_code', sa.String(length=50), nullable=False),
        sa.Column('service_name_tr', sa.String(length=200), nullable=False),
        sa.Column('service_name_en', sa.String(length=200), nullable=True),
        sa.Column('service_name_ar', sa.String(length=200), nullable=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('base_price', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(length=3), nullable=True, default='USD'),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('is_featured', sa.Boolean(), nullable=True, default=False),
        sa.Column('display_order', sa.Integer(), nullable=True, default=0),
        sa.Column('created_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Add currency settings to app_settings table
    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.add_column(sa.Column('base_currency', sa.String(length=3), nullable=True, server_default='USD'))
        batch_op.add_column(sa.Column('currency_api_source', sa.String(length=50), nullable=True, server_default='exchangerate-api'))
        batch_op.add_column(sa.Column('auto_update_rates', sa.Boolean(), nullable=True, server_default='1'))
        batch_op.add_column(sa.Column('last_rate_update', sa.DateTime(), nullable=True))


def downgrade():
    # Remove currency settings from app_settings
    with op.batch_alter_table('app_settings', schema=None) as batch_op:
        batch_op.drop_column('last_rate_update')
        batch_op.drop_column('auto_update_rates')
        batch_op.drop_column('currency_api_source')
        batch_op.drop_column('base_currency')
    
    # Drop tables
    op.drop_table('price_list_items')
    op.drop_table('currency_rates')
