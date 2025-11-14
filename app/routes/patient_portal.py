# Hasta Portalı - Evrak Yükleme Blueprint
from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file, abort
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

bp = Blueprint('patient_portal', __name__, url_prefix='/portal')

# Bu blueprint hasta girişi için tasarlandı
# Şu an için login_required ile çalışıyor ama gelecekte hasta authentication sistemi eklenebilir

ALLOWED_EXTENSIONS = {'pdf', 'jpg', 'jpeg', 'png', 'doc', 'docx'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@bp.route('/documents')
def my_documents():
    """Hastanın kendi evraklarını görüntüleme"""
    from flask_login import login_required, current_user
    from app.models import Document
    
    # Şu an için normal kullanıcılar hastaymiş gibi davranıyor
    # Gerçek hasta portalında hasta_id session'dan alınacak
    patient_id = request.args.get('patient_id', type=int)
    
    if not patient_id:
        flash('Hasta ID gerekli', 'danger')
        return redirect(url_for('main.dashboard'))
    
    docs = Document.query.filter_by(
        patient_id=patient_id,
        is_archived=False
    ).order_by(Document.uploaded_at.desc()).all()
    
    return render_template('patient_portal/my_documents.html', 
                         documents=docs,
                         patient_id=patient_id)


@bp.route('/documents/upload', methods=['GET', 'POST'])
def upload_document():
    """Hasta evrak yükleme"""
    from flask_login import login_required, current_user
    from flask import current_app
    from app import db
    from app.models import Document, Patient, AuditLog
    
    patient_id = request.args.get('patient_id', type=int) or request.form.get('patient_id', type=int)
    
    if not patient_id:
        flash('Hasta ID gerekli', 'danger')
        return redirect(url_for('main.dashboard'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        # Dosya kontrolü
        if 'file' not in request.files:
            flash('Dosya seçilmedi', 'warning')
            return redirect(request.url)
        
        file = request.files['file']
        
        if file.filename == '':
            flash('Dosya seçilmedi', 'warning')
            return redirect(request.url)
        
        # Dosya boyutu kontrolü
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            flash(f'Dosya çok büyük. Maksimum {MAX_FILE_SIZE // (1024*1024)}MB yüklenebilir.', 'danger')
            return redirect(request.url)
        
        # Dosya tipi kontrolü
        if not allowed_file(file.filename):
            flash(f'Geçersiz dosya tipi. İzin verilen: {", ".join(ALLOWED_EXTENSIONS)}', 'danger')
            return redirect(request.url)
        
        # Güvenli dosya adı
        from app.utils.security import sanitize_filename, validate_file_mime, SAFE_MIME_TYPES
        original_filename = sanitize_filename(secure_filename(file.filename))
        
        # MIME type validation
        if not validate_file_mime(file, list(SAFE_MIME_TYPES)):
            flash('Geçersiz dosya tipi tespit edildi', 'danger')
            return redirect(request.url)
        
        ext = os.path.splitext(original_filename)[1]
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Dosyayı kaydet
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, stored_filename)
        file.save(file_path)
        
        # Veritabanına kaydet
        doc = Document(
            distributor_id=patient.distributor_id,
            patient_id=patient_id,
            uploaded_by=getattr(current_user, 'id', None) if hasattr(current_user, 'id') else None,
            title=request.form.get('title') or original_filename,
            description=request.form.get('description'),
            filename=original_filename,
            stored_filename=stored_filename,
            file_path=f'uploads/{stored_filename}',
            file_size=file_size,
            mime_type=file.content_type,
            document_type=request.form.get('document_type', 'patient_upload'),
            tags='hasta_yüklemesi',
            is_public=False
        )
        
        db.session.add(doc)
        
        # File integrity hash (opsiyonel - ileride integrity check için)
        try:
            from app.utils.security import hash_file_content
            file_hash = hash_file_content(file_path)
            if file_hash:
                doc.tags = f"{doc.tags},hash:{file_hash[:16]}" if doc.tags else f"hash:{file_hash[:16]}"
        except Exception:
            pass
        
        # Encryption placeholder (production'da aktif edilmeli)
        # from app.utils.security import encrypt_file, get_encryption_key
        # encryption_key = get_encryption_key(doc.id)
        # encrypt_file(file_path, encryption_key)
        
        # Audit log
        try:
            audit = AuditLog(
                distributor_id=patient.distributor_id,
                user_id=getattr(current_user, 'id', None),
                action='create',
                entity_type='document',
                entity_id=doc.id,
                note=f'Hasta evrak yükledi: {original_filename}'
            )
            db.session.add(audit)
        except Exception:
            pass
        
        db.session.commit()
        
        # Bildirim: Yöneticilere evrak yüklendi bildirimi
        try:
            from app.utils.notifications import notify_distributor_admins
            notify_distributor_admins(
                patient.distributor_id,
                'Yeni Hasta Evrakı',
                f'{patient.first_name} {patient.last_name} evrak yükledi: {original_filename}',
                url_for('main.view_document', id=doc.id, _external=True),
                'info',
                'document'
            )
        except Exception:
            pass
        
        flash('Evrak başarıyla yüklendi', 'success')
        return redirect(url_for('patient_portal.my_documents', patient_id=patient_id))
    
    return render_template('patient_portal/upload_document.html', 
                         patient=patient,
                         max_size_mb=MAX_FILE_SIZE // (1024*1024),
                         allowed_extensions=ALLOWED_EXTENSIONS)


@bp.route('/documents/<int:doc_id>/download')
def download_document(doc_id):
    """Hastanın kendi evrakını indirme"""
    from flask import current_app
    from app.models import Document
    
    doc = Document.query.get_or_404(doc_id)
    
    # Yetki kontrolü: sadece kendi evrakını indirebilir
    patient_id = request.args.get('patient_id', type=int)
    if doc.patient_id != patient_id:
        abort(403)
    
    file_path = os.path.join(
        current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'),
        doc.stored_filename
    )
    
    if not os.path.exists(file_path):
        flash('Dosya bulunamadı', 'danger')
        return redirect(url_for('patient_portal.my_documents', patient_id=patient_id))
    
    return send_file(file_path, as_attachment=True, download_name=doc.filename)
