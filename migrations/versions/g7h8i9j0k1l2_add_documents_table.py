"""add documents table

Revision ID: g7h8i9j0k1l2
Revises: f5g6h7i8j9k0
Create Date: 2025-11-08 13:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'g7h8i9j0k1l2'
down_revision = 'f5g6h7i8j9k0'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('documents',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('distributor_id', sa.Integer(), sa.ForeignKey('distributors.id'), nullable=False),
        sa.Column('patient_id', sa.Integer(), sa.ForeignKey('patients.id'), nullable=True),
        sa.Column('encounter_id', sa.Integer(), sa.ForeignKey('encounters.id'), nullable=True),
        sa.Column('uploaded_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('title', sa.String(length=200), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('stored_filename', sa.String(length=255), nullable=False),
        sa.Column('file_path', sa.String(length=500), nullable=False),
        sa.Column('file_size', sa.Integer(), nullable=True),
        sa.Column('mime_type', sa.String(length=100), nullable=True),
        sa.Column('document_type', sa.String(length=50), nullable=True),
        sa.Column('tags', sa.String(length=500), nullable=True),
        sa.Column('is_public', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('is_archived', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('uploaded_at', sa.DateTime(), nullable=True),
        sa.Column('archived_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_documents_distributor_id', 'documents', ['distributor_id'])
    op.create_index('ix_documents_patient_id', 'documents', ['patient_id'])
    op.create_index('ix_documents_encounter_id', 'documents', ['encounter_id'])
    op.create_index('ix_documents_document_type', 'documents', ['document_type'])
    op.create_index('ix_documents_is_archived', 'documents', ['is_archived'])
    op.create_index('ix_documents_uploaded_at', 'documents', ['uploaded_at'])


def downgrade():
    op.drop_index('ix_documents_uploaded_at', table_name='documents')
    op.drop_index('ix_documents_is_archived', table_name='documents')
    op.drop_index('ix_documents_document_type', table_name='documents')
    op.drop_index('ix_documents_encounter_id', table_name='documents')
    op.drop_index('ix_documents_patient_id', table_name='documents')
    op.drop_index('ix_documents_distributor_id', table_name='documents')
    op.drop_table('documents')
