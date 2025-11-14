from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from app.models import Distributor, User, AppSettings
from app import db
from functools import wraps
from werkzeug.utils import secure_filename
import os

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

bp = Blueprint('admin', __name__, url_prefix='/admin')

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_admin():
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('main.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def superadmin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not getattr(current_user, 'is_superadmin', lambda: False)():
            flash('Bu sayfaya sadece süper yöneticiler erişebilir', 'danger')
            return redirect(url_for('admin.index'))
        return f(*args, **kwargs)
    return decorated_function

@bp.route('/')
@login_required
@admin_required
def index():
    from app.models.meta_lead import FacebookLead
    
    distributors_count = Distributor.query.count()
    users_count = User.query.count()
    facebook_leads_count = FacebookLead.query.count()
    settings = AppSettings.get()
    return render_template('admin/index.html',
                         distributors_count=distributors_count,
                         users_count=users_count,
                         facebook_leads_count=facebook_leads_count,
                         settings=settings)

@bp.route('/settings', methods=['GET','POST'])
@login_required
@superadmin_required
def settings():
    settings = AppSettings.get()
    if request.method == 'POST':
        settings.enable_hair = bool(request.form.get('enable_hair'))
        settings.enable_teeth = bool(request.form.get('enable_teeth'))
        settings.enable_eye = bool(request.form.get('enable_eye'))
        settings.enable_hotel = bool(request.form.get('enable_hotel'))
        settings.enable_leads = bool(request.form.get('enable_leads'))
        settings.enable_aesthetic = bool(request.form.get('enable_aesthetic'))
        settings.enable_bariatric = bool(request.form.get('enable_bariatric'))
        settings.enable_ivf = bool(request.form.get('enable_ivf'))
        settings.enable_checkup = bool(request.form.get('enable_checkup'))
        settings.theme_color = request.form.get('theme_color') or settings.theme_color
        settings.navbar_style = request.form.get('navbar_style') or settings.navbar_style
        
        # Handle logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename:
                # Check file size (max 1MB)
                file.seek(0, 2)  # Seek to end
                file_size = file.tell()
                file.seek(0)  # Seek back to start
                
                if file_size > 1024 * 1024:  # 1MB
                    flash('Logo dosyası çok büyük! Maksimum 1MB olmalı.', 'danger')
                elif allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    import time
                    filename = f"global_logo_{int(time.time())}_{filename}"
                    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                    
                    # Delete old logo if exists
                    if settings.logo_path:
                        old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], settings.logo_path)
                        if os.path.exists(old_path):
                            os.remove(old_path)
                    
                    file.save(filepath)
                    settings.logo_path = filename
                    flash('Logo başarıyla yüklendi!', 'success')
                else:
                    flash('Geçersiz dosya formatı! Sadece PNG, JPG, JPEG, GIF desteklenmektedir.', 'danger')
        
        db.session.commit()
        flash('Genel ayarlar güncellendi', 'success')
        return redirect(url_for('admin.settings'))
    return render_template('admin/settings.html', settings=settings)

@bp.route('/distributors')
@login_required
@admin_required
def distributors():
    distributors = Distributor.query.all()
    return render_template('admin/distributors.html', distributors=distributors)

