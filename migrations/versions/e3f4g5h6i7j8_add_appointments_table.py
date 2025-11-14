"""add appointments table

Revision ID: e3f4g5h6i7j8
Revises: d1e2f3a4b5c6
Create Date: 2025-11-08 12:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e3f4g5h6i7j8'
down_revision = 'd1e2f3a4b5c6'
branch_labels = None
depends_on = None

def upgrade():
    """Create appointments table and indexes if they don't already exist.
    This prevents failures on partially-applied dev databases.
    """
    bind = op.get_bind()
    insp = sa.inspect(bind)

    if not insp.has_table('appointments'):
        op.create_table('appointments',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id'), nullable=False, index=True),
            sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id'), nullable=False, index=True),
            sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=True, index=True),
            sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
            sa.Column('title', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('appointment_type', sa.String(length=50), nullable=True),
            sa.Column('start_time', sa.DateTime(), nullable=False),
            sa.Column('end_time', sa.DateTime(), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=True),
            sa.Column('doctor_name', sa.String(length=100), nullable=True),
            sa.Column('room_number', sa.String(length=50), nullable=True),
            sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
            sa.Column('reminder_method', sa.String(length=20), nullable=True),
            sa.Column('notes', sa.Text(), nullable=True),
            sa.Column('cancellation_reason', sa.Text(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.Column('updated_at', sa.DateTime(), nullable=True)
        )
        op.create_index('ix_appointments_distributor_id', 'appointments', ['distributor_id'])
        op.create_index('ix_appointments_patient_id', 'appointments', ['patient_id'])
        op.create_index('ix_appointments_encounter_id', 'appointments', ['encounter_id'])
        op.create_index('ix_appointments_start_time', 'appointments', ['start_time'])
        op.create_index('ix_appointments_end_time', 'appointments', ['end_time'])
        op.create_index('ix_appointments_status', 'appointments', ['status'])
        op.create_index('ix_appointments_created_at', 'appointments', ['created_at'])
    else:
        # Ensure indexes exist when table exists already (SQLite IF NOT EXISTS)
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_distributor_id ON appointments (distributor_id)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_patient_id ON appointments (patient_id)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_encounter_id ON appointments (encounter_id)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_start_time ON appointments (start_time)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_end_time ON appointments (end_time)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_status ON appointments (status)')
        op.execute('CREATE INDEX IF NOT EXISTS ix_appointments_created_at ON appointments (created_at)')


def downgrade():
    op.drop_index('ix_appointments_created_at', table_name='appointments')
    op.drop_index('ix_appointments_status', table_name='appointments')
    op.drop_index('ix_appointments_end_time', table_name='appointments')
    op.drop_index('ix_appointments_start_time', table_name='appointments')
    op.drop_index('ix_appointments_encounter_id', table_name='appointments')
    op.drop_index('ix_appointments_patient_id', table_name='appointments')
    op.drop_index('ix_appointments_distributor_id', table_name='appointments')
    op.drop_table('appointments')
