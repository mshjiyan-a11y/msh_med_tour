"""add multilang, personalization, backup fields

Revision ID: b3c4d5e6f7g8
Revises: a1b2c3d4e5f6
Create Date: 2025-11-07 14:00:00.000000
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'b3c4d5e6f7g8'
down_revision = 'a1b2c3d4e5f6'
branch_labels = None
depends_on = None

def upgrade():
    # Distributor: add personalized greeting and brand font
    op.add_column('distributors', sa.Column('greeting_message', sa.Text(), nullable=True))
    op.add_column('distributors', sa.Column('brand_font', sa.String(length=50), nullable=True))
    op.add_column('distributors', sa.Column('pdf_language', sa.String(length=2), server_default='tr', nullable=False))
    op.add_column('distributors', sa.Column('currency_format_locale', sa.String(length=10), server_default='tr_TR', nullable=False))
    
    # Encounter: add personalized greeting, valid_until, payment_plan, exchange_rate
    op.add_column('encounters', sa.Column('valid_until', sa.Date(), nullable=True))
    op.add_column('encounters', sa.Column('payment_plan', sa.String(length=100), nullable=True))
    op.add_column('encounters', sa.Column('exchange_rate', sa.String(length=50), nullable=True))
    op.add_column('encounters', sa.Column('greeting_message', sa.Text(), nullable=True))
    
    # AppSettings: backup schedule, API endpoint, performance flag
    op.add_column('app_settings', sa.Column('backup_enabled', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('app_settings', sa.Column('backup_schedule', sa.String(length=50), server_default='daily', nullable=False))
    op.add_column('app_settings', sa.Column('api_enabled', sa.Boolean(), server_default='1', nullable=False))
    op.add_column('app_settings', sa.Column('performance_mode', sa.String(length=20), server_default='standard', nullable=False))

def downgrade():
    op.drop_column('app_settings', 'performance_mode')
    op.drop_column('app_settings', 'api_enabled')
    op.drop_column('app_settings', 'backup_schedule')
    op.drop_column('app_settings', 'backup_enabled')
    op.drop_column('encounters', 'greeting_message')
    op.drop_column('encounters', 'exchange_rate')
    op.drop_column('encounters', 'payment_plan')
    op.drop_column('encounters', 'valid_until')
    op.drop_column('distributors', 'currency_format_locale')
    op.drop_column('distributors', 'pdf_language')
    op.drop_column('distributors', 'brand_font')
    op.drop_column('distributors', 'greeting_message')
