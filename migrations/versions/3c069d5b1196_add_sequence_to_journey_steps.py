"""add sequence to journey steps

Revision ID: 3c069d5b1196
Revises: 54d32723504f
Create Date: 2025-11-10 00:17:32.364127

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3c069d5b1196'
down_revision = '54d32723504f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    existing = inspector.get_table_names()

    # If journey tables were never created (previous migration was empty), create them now (with sequence)
    if 'patient_journeys' not in existing:
        op.create_table('patient_journeys',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('distributor_id', sa.Integer(), nullable=False),
            sa.Column('patient_id', sa.Integer(), nullable=False),
            sa.Column('encounter_id', sa.Integer(), nullable=True),
            sa.Column('coordinator_id', sa.Integer(), nullable=True),
            sa.Column('journey_code', sa.String(length=50), nullable=False),
            sa.Column('journey_type', sa.String(length=50), nullable=True),
            sa.Column('arrival_date', sa.DateTime(), nullable=False),
            sa.Column('departure_date', sa.DateTime(), nullable=False),
            sa.Column('actual_arrival', sa.DateTime(), nullable=True),
            sa.Column('actual_departure', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=True),
            sa.Column('purpose', sa.Text(), nullable=True),
            sa.Column('special_requirements', sa.Text(), nullable=True),
            sa.Column('emergency_contact', sa.String(length=200), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('estimated_cost', sa.Float(), nullable=True),
            sa.Column('actual_cost', sa.Float(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('created_by', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['coordinator_id'], ['users.id']),
            sa.ForeignKeyConstraint(['created_by'], ['users.id']),
            sa.ForeignKeyConstraint(['distributor_id'], ['distributors.id']),
            sa.ForeignKeyConstraint(['encounter_id'], ['encounters.id']),
            sa.ForeignKeyConstraint(['patient_id'], ['patients.id']),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('journey_code')
        )
        op.create_index(op.f('ix_patient_journeys_arrival_date'), 'patient_journeys', ['arrival_date'], unique=False)
        op.create_index(op.f('ix_patient_journeys_departure_date'), 'patient_journeys', ['departure_date'], unique=False)
        op.create_index(op.f('ix_patient_journeys_distributor_id'), 'patient_journeys', ['distributor_id'], unique=False)
        op.create_index(op.f('ix_patient_journeys_encounter_id'), 'patient_journeys', ['encounter_id'], unique=False)
        op.create_index(op.f('ix_patient_journeys_journey_code'), 'patient_journeys', ['journey_code'], unique=True)
        op.create_index(op.f('ix_patient_journeys_patient_id'), 'patient_journeys', ['patient_id'], unique=False)
        op.create_index(op.f('ix_patient_journeys_status'), 'patient_journeys', ['status'], unique=False)

    if 'journey_steps' not in existing:
        op.create_table('journey_steps',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('journey_id', sa.Integer(), nullable=False),
            sa.Column('step_type', sa.String(length=50), nullable=False),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('scheduled_date', sa.DateTime(), nullable=False),
            sa.Column('scheduled_end', sa.DateTime(), nullable=True),
            sa.Column('actual_start', sa.DateTime(), nullable=True),
            sa.Column('actual_end', sa.DateTime(), nullable=True),
            sa.Column('duration_minutes', sa.Integer(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=True),
            sa.Column('appointment_id', sa.Integer(), nullable=True),
            sa.Column('hotel_reservation_id', sa.Integer(), nullable=True),
            sa.Column('location', sa.String(length=300), nullable=True),
            sa.Column('contact_person', sa.String(length=100), nullable=True),
            sa.Column('contact_phone', sa.String(length=30), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('alert_message', sa.String(length=500), nullable=True),
            sa.Column('is_critical', sa.Boolean(), nullable=True),
            sa.Column('cost', sa.Float(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.Column('completed_by', sa.Integer(), nullable=True),
            sa.Column('sequence', sa.Integer(), nullable=True),
            sa.ForeignKeyConstraint(['appointment_id'], ['appointments.id']),
            sa.ForeignKeyConstraint(['completed_by'], ['users.id']),
            sa.ForeignKeyConstraint(['hotel_reservation_id'], ['hotel_reservations.id']),
            sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_journey_steps_journey_id'), 'journey_steps', ['journey_id'], unique=False)
        op.create_index(op.f('ix_journey_steps_scheduled_date'), 'journey_steps', ['scheduled_date'], unique=False)
        op.create_index(op.f('ix_journey_steps_status'), 'journey_steps', ['status'], unique=False)
        op.create_index(op.f('ix_journey_steps_step_type'), 'journey_steps', ['step_type'], unique=False)
        op.create_index(op.f('ix_journey_steps_sequence'), 'journey_steps', ['sequence'], unique=False)
    else:
        # Table exists, just add sequence if missing
        cols = [c['name'] for c in inspector.get_columns('journey_steps')]
        if 'sequence' not in cols:
            with op.batch_alter_table('journey_steps') as batch_op:
                batch_op.add_column(sa.Column('sequence', sa.Integer(), nullable=True))
                batch_op.create_index(batch_op.f('ix_journey_steps_sequence'), ['sequence'], unique=False)

    if 'flights' not in existing:
        op.create_table('flights',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('journey_id', sa.Integer(), nullable=False),
            sa.Column('journey_step_id', sa.Integer(), nullable=True),
            sa.Column('flight_type', sa.String(length=20), nullable=False),
            sa.Column('airline', sa.String(length=100), nullable=True),
            sa.Column('flight_number', sa.String(length=50), nullable=True),
            sa.Column('booking_reference', sa.String(length=50), nullable=True),
            sa.Column('departure_airport', sa.String(length=100), nullable=True),
            sa.Column('arrival_airport', sa.String(length=100), nullable=True),
            sa.Column('departure_city', sa.String(length=100), nullable=True),
            sa.Column('arrival_city', sa.String(length=100), nullable=True),
            sa.Column('scheduled_departure', sa.DateTime(), nullable=False),
            sa.Column('scheduled_arrival', sa.DateTime(), nullable=False),
            sa.Column('actual_departure', sa.DateTime(), nullable=True),
            sa.Column('actual_arrival', sa.DateTime(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=True),
            sa.Column('passenger_count', sa.Integer(), nullable=True),
            sa.Column('seat_numbers', sa.String(length=100), nullable=True),
            sa.Column('baggage_info', sa.String(length=200), nullable=True),
            sa.Column('terminal', sa.String(length=20), nullable=True),
            sa.Column('gate', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id']),
            sa.ForeignKeyConstraint(['journey_step_id'], ['journey_steps.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_flights_journey_id'), 'flights', ['journey_id'], unique=False)

    if 'transfers' not in existing:
        op.create_table('transfers',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('journey_id', sa.Integer(), nullable=False),
            sa.Column('journey_step_id', sa.Integer(), nullable=True),
            sa.Column('transfer_type', sa.String(length=50), nullable=False),
            sa.Column('pickup_location', sa.String(length=300), nullable=False),
            sa.Column('pickup_address', sa.Text(), nullable=True),
            sa.Column('dropoff_location', sa.String(length=300), nullable=False),
            sa.Column('dropoff_address', sa.Text(), nullable=True),
            sa.Column('scheduled_pickup', sa.DateTime(), nullable=False),
            sa.Column('actual_pickup', sa.DateTime(), nullable=True),
            sa.Column('estimated_duration', sa.Integer(), nullable=True),
            sa.Column('actual_duration', sa.Integer(), nullable=True),
            sa.Column('vehicle_type', sa.String(length=50), nullable=True),
            sa.Column('vehicle_plate', sa.String(length=30), nullable=True),
            sa.Column('driver_name', sa.String(length=100), nullable=True),
            sa.Column('driver_phone', sa.String(length=30), nullable=True),
            sa.Column('passenger_count', sa.Integer(), nullable=True),
            sa.Column('has_luggage', sa.Boolean(), nullable=True),
            sa.Column('wheelchair_required', sa.Boolean(), nullable=True),
            sa.Column('status', sa.String(length=30), nullable=True),
            sa.Column('cost', sa.Float(), nullable=True),
            sa.Column('currency', sa.String(length=3), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('special_instructions', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True),
            sa.ForeignKeyConstraint(['journey_id'], ['patient_journeys.id']),
            sa.ForeignKeyConstraint(['journey_step_id'], ['journey_steps.id']),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index(op.f('ix_transfers_journey_id'), 'transfers', ['journey_id'], unique=False)
        op.create_index(op.f('ix_transfers_scheduled_pickup'), 'transfers', ['scheduled_pickup'], unique=False)
        op.create_index(op.f('ix_transfers_status'), 'transfers', ['status'], unique=False)


def downgrade():
    # Only drop sequence column (not full tables) to avoid data loss
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    if 'journey_steps' in inspector.get_table_names():
        cols = [c['name'] for c in inspector.get_columns('journey_steps')]
        if 'sequence' in cols:
            with op.batch_alter_table('journey_steps') as batch_op:
                batch_op.drop_index(batch_op.f('ix_journey_steps_sequence'))
                batch_op.drop_column('sequence')
