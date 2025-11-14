"""add rbac tables

Revision ID: f5g6h7i8j9k0
Revises: e3f4g5h6i7j8
Create Date: 2025-11-08 13:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f5g6h7i8j9k0'
down_revision = 'e3f4g5h6i7j8'
branch_labels = None
depends_on = None

def upgrade():
    # Roles table
    op.create_table('roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('is_system', sa.Boolean(), nullable=True, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_roles_name', 'roles', ['name'])

    # Permissions table
    op.create_table('permissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(length=50), nullable=False, unique=True),
        sa.Column('display_name', sa.String(length=100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True)
    )
    op.create_index('ix_permissions_name', 'permissions', ['name'])

    # Role-Permission junction table
    op.create_table('role_permissions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('permission_id', sa.Integer(), sa.ForeignKey('permissions.id'), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('role_id', 'permission_id', name='uq_role_permission')
    )
    op.create_index('ix_role_permissions_role_id', 'role_permissions', ['role_id'])
    op.create_index('ix_role_permissions_permission_id', 'role_permissions', ['permission_id'])

    # User-Role junction table
    op.create_table('user_roles',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('role_id', sa.Integer(), sa.ForeignKey('roles.id'), nullable=False),
        sa.Column('granted_by', sa.Integer(), sa.ForeignKey('users.id'), nullable=True),
        sa.Column('granted_at', sa.DateTime(), nullable=True),
        sa.UniqueConstraint('user_id', 'role_id', name='uq_user_role')
    )
    op.create_index('ix_user_roles_user_id', 'user_roles', ['user_id'])
    op.create_index('ix_user_roles_role_id', 'user_roles', ['role_id'])

    # Seed default roles and permissions
    op.execute("""
        INSERT INTO roles (name, display_name, description, is_system, created_at) VALUES
        ('viewer', 'Görüntüleyici', 'Sadece okuma yetkisi', 1, datetime('now')),
        ('staff', 'Personel', 'Temel işlem yetkileri', 1, datetime('now')),
        ('manager', 'Yönetici', 'Tüm işlemleri yapma yetkisi', 1, datetime('now')),
        ('admin', 'Admin', 'Sistem yönetimi', 1, datetime('now'))
    """)

    op.execute("""
        INSERT INTO permissions (name, display_name, description, category, created_at) VALUES
        ('view_patients', 'Hastaları Görüntüle', 'Hasta listesini ve detaylarını görüntüleme', 'patients', datetime('now')),
        ('create_patients', 'Hasta Ekle', 'Yeni hasta oluşturma', 'patients', datetime('now')),
        ('edit_patients', 'Hasta Düzenle', 'Hasta bilgilerini düzenleme', 'patients', datetime('now')),
        ('delete_patients', 'Hasta Sil', 'Hasta kaydını silme', 'patients', datetime('now')),
        ('view_encounters', 'Muayeneleri Görüntüle', 'Muayene listesini görüntüleme', 'encounters', datetime('now')),
        ('create_encounters', 'Muayene Ekle', 'Yeni muayene oluşturma', 'encounters', datetime('now')),
        ('edit_encounters', 'Muayene Düzenle', 'Muayene bilgilerini düzenleme', 'encounters', datetime('now')),
        ('delete_encounters', 'Muayene Sil', 'Muayene kaydını silme', 'encounters', datetime('now')),
        ('view_appointments', 'Randevuları Görüntüle', 'Randevu listesini görüntüleme', 'appointments', datetime('now')),
        ('create_appointments', 'Randevu Ekle', 'Yeni randevu oluşturma', 'appointments', datetime('now')),
        ('edit_appointments', 'Randevu Düzenle', 'Randevu bilgilerini düzenleme', 'appointments', datetime('now')),
        ('delete_appointments', 'Randevu Sil', 'Randevu kaydını silme', 'appointments', datetime('now')),
        ('manage_users', 'Kullanıcı Yönetimi', 'Kullanıcı ekleme/düzenleme/silme', 'admin', datetime('now')),
        ('manage_roles', 'Rol Yönetimi', 'Rol ve yetki yönetimi', 'admin', datetime('now')),
        ('view_reports', 'Raporları Görüntüle', 'PDF ve raporları görüntüleme', 'reports', datetime('now')),
        ('send_emails', 'E-posta Gönder', 'Hasta ve tekliflere e-posta gönderme', 'reports', datetime('now')),
        ('manage_settings', 'Ayarları Yönet', 'Sistem ayarlarını değiştirme', 'admin', datetime('now'))
    """)

    # Assign permissions to roles
    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, datetime('now')
        FROM roles r, permissions p
        WHERE r.name = 'viewer' AND p.name IN ('view_patients', 'view_encounters', 'view_appointments', 'view_reports')
    """)

    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, datetime('now')
        FROM roles r, permissions p
        WHERE r.name = 'staff' AND p.name IN ('view_patients', 'create_patients', 'edit_patients', 'view_encounters', 'create_encounters', 'edit_encounters', 'view_appointments', 'create_appointments', 'edit_appointments', 'view_reports', 'send_emails')
    """)

    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, datetime('now')
        FROM roles r, permissions p
        WHERE r.name = 'manager' AND p.category IN ('patients', 'encounters', 'appointments', 'reports')
    """)

    op.execute("""
        INSERT INTO role_permissions (role_id, permission_id, created_at)
        SELECT r.id, p.id, datetime('now')
        FROM roles r, permissions p
        WHERE r.name = 'admin'
    """)


def downgrade():
    op.drop_index('ix_user_roles_role_id', table_name='user_roles')
    op.drop_index('ix_user_roles_user_id', table_name='user_roles')
    op.drop_table('user_roles')
    
    op.drop_index('ix_role_permissions_permission_id', table_name='role_permissions')
    op.drop_index('ix_role_permissions_role_id', table_name='role_permissions')
    op.drop_table('role_permissions')
    
    op.drop_index('ix_permissions_name', table_name='permissions')
    op.drop_table('permissions')
    
    op.drop_index('ix_roles_name', table_name='roles')
    op.drop_table('roles')
