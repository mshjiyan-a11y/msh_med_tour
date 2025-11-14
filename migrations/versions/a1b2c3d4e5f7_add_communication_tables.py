"""add_communication_tables

Revision ID: a1b2c3d4e5f7
Revises: 3c069d5b1196
Create Date: 2025-11-10 16:50:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'a1b2c3d4e5f7'
down_revision = '3c069d5b1196'
branch_labels = None
depends_on = None


def upgrade():
    # Messages table
    op.create_table('messages',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('distributor_id', sa.Integer(), nullable=False),
    sa.Column('sender_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('journey_id', sa.Integer(), nullable=True),
    sa.Column('message_type', sa.String(length=20), nullable=True),
    sa.Column('content', sa.Text(), nullable=False),
    sa.Column('attachment_url', sa.String(length=500), nullable=True),
    sa.Column('is_read', sa.Boolean(), nullable=True),
    sa.Column('read_at', sa.DateTime(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['sender_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Communication logs table
    op.create_table('communication_logs',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('distributor_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('journey_id', sa.Integer(), nullable=True),
    sa.Column('communication_type', sa.String(length=20), nullable=False),
    sa.Column('direction', sa.String(length=10), nullable=False),
    sa.Column('subject', sa.String(length=200), nullable=True),
    sa.Column('content', sa.Text(), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('phone_number', sa.String(length=20), nullable=True),
    sa.Column('email_address', sa.String(length=100), nullable=True),
    sa.Column('recording_url', sa.String(length=500), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Patient feedbacks table
    op.create_table('patient_feedbacks',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('distributor_id', sa.Integer(), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('journey_id', sa.Integer(), nullable=True),
    sa.Column('encounter_id', sa.Integer(), nullable=True),
    sa.Column('feedback_type', sa.String(length=30), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.Column('service_quality', sa.Integer(), nullable=True),
    sa.Column('communication_quality', sa.Integer(), nullable=True),
    sa.Column('facility_cleanliness', sa.Integer(), nullable=True),
    sa.Column('treatment_satisfaction', sa.Integer(), nullable=True),
    sa.Column('value_for_money', sa.Integer(), nullable=True),
    sa.Column('comment', sa.Text(), nullable=True),
    sa.Column('suggestions', sa.Text(), nullable=True),
    sa.Column('would_recommend', sa.Boolean(), nullable=True),
    sa.Column('referral_likelihood', sa.Integer(), nullable=True),
    sa.Column('is_public', sa.Boolean(), nullable=True),
    sa.Column('is_featured', sa.Boolean(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('response', sa.Text(), nullable=True),
    sa.Column('responded_by', sa.Integer(), nullable=True),
    sa.Column('responded_at', sa.DateTime(), nullable=True),
    sa.Column('ip_address', sa.String(length=50), nullable=True),
    sa.Column('user_agent', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id'], ),
    sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id'], ),
    sa.ForeignKeyConstraint(['responded_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Support tickets table
    op.create_table('support_tickets',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('distributor_id', sa.Integer(), nullable=False),
    sa.Column('ticket_number', sa.String(length=20), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=False),
    sa.Column('journey_id', sa.Integer(), nullable=True),
    sa.Column('category', sa.String(length=50), nullable=False),
    sa.Column('priority', sa.String(length=20), nullable=True),
    sa.Column('subject', sa.String(length=200), nullable=False),
    sa.Column('description', sa.Text(), nullable=False),
    sa.Column('assigned_to', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('resolution', sa.Text(), nullable=True),
    sa.Column('resolved_at', sa.DateTime(), nullable=True),
    sa.Column('resolved_by', sa.Integer(), nullable=True),
    sa.Column('due_date', sa.DateTime(), nullable=True),
    sa.Column('first_response_at', sa.DateTime(), nullable=True),
    sa.Column('tags', sa.String(length=200), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.Column('closed_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id'], ),
    sa.ForeignKeyConstraint(['assigned_to'], ['users.id'], ),
    sa.ForeignKeyConstraint(['resolved_by'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('ticket_number')
    )
    
    # Ticket replies table
    op.create_table('ticket_replies',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ticket_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('is_staff', sa.Boolean(), nullable=True),
    sa.Column('message', sa.Text(), nullable=False),
    sa.Column('attachments', sa.Text(), nullable=True),
    sa.Column('is_internal', sa.Boolean(), nullable=True),
    sa.Column('created_at', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['ticket_id'], ['support_tickets.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # Chat sessions table
    op.create_table('chat_sessions',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('distributor_id', sa.Integer(), nullable=False),
    sa.Column('session_id', sa.String(length=50), nullable=False),
    sa.Column('patient_id', sa.Integer(), nullable=True),
    sa.Column('agent_id', sa.Integer(), nullable=True),
    sa.Column('status', sa.String(length=20), nullable=True),
    sa.Column('started_at', sa.DateTime(), nullable=True),
    sa.Column('ended_at', sa.DateTime(), nullable=True),
    sa.Column('duration_seconds', sa.Integer(), nullable=True),
    sa.Column('visitor_ip', sa.String(length=50), nullable=True),
    sa.Column('visitor_country', sa.String(length=50), nullable=True),
    sa.Column('referrer_url', sa.String(length=500), nullable=True),
    sa.Column('rated', sa.Boolean(), nullable=True),
    sa.Column('rating', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id'], ),
    sa.ForeignKeyConstraint(['patient_id'], ['patients.id'], ),
    sa.ForeignKeyConstraint(['agent_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('session_id')
    )


def downgrade():
    op.drop_table('chat_sessions')
    op.drop_table('ticket_replies')
    op.drop_table('support_tickets')
    op.drop_table('patient_feedbacks')
    op.drop_table('communication_logs')
    op.drop_table('messages')
