from functools import wraps
from flask import abort, flash, redirect, url_for
from flask_login import current_user


def permission_required(permission_name):
    """Decorator to check if current user has a specific permission."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Lütfen giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Superadmin bypass
            if hasattr(current_user, 'is_superadmin') and current_user.is_superadmin():
                return f(*args, **kwargs)
            
            # Check permission
            if not has_permission(current_user, permission_name):
                flash('Bu işlem için yetkiniz yok.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def role_required(role_name):
    """Decorator to check if current user has a specific role."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Lütfen giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            
            # Superadmin bypass
            if hasattr(current_user, 'is_superadmin') and current_user.is_superadmin():
                return f(*args, **kwargs)
            
            # Check role
            if not has_role(current_user, role_name):
                flash('Bu sayfaya erişim yetkiniz yok.', 'danger')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def any_permission_required(*permission_names):
    """Decorator to check if user has at least one of the specified permissions."""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Lütfen giriş yapın.', 'warning')
                return redirect(url_for('auth.login'))
            
            if hasattr(current_user, 'is_superadmin') and current_user.is_superadmin():
                return f(*args, **kwargs)
            
            for perm in permission_names:
                if has_permission(current_user, perm):
                    return f(*args, **kwargs)
            
            flash('Bu işlem için yetkiniz yok.', 'danger')
            abort(403)
        return decorated_function
    return decorator


def has_permission(user, permission_name):
    """Check if user has a specific permission through their roles."""
    from app.models.rbac import Permission, RolePermission, UserRole
    
    # Get user's roles
    user_role_ids = [ur.role_id for ur in user.user_roles]
    if not user_role_ids:
        return False
    
    # Check if any role has the permission
    perm = Permission.query.filter_by(name=permission_name).first()
    if not perm:
        return False
    
    role_perm = RolePermission.query.filter(
        RolePermission.role_id.in_(user_role_ids),
        RolePermission.permission_id == perm.id
    ).first()
    
    return role_perm is not None


def has_role(user, role_name):
    """Check if user has a specific role."""
    from app.models.rbac import Role, UserRole
    
    role = Role.query.filter_by(name=role_name).first()
    if not role:
        return False
    
    user_role = UserRole.query.filter_by(user_id=user.id, role_id=role.id).first()
    return user_role is not None


def get_user_permissions(user):
    """Get all permission names for a user."""
    from app.models.rbac import Permission, RolePermission
    
    if hasattr(user, 'is_superadmin') and user.is_superadmin():
        # Superadmin has all permissions
        return [p.name for p in Permission.query.all()]
    
    user_role_ids = [ur.role_id for ur in user.user_roles]
    if not user_role_ids:
        return []
    
    permission_ids = [rp.permission_id for rp in RolePermission.query.filter(
        RolePermission.role_id.in_(user_role_ids)
    ).all()]
    
    permissions = Permission.query.filter(Permission.id.in_(permission_ids)).all()
    return [p.name for p in permissions]


def get_user_roles(user):
    """Get all role names for a user."""
    return [ur.role.name for ur in user.user_roles]
