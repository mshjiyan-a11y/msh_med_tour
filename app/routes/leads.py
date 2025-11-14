from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models import Lead, LeadNote, APIKey, Patient
from app import db
from datetime import datetime
import secrets

bp = Blueprint('leads', __name__, url_prefix='/leads')

@bp.before_request
def ensure_leads_enabled():
    try:
        from app.models.settings import AppSettings
        settings = AppSettings.get()
        # Allow superadmin to access even if disabled (for debugging)
        if not settings.enable_leads and not getattr(current_user, 'is_superadmin', lambda: False)():
            abort(404)
    except Exception:
        # If settings not available (e.g., during migration), allow access
        pass

@bp.route('/')
@login_required
def index():
    """List all leads for current distributor"""
    status_filter = request.args.get('status', 'all')
    source_filter = request.args.get('source', 'all')
    page = request.args.get('page', 1, type=int)
    
    query = Lead.query.filter_by(distributor_id=current_user.distributor_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if source_filter != 'all':
        query = query.filter_by(source=source_filter)
    
    leads = query.order_by(Lead.created_at.desc()).paginate(page=page, per_page=20)
    
    # Get counts by status
    status_counts = {
        'new': Lead.query.filter_by(distributor_id=current_user.distributor_id, status='new').count(),
        'contacted': Lead.query.filter_by(distributor_id=current_user.distributor_id, status='contacted').count(),
        'qualified': Lead.query.filter_by(distributor_id=current_user.distributor_id, status='qualified').count(),
        'converted': Lead.query.filter_by(distributor_id=current_user.distributor_id, status='converted').count(),
        'rejected': Lead.query.filter_by(distributor_id=current_user.distributor_id, status='rejected').count(),
    }
    
    return render_template('leads/index.html',
                         leads=leads,
                         status_counts=status_counts,
                         status_filter=status_filter,
                         source_filter=source_filter)

@bp.route('/export')
@login_required
def export_leads():
    """Export leads to Excel"""
    from flask import send_file
    from app.utils.export import export_leads_to_excel
    
    status_filter = request.args.get('status', 'all')
    source_filter = request.args.get('source', 'all')
    
    query = Lead.query.filter_by(distributor_id=current_user.distributor_id)
    
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if source_filter != 'all':
        query = query.filter_by(source=source_filter)
    
    leads = query.order_by(Lead.created_at.desc()).all()
    excel_file = export_leads_to_excel(leads)
    
    filename = f"leadler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/<int:id>')
@login_required
def detail(id):
    """View lead details"""
    lead = Lead.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    notes = lead.notes.order_by(LeadNote.created_at.desc()).all()
    
    return render_template('leads/detail.html', lead=lead, notes=notes)

@bp.route('/<int:id>/update_status', methods=['POST'])
@login_required
def update_status(id):
    """Update lead status"""
    lead = Lead.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    new_status = request.form.get('status')
    if new_status in ['new', 'contacted', 'qualified', 'converted', 'rejected']:
        lead.status = new_status
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Lead durumu güncellendi', 'success')
    
    return redirect(url_for('leads.detail', id=id))

@bp.route('/<int:id>/add_note', methods=['POST'])
@login_required
def add_note(id):
    """Add note to lead"""
    lead = Lead.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    note_text = request.form.get('note')
    if note_text:
        note = LeadNote(
            lead_id=lead.id,
            user_id=current_user.id,
            note=note_text
        )
        db.session.add(note)
        lead.updated_at = datetime.utcnow()
        db.session.commit()
        flash('Not eklendi', 'success')
    
    return redirect(url_for('leads.detail', id=id))

@bp.route('/<int:id>/convert', methods=['GET', 'POST'])
@login_required
def convert_to_patient(id):
    """Convert lead to patient"""
    lead = Lead.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if lead.is_converted:
        flash('Bu lead zaten hastaya dönüştürülmüş', 'warning')
        return redirect(url_for('leads.detail', id=id))
    
    if request.method == 'POST':
        # Create patient from lead
        patient = Patient(
            distributor_id=lead.distributor_id,
            first_name=lead.first_name or '',
            last_name=lead.last_name or '',
            phone=lead.phone or '',
            email=lead.email,
            nationality=lead.country,
            notes=f"Lead'den dönüştürüldü (#{lead.id})\nKaynak: {lead.source}\n{lead.message or ''}"
        )
        
        db.session.add(patient)
        db.session.flush()
        
        # Update lead
        lead.status = 'converted'
        lead.converted_to_patient_id = patient.id
        lead.converted_at = datetime.utcnow()
        
        # Add conversion note
        note = LeadNote(
            lead_id=lead.id,
            user_id=current_user.id,
            note=f'Lead hastaya dönüştürüldü (Hasta #{patient.id})'
        )
        db.session.add(note)
        
        db.session.commit()
        
        flash(f'Lead başarıyla hastaya dönüştürüldü', 'success')
        return redirect(url_for('main.patient_detail', id=patient.id))
    
    return render_template('leads/convert.html', lead=lead)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete lead"""
    lead = Lead.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if lead.is_converted:
        flash('Dönüştürülmüş lead silinemez', 'danger')
        return redirect(url_for('leads.detail', id=id))
    
    db.session.delete(lead)
    db.session.commit()
    
    flash('Lead silindi', 'success')
    return redirect(url_for('leads.index'))


# ========== API KEY MANAGEMENT ==========

@bp.route('/api-keys')
@login_required
def api_keys():
    """View API keys (read-only for non-admins)"""
    keys = APIKey.query.filter_by(distributor_id=current_user.distributor_id).all()
    return render_template('leads/api_keys.html', api_keys=keys)

# API Key management moved to admin panel only