@bp.route('/distributor/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_distributor():
    from app.forms import DistributorForm
    form = DistributorForm()
    
    if form.validate_on_submit():
        distributor = Distributor(
            name=form.name.data,
            contact_name=form.contact_name.data,
            phone=form.phone.data,
            email=form.email.data,
            address=form.address.data,
            city=form.city.data,
            country=form.country.data,
            whatsapp=form.whatsapp.data,
            website=form.website.data,
            facebook=form.facebook.data,
            instagram=form.instagram.data,
            twitter=form.twitter.data,
            linkedin=form.linkedin.data,
            hospital_license=form.hospital_license.data,
            tax_number=form.tax_number.data,
            color_hex=form.color_hex.data or '#7a001d',
            pdf_footer_text=form.pdf_footer_text.data,
            enable_hair=form.enable_hair.data,
            enable_teeth=form.enable_teeth.data,
            enable_eye=form.enable_eye.data,
            enable_aesthetic=request.form.get('enable_aesthetic') == 'on',
            enable_bariatric=request.form.get('enable_bariatric') == 'on',
            enable_ivf=request.form.get('enable_ivf') == 'on',
            enable_checkup=request.form.get('enable_checkup') == 'on',
            price_per_graft=form.price_per_graft.data or 0,
            currency=form.currency.data,
            is_active=form.is_active.data
        )
        
        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            if allowed_file(file.filename):
                filename = secure_filename(file.filename)
                # Add timestamp to avoid conflicts
                import time
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                distributor.logo_path = filename
        
        db.session.add(distributor)
        db.session.commit()
        
        # Create distributor admin user if credentials provided
        admin_username = request.form.get('admin_username')
        admin_password = request.form.get('admin_password')
        if admin_username and admin_password:
            admin_user = User(
                distributor_id=distributor.id,
                username=admin_username,
                email=form.email.data,
                role='distributor'
            )
            admin_user.set_password(admin_password)
            db.session.add(admin_user)
            db.session.commit()
        
        flash('Bayi başarıyla eklendi', 'success')
        return redirect(url_for('admin.distributors'))
        
    return render_template('admin/distributor_form.html', form=form)

@bp.route('/distributor/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_distributor(id):
    from app.forms import DistributorForm
    distributor = Distributor.query.get_or_404(id)
    
    if request.method == 'POST':
        # Manuel olarak modül checkbox'larını al (form validation sorununu bypass et)
        distributor.name = request.form.get('name', '')
        distributor.contact_name = request.form.get('contact_name', '')
        distributor.phone = request.form.get('phone', '')
        distributor.email = request.form.get('email', '')
        distributor.address = request.form.get('address', '')
        distributor.city = request.form.get('city', '')
        distributor.country = request.form.get('country', '')
        distributor.whatsapp = request.form.get('whatsapp', '')
        distributor.website = request.form.get('website', '')
        distributor.facebook = request.form.get('facebook', '')
        distributor.instagram = request.form.get('instagram', '')
        distributor.twitter = request.form.get('twitter', '')
        distributor.linkedin = request.form.get('linkedin', '')
        distributor.hospital_license = request.form.get('hospital_license', '')
        distributor.tax_number = request.form.get('tax_number', '')
        distributor.color_hex = request.form.get('color_hex', '#7a001d')
        distributor.pdf_footer_text = request.form.get('pdf_footer_text', '')
        
        # Modül checkbox'ları - checkbox işaretliyse 'on' değeri gelir
        distributor.enable_hair = request.form.get('enable_hair') == 'on'
        distributor.enable_teeth = request.form.get('enable_teeth') == 'on'
        distributor.enable_eye = request.form.get('enable_eye') == 'on'
        distributor.enable_aesthetic = request.form.get('enable_aesthetic') == 'on'
        distributor.enable_bariatric = request.form.get('enable_bariatric') == 'on'
        distributor.enable_ivf = request.form.get('enable_ivf') == 'on'
        distributor.enable_checkup = request.form.get('enable_checkup') == 'on'
        
        # Fiyat ve para birimi
        price_per_graft = request.form.get('price_per_graft', '0')
        try:
            distributor.price_per_graft = float(price_per_graft) if price_per_graft else 0
        except ValueError:
            distributor.price_per_graft = 0
            
        distributor.currency = request.form.get('currency', 'EUR')
        distributor.is_active = request.form.get('is_active') == 'on'
        
        # Logo upload
        if 'logo' in request.files:
            file = request.files['logo']
            if file and file.filename and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                import time
                filename = f"{int(time.time())}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                distributor.logo_path = filename
        
        try:
            db.session.commit()
            flash('Bayi bilgileri güncellendi', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Hata: {str(e)}', 'error')
            
        return redirect(url_for('admin.distributors'))
        
    return render_template('admin/distributor_form.html', distributor=distributor)

@bp.route('/distributor/<int:id>/view')
@login_required
@admin_required
def view_distributor(id):
    from app.models import Patient, Encounter, Lead, APIKey
    from app.models.meta_lead import MetaAPIConfig
    
    distributor = Distributor.query.get_or_404(id)
    users = User.query.filter_by(distributor_id=id).all()
    patients_count = Patient.query.filter_by(distributor_id=id).count()
    encounters_count = Encounter.query.filter_by(distributor_id=id).count()
    leads_count = Lead.query.filter_by(distributor_id=id).count()
    api_keys = APIKey.query.filter_by(distributor_id=id).all()
    meta_config = MetaAPIConfig.query.filter_by(distributor_id=id).first()
    
    return render_template('admin/distributor_detail.html', 
                         distributor=distributor,
                         users=users,
                         patients_count=patients_count,
                         encounters_count=encounters_count,
                         leads_count=leads_count,
                         api_keys=api_keys,
                         meta_config=meta_config)

@bp.route('/distributor/<int:id>/integration', methods=['GET', 'POST'])
@login_required
@admin_required
def distributor_integration(id):
    """Manage lead integration settings for distributor"""
    from app.models import APIKey
    import secrets
    
    distributor = Distributor.query.get_or_404(id)
    
    if request.method == 'POST':
        # Update Facebook settings
        distributor.facebook_page_id = request.form.get('facebook_page_id')
        distributor.facebook_access_token = request.form.get('facebook_access_token')
        distributor.webhook_secret = request.form.get('webhook_secret')
        
        # Generate or update website API key
        if request.form.get('generate_api_key') == 'yes':
            # Check if website API key exists
            existing_key = APIKey.query.filter_by(
                distributor_id=id, 
                key_name='Website Form'
            ).first()
            
            if existing_key:
                # Regenerate
                existing_key.api_key = secrets.token_urlsafe(48)
                existing_key.last_used_at = None
                existing_key.usage_count = 0
                distributor.website_api_key = existing_key.api_key
            else:
                # Create new
                api_key = secrets.token_urlsafe(48)
                new_key = APIKey(
                    distributor_id=id,
                    key_name='Website Form',
                    api_key=api_key,
                    can_create_leads=True,
                    can_read_leads=False,
                    allowed_sources='website',
                    is_active=True,
                    created_by=current_user.id
                )
                db.session.add(new_key)
                distributor.website_api_key = api_key
        
        db.session.commit()
        flash('Entegrasyon ayarları güncellendi', 'success')
        return redirect(url_for('admin.view_distributor', id=id))
    
    api_keys = APIKey.query.filter_by(distributor_id=id).all()
    
    return render_template('admin/distributor_integration.html', 
                         distributor=distributor,
                         api_keys=api_keys)

@bp.route('/distributor/<int:id>/api-key/new', methods=['POST'])
@login_required
@admin_required
def create_distributor_api_key(id):
    """Create new API key for distributor"""
    from app.models import APIKey
    import secrets
    
    distributor = Distributor.query.get_or_404(id)
    
    key_name = request.form.get('key_name', 'Custom Integration')
    allowed_sources = request.form.get('allowed_sources', 'website,facebook,instagram')
    
    api_key = secrets.token_urlsafe(48)
    
    new_key = APIKey(
        distributor_id=id,
        key_name=key_name,
        api_key=api_key,
        can_create_leads=True,
        can_read_leads='can_read_leads' in request.form,
        allowed_sources=allowed_sources,
        is_active=True,
        created_by=current_user.id
    )
    
    db.session.add(new_key)
    db.session.commit()
    
    flash(f'API Key oluşturuldu: {key_name}', 'success')
    return redirect(url_for('admin.distributor_integration', id=id))

@bp.route('/api-key/<int:id>/toggle', methods=['POST'])
@login_required
@admin_required
def toggle_api_key(id):
    """Toggle API key status"""
    from app.models import APIKey
    
    api_key = APIKey.query.get_or_404(id)
    api_key.is_active = not api_key.is_active
    db.session.commit()
    
    status = 'aktif' if api_key.is_active else 'pasif'
    flash(f'API Key {status} edildi', 'success')
    return redirect(request.referrer or url_for('admin.distributors'))

@bp.route('/api-key/<int:id>/delete', methods=['POST'])
@login_required
@admin_required
def delete_api_key(id):
    """Delete API key"""
    from app.models import APIKey
    
    api_key = APIKey.query.get_or_404(id)
    distributor_id = api_key.distributor_id
    
    db.session.delete(api_key)
    db.session.commit()
    
    flash('API Key silindi', 'success')
    return redirect(url_for('admin.distributor_integration', id=distributor_id))


# ========== RBAC MANAGEMENT ==========

@bp.route('/roles')
@login_required
@superadmin_required
def roles():
    """List all roles."""
    from app.models import Role
    roles = Role.query.order_by(Role.name).all()
    return render_template('admin/roles.html', roles=roles)


@bp.route('/roles/new', methods=['GET', 'POST'])
@login_required
@superadmin_required
def new_role():
    """Create new role."""
    from app.models import Role, Permission
    
    if request.method == 'POST':
        name = request.form.get('name')
        display_name = request.form.get('display_name')
        description = request.form.get('description')
        
        if not name or not display_name:
            flash('Rol adı ve görünen adı zorunludur.', 'warning')
            return redirect(request.referrer)
        
        # Check duplicate
        existing = Role.query.filter_by(name=name).first()
        if existing:
            flash('Bu rol adı zaten kullanılıyor.', 'warning')
            return redirect(request.referrer)
        
        role = Role(name=name, display_name=display_name, description=description, is_system=False)
        db.session.add(role)
        db.session.flush()
        
        # Assign permissions
        from app.models import RolePermission
        permission_ids = request.form.getlist('permissions')
        for perm_id in permission_ids:
            rp = RolePermission(role_id=role.id, permission_id=int(perm_id))
            db.session.add(rp)
        
        db.session.commit()
        flash('Rol başarıyla oluşturuldu.', 'success')
        return redirect(url_for('admin.roles'))
    
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    return render_template('admin/role_form.html', role=None, permissions=permissions)


@bp.route('/roles/<int:id>/edit', methods=['GET', 'POST'])
@login_required
@superadmin_required
def edit_role(id):
    """Edit role."""
    from app.models import Role, Permission, RolePermission
    
    role = Role.query.get_or_404(id)
    
    if request.method == 'POST':
        role.display_name = request.form.get('display_name')
        role.description = request.form.get('description')
        
        # Update permissions
        RolePermission.query.filter_by(role_id=role.id).delete()
        permission_ids = request.form.getlist('permissions')
        for perm_id in permission_ids:
            rp = RolePermission(role_id=role.id, permission_id=int(perm_id))
            db.session.add(rp)
        
        db.session.commit()
        flash('Rol güncellendi.', 'success')
        return redirect(url_for('admin.roles'))
    
    permissions = Permission.query.order_by(Permission.category, Permission.name).all()
    role_permission_ids = [rp.permission_id for rp in role.permissions]
    return render_template('admin/role_form.html', role=role, permissions=permissions, role_permission_ids=role_permission_ids)


@bp.route('/roles/<int:id>/delete', methods=['POST'])
@login_required
@superadmin_required
def delete_role(id):
    """Delete role."""
    from app.models import Role
    
    role = Role.query.get_or_404(id)
    
    if role.is_system:
        flash('Sistem rolleri silinemez.', 'danger')
        return redirect(url_for('admin.roles'))
    
    db.session.delete(role)
    db.session.commit()
    flash('Rol silindi.', 'success')
    return redirect(url_for('admin.roles'))


@bp.route('/user/<int:user_id>/roles', methods=['GET', 'POST'])
@login_required
@admin_required
def manage_user_roles(user_id):
    """Manage user roles."""
    from app.models import Role, UserRole
    
    user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        # Remove all roles
        UserRole.query.filter_by(user_id=user.id).delete()
        
        # Add selected roles
        role_ids = request.form.getlist('roles')
        for role_id in role_ids:
            ur = UserRole(user_id=user.id, role_id=int(role_id), granted_by=current_user.id)
            db.session.add(ur)
        
        db.session.commit()
        flash('Kullanıcı rolleri güncellendi.', 'success')
        return redirect(url_for('admin.users'))
    
    roles = Role.query.order_by(Role.name).all()
    user_role_ids = [ur.role_id for ur in user.user_roles]
    return render_template('admin/user_roles.html', user=user, roles=roles, user_role_ids=user_role_ids)

@bp.route('/distributor/<int:dist_id>/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_distributor_user(dist_id):
    distributor = Distributor.query.get_or_404(dist_id)
    
    if request.method == 'POST':
        user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            distributor_id=dist_id,
            role=request.form.get('role', 'staff'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone')
        )
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash(f'{distributor.name} için kullanıcı başarıyla eklendi', 'success')
        return redirect(url_for('admin.view_distributor', id=dist_id))
        
    return render_template('admin/distributor_user_form.html', distributor=distributor)

@bp.route('/users')
@login_required
@admin_required
def users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@bp.route('/user/new', methods=['GET', 'POST'])
@login_required
@admin_required
def new_user():
    if request.method == 'POST':
        user = User(
            username=request.form.get('username'),
            email=request.form.get('email'),
            distributor_id=request.form.get('distributor_id'),
            role=request.form.get('role'),
            first_name=request.form.get('first_name'),
            last_name=request.form.get('last_name'),
            phone=request.form.get('phone')
        )
        user.set_password(request.form.get('password'))
        db.session.add(user)
        db.session.commit()
        flash('Kullanıcı başarıyla eklendi', 'success')
        return redirect(url_for('admin.users'))
        
    distributors = Distributor.query.all()
    return render_template('admin/user_form.html', distributors=distributors)

@bp.route('/user/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_user(id):
    user = User.query.get_or_404(id)
    
    if request.method == 'POST':
        user.username = request.form.get('username')
        user.email = request.form.get('email')
        user.distributor_id = request.form.get('distributor_id')
        user.role = request.form.get('role')
        user.first_name = request.form.get('first_name')
        user.last_name = request.form.get('last_name')
        user.phone = request.form.get('phone')
        
        if request.form.get('password'):
            user.set_password(request.form.get('password'))
            
        db.session.commit()
        flash('Kullanıcı bilgileri güncellendi', 'success')
        return redirect(url_for('admin.users'))
        
    distributors = Distributor.query.all()
    return render_template('admin/user_form.html', user=user, distributors=distributors)


# ==================== Meta/Facebook Lead Integration ====================

@bp.route('/distributor_settings/<int:id>', methods=['GET', 'POST'])
@bp.route('/distributor/<int:id>/meta-settings', methods=['GET', 'POST'])
@login_required
@admin_required
def distributor_settings(id):
    """Distributor settings with Meta integration"""
    from app.models.meta_lead import MetaAPIConfig
    
    distributor = Distributor.query.get_or_404(id)
    meta_config = MetaAPIConfig.query.filter_by(distributor_id=id).first()
    
    if request.method == 'POST':
        # Handle Meta API configuration
        page_id = request.form.get('meta_page_id', '').strip()
        form_id = request.form.get('meta_form_id', '').strip()
        access_token = request.form.get('meta_access_token', '').strip()
        fetch_interval = request.form.get('meta_fetch_interval', '5')
        is_active = request.form.get('meta_is_active') == 'on'
        
        try:
            fetch_interval = max(5, min(1440, int(fetch_interval)))
        except (ValueError, TypeError):
            fetch_interval = 5
        
        if not meta_config:
            meta_config = MetaAPIConfig(distributor_id=id)
            db.session.add(meta_config)
        
        meta_config.page_id = page_id
        meta_config.form_id = form_id
        meta_config.access_token = access_token
        meta_config.fetch_interval_minutes = fetch_interval
        meta_config.is_active = is_active
        
        try:
            db.session.commit()
            flash('Meta API ayarları kaydedildi', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Ayarlar kaydedilirken hata: {str(e)}', 'danger')
        
        return redirect(url_for('admin.distributor_settings', id=id))
    
    return render_template('admin/distributor_meta_settings.html',
                         distributor=distributor,
                         meta_config=meta_config)


@bp.route('/test-meta-connection/<int:distributor_id>', methods=['POST'])
@login_required
@admin_required
def test_meta_connection(distributor_id):
    """Test Meta API connection"""
    from app.models.meta_lead import MetaAPIConfig
    from app.services.meta_lead_service import MetaLeadService
    
    distributor = Distributor.query.get_or_404(distributor_id)
    meta_config = MetaAPIConfig.query.filter_by(distributor_id=distributor_id).first()
    
    if not meta_config or not meta_config.access_token:
        flash('Meta API konfigürasyonu eksik. Lütfen önce ayarları kaydedin.', 'danger')
        return redirect(url_for('admin.view_distributor', id=distributor_id))
    
    try:
        service = MetaLeadService(meta_config)
        success, message = service.test_connection()
        
        if success:
            flash(f'✓ Bağlantı başarılı! {message}', 'success')
        else:
            flash(f'✗ Bağlantı hatası: {message}', 'danger')
    except Exception as e:
        flash(f'✗ Hata: {str(e)}', 'danger')
    
    return redirect(url_for('admin.view_distributor', id=distributor_id))


@bp.route('/sync-meta-leads/<int:distributor_id>', methods=['POST'])
@login_required
@admin_required
def sync_meta_leads(distributor_id):
    """Manually sync Meta leads"""
    from app.models.meta_lead import MetaAPIConfig
    from app.services.meta_lead_service import MetaLeadService
    from app.models.meta_lead import FacebookLead
    
    distributor = Distributor.query.get_or_404(distributor_id)
    meta_config = MetaAPIConfig.query.filter_by(distributor_id=distributor_id).first()
    
    if not meta_config or not meta_config.is_active:
        flash('Meta API konfigürasyonu aktif değil.', 'danger')
        return redirect(url_for('admin.view_distributor', id=distributor_id))
    
    try:
        service = MetaLeadService(meta_config)
        
        # Sync leads
        leads_before = FacebookLead.query.filter_by(distributor_id=distributor_id).count()
        result = service.sync_leads(limit=100)
        leads_after = FacebookLead.query.filter_by(distributor_id=distributor_id).count()
        
        new_leads = leads_after - leads_before
        
        flash(f'✓ Senkronizasyon tamamlandı! Toplam {leads_after} lead, {new_leads} yeni lead', 'success')
    except Exception as e:
        flash(f'✗ Senkronizasyon hatası: {str(e)}', 'danger')
    
    return redirect(url_for('admin.view_distributor', id=distributor_id))


@bp.route('/facebook-leads', methods=['GET'])
@login_required
@admin_required
def facebook_leads_list():
    """List all Facebook leads"""
    from app.models.meta_lead import FacebookLead, MetaAPIConfig
    
    # Get filters
    status = request.args.get('status', '')
    distributor_id = request.args.get('distributor_id', '')
    search = request.args.get('search', '')
    page = request.args.get('page', 1, type=int)
    
    # Build query
    query = FacebookLead.query
    
    if status and status != 'all':
        query = query.filter_by(status=status)
    
    if distributor_id and distributor_id != 'all':
        query = query.filter_by(distributor_id=distributor_id)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (FacebookLead.first_name.ilike(search_term)) |
            (FacebookLead.last_name.ilike(search_term)) |
            (FacebookLead.email.ilike(search_term)) |
            (FacebookLead.phone.ilike(search_term))
        )
    
    # Calculate stats
    all_leads = FacebookLead.query.all()
    high_score_count = len([l for l in all_leads if hasattr(l, 'quality_score') and l.quality_score >= 70])
    medium_score_count = len([l for l in all_leads if hasattr(l, 'quality_score') and 40 <= l.quality_score < 70])
    low_score_count = len([l for l in all_leads if hasattr(l, 'quality_score') and l.quality_score < 40])
    
    # Paginate
    leads = query.order_by(FacebookLead.created_at.desc()).paginate(page=page, per_page=20)
    
    # Get distributors for filter
    distributors = Distributor.query.all()
    
    return render_template('admin/facebook_leads/index.html',
                         leads=leads.items,
                         distributors=distributors,
                         high_score_count=high_score_count,
                         medium_score_count=medium_score_count,
                         low_score_count=low_score_count)
    
    if not config.is_active:
        return {'success': False, 'message': 'Bu konfigürasyon aktif değil'}, 400
    
    service = MetaLeadService(config)
    result = service.sync_leads(limit=100)
    
    return result