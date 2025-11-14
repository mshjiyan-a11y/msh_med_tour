from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify, current_app
from flask_login import login_required, current_user
from functools import wraps
from app.models import FacebookLead, MetaAPIConfig, LeadInteraction, User
from app.services.meta_lead_service import MetaLeadService
from app import db
from datetime import datetime
import logging
import json

logger = logging.getLogger(__name__)

bp = Blueprint('facebook_leads', __name__, url_prefix='/admin/facebook-leads')


def require_superadmin(f):
    """Require superadmin access"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not getattr(current_user, 'is_superadmin', False):
            flash('Bu sayfaya erişim yetkiniz yok', 'danger')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function


@bp.route('/')
@login_required
@require_superadmin
def index():
    """Facebook leads dashboard"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', 'all')
    distributor_filter = request.args.get('distributor', 'all')
    search = request.args.get('search', '').strip()
    
    query = FacebookLead.query
    
    # Apply filters
    if status_filter != 'all':
        query = query.filter_by(status=status_filter)
    
    if distributor_filter != 'all':
        try:
            distributor_id = int(distributor_filter)
            query = query.filter_by(distributor_id=distributor_id)
        except:
            pass
    
    if search:
        search_pattern = f"%{search}%"
        query = query.filter(
            (FacebookLead.first_name.ilike(search_pattern)) |
            (FacebookLead.last_name.ilike(search_pattern)) |
            (FacebookLead.email.ilike(search_pattern)) |
            (FacebookLead.phone.ilike(search_pattern))
        )
    
    # Get status counts
    status_counts = {
        'new': FacebookLead.query.filter_by(status='new').count(),
        'assigned': FacebookLead.query.filter_by(status='assigned').count(),
        'contacted': FacebookLead.query.filter_by(status='contacted').count(),
        'converted': FacebookLead.query.filter_by(status='converted').count(),
        'rejected': FacebookLead.query.filter_by(status='rejected').count(),
    }
    
    # Get all Meta configs for distributor selection
    meta_configs = MetaAPIConfig.query.all()
    
    # Paginate
    leads_page = query.order_by(FacebookLead.created_at.desc()).paginate(
        page=page, per_page=25
    )
    
    return render_template('admin/facebook_leads/index.html',
                         leads_page=leads_page,
                         status_counts=status_counts,
                         meta_configs=meta_configs,
                         current_status=status_filter,
                         current_distributor=distributor_filter,
                         search_query=search)


@bp.route('/<int:lead_id>')
@login_required
@require_superadmin
def view_lead(lead_id):
    """View lead details"""
    lead = FacebookLead.query.get_or_404(lead_id)
    interactions = LeadInteraction.query.filter_by(lead_id=lead_id).order_by(
        LeadInteraction.created_at.desc()
    ).all()
    
    return render_template('admin/facebook_leads/view.html',
                         lead=lead,
                         interactions=interactions)


@bp.route('/<int:lead_id>/status', methods=['POST'])
@login_required
@require_superadmin
def update_status(lead_id):
    """Update lead status"""
    lead = FacebookLead.query.get_or_404(lead_id)
    new_status = request.form.get('status', '').strip()
    
    valid_statuses = ['new', 'assigned', 'contacted', 'converted', 'rejected']
    if new_status not in valid_statuses:
        flash('Geçersiz durum', 'danger')
        return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))
    
    old_status = lead.status
    lead.status = new_status
    lead.updated_at = datetime.utcnow()
    
    # Create interaction record
    interaction = LeadInteraction(
        lead_id=lead_id,
        user_id=current_user.id,
        interaction_type='status_changed',
        description=f"{old_status} → {new_status}",
        result='success'
    )
    
    try:
        db.session.add(interaction)
        db.session.commit()
        flash(f'Lead durumu güncellendi: {new_status}', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Status update hatası: {str(e)}")
        flash('Durum güncellenirken hata oluştu', 'danger')
    
    return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))


@bp.route('/<int:lead_id>/assign', methods=['POST'])
@login_required
@require_superadmin
def assign_lead(lead_id):
    """Assign lead to staff"""
    lead = FacebookLead.query.get_or_404(lead_id)
    user_id = request.form.get('user_id', type=int)
    
    if not user_id:
        flash('Personel seçilmedi', 'danger')
        return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))
    
    user = User.query.get(user_id)
    if not user:
        flash('Personel bulunamadı', 'danger')
        return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))
    
    lead.assigned_to_id = user_id
    lead.status = 'assigned'
    lead.updated_at = datetime.utcnow()
    
    # Create interaction
    interaction = LeadInteraction(
        lead_id=lead_id,
        user_id=current_user.id,
        interaction_type='status_changed',
        description=f"Lead atandı: {user.username}",
        result='success'
    )
    
    try:
        db.session.add(interaction)
        db.session.commit()
        flash(f'Lead {user.username} kullanıcısına atandı', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Assign hatası: {str(e)}")
        flash('Atanırken hata oluştu', 'danger')
    
    return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))


@bp.route('/<int:lead_id>/note', methods=['POST'])
@login_required
@require_superadmin
def add_note(lead_id):
    """Add note to lead"""
    lead = FacebookLead.query.get_or_404(lead_id)
    note = request.form.get('note', '').strip()
    
    if not note:
        flash('Not boş olamaz', 'danger')
        return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))
    
    # Create interaction
    interaction = LeadInteraction(
        lead_id=lead_id,
        user_id=current_user.id,
        interaction_type='note',
        description=note,
        result='success'
    )
    
    try:
        db.session.add(interaction)
        db.session.commit()
        flash('Not eklendi', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Note ekleme hatası: {str(e)}")
        flash('Not eklenirken hata oluştu', 'danger')
    
    return redirect(url_for('facebook_leads.view_lead', lead_id=lead_id))


@bp.route('/<int:lead_id>/delete', methods=['POST'])
@login_required
@require_superadmin
def delete_lead(lead_id):
    """Delete lead"""
    lead = FacebookLead.query.get_or_404(lead_id)
    
    try:
        # Delete interactions first
        LeadInteraction.query.filter_by(lead_id=lead_id).delete()
        db.session.delete(lead)
        db.session.commit()
        flash('Lead silindi', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Lead silme hatası: {str(e)}")
        flash('Lead silinirken hata oluştu', 'danger')
    
    return redirect(url_for('facebook_leads.index'))


@bp.route('/config/<int:config_id>/test', methods=['POST'])
@login_required
@require_superadmin
def test_meta_connection(config_id):
    """Test Meta API connection"""
    config = MetaAPIConfig.query.get_or_404(config_id)
    
    service = MetaLeadService(config)
    success, message = service.test_connection()
    
    if success:
        flash(f'✅ {message}', 'success')
    else:
        flash(f'❌ {message}', 'danger')
    
    return redirect(url_for('admin.distributor_settings', distributor_id=config.distributor_id))


@bp.route('/config/<int:config_id>/sync', methods=['POST'])
@login_required
@require_superadmin
def sync_leads(config_id):
    """Manually sync leads from Meta"""
    config = MetaAPIConfig.query.get_or_404(config_id)
    
    if not config.is_active:
        flash('Bu config etkinleştirilmemiş', 'danger')
        return redirect(url_for('admin.distributor_settings', distributor_id=config.distributor_id))
    
    service = MetaLeadService(config)
    result = service.sync_leads(limit=100)
    
    message = f"Sonuç: {result['message']}"
    if result['errors']:
        message += f" | Hatalar: {'; '.join(result['errors'][:2])}"
    
    flash(message, 'success' if result['success'] else 'danger')
    return redirect(url_for('admin.distributor_settings', distributor_id=config.distributor_id))


@bp.route('/api/stats')
@login_required
@require_superadmin
def api_stats():
    """Get lead statistics via API"""
    stats = {
        'total': FacebookLead.query.count(),
        'new': FacebookLead.query.filter_by(status='new').count(),
        'assigned': FacebookLead.query.filter_by(status='assigned').count(),
        'contacted': FacebookLead.query.filter_by(status='contacted').count(),
        'converted': FacebookLead.query.filter_by(status='converted').count(),
        'rejected': FacebookLead.query.filter_by(status='rejected').count(),
    }
    return jsonify(stats)


@bp.route('/api/recent')
@login_required
@require_superadmin
def api_recent_leads():
    """Get recent leads via API"""
    limit = request.args.get('limit', 10, type=int)
    
    leads = FacebookLead.query.order_by(
        FacebookLead.created_at.desc()
    ).limit(limit).all()
    
    return jsonify({
        'leads': [lead.to_dict() for lead in leads]
    })


# ==================== BULK OPERATIONS ====================

@bp.route('/bulk/status', methods=['POST'])
@login_required
@require_superadmin
def bulk_status():
    """Bulk status change"""
    from app.services.bulk_operations import BulkLeadOperations
    
    lead_ids = request.form.getlist('lead_ids', type=int)
    new_status = request.form.get('status', '').strip()
    
    if not lead_ids:
        flash('Lead seçilmedi', 'warning')
        return redirect(url_for('facebook_leads.index'))
    
    result = BulkLeadOperations.bulk_status_change(lead_ids, new_status, current_user.id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    
    return redirect(url_for('facebook_leads.index'))


@bp.route('/bulk/assign', methods=['POST'])
@login_required
@require_superadmin
def bulk_assign():
    """Bulk assign leads"""
    from app.services.bulk_operations import BulkLeadOperations
    
    lead_ids = request.form.getlist('lead_ids', type=int)
    user_id = request.form.get('user_id', type=int)
    
    if not lead_ids or not user_id:
        flash('Lead veya personel seçilmedi', 'warning')
        return redirect(url_for('facebook_leads.index'))
    
    result = BulkLeadOperations.bulk_assign(lead_ids, current_user.id, user_id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    
    return redirect(url_for('facebook_leads.index'))


@bp.route('/bulk/delete', methods=['POST'])
@login_required
@require_superadmin
def bulk_delete():
    """Bulk delete leads"""
    from app.services.bulk_operations import BulkLeadOperations
    
    lead_ids = request.form.getlist('lead_ids', type=int)
    
    if not lead_ids:
        flash('Lead seçilmedi', 'warning')
        return redirect(url_for('facebook_leads.index'))
    
    result = BulkLeadOperations.bulk_delete(lead_ids, current_user.id)
    
    if result['success']:
        flash(result['message'], 'success')
    else:
        flash(result['message'], 'danger')
    
    return redirect(url_for('facebook_leads.index'))


@bp.route('/bulk/export', methods=['POST'])
@login_required
@require_superadmin
def bulk_export():
    """Export leads"""
    from app.services.bulk_operations import BulkLeadOperations
    from flask import send_file
    
    lead_ids = request.form.getlist('lead_ids', type=int)
    export_format = request.form.get('format', 'csv')
    
    if not lead_ids:
        flash('Lead seçilmedi', 'warning')
        return redirect(url_for('facebook_leads.index'))
    
    result = BulkLeadOperations.export_leads(lead_ids, export_format)
    
    if not result:
        flash('Export hatası', 'danger')
        return redirect(url_for('facebook_leads.index'))
    
    from io import BytesIO
    
    if export_format == 'csv':
        output = BytesIO()
        output.write(result.encode('utf-8-sig'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'facebook_leads_export.csv'
        )
    
    elif export_format == 'json':
        output = BytesIO()
        output.write(result.encode('utf-8'))
        output.seek(0)
        
        return send_file(
            output,
            mimetype='application/json',
            as_attachment=True,
            download_name=f'facebook_leads_export.json'
        )
    
    flash('Desteklenmeyen format', 'danger')
    return redirect(url_for('facebook_leads.index'))


@bp.route('/api/scoring')
@login_required
@require_superadmin
def api_scoring():
    """Get lead scores via API"""
    from app.services.lead_scoring import LeadScoringEngine
    
    leads = FacebookLead.query.all()
    scores = LeadScoringEngine.batch_score_leads(leads)
    
    return jsonify(scores)


@bp.route('/scoring-dashboard')
@login_required
@require_superadmin
def scoring_dashboard():
    """Lead scoring and prioritization dashboard"""
    from app.services.lead_scoring import LeadScoringEngine
    
    # Get top leads
    top_leads = LeadScoringEngine.get_top_leads(limit=20)
    
    # Get recommendations
    recommendations = LeadScoringEngine.get_priority_recommendations()
    
    # Score distribution
    all_leads = FacebookLead.query.all()
    scores = {}
    for lead in all_leads:
        score = LeadScoringEngine.calculate_score(lead)
        level = LeadScoringEngine.get_score_level(score)
        scores[level] = scores.get(level, 0) + 1
    
    return render_template(
        'admin/facebook_leads/scoring_dashboard.html',
        top_leads=top_leads,
        recommendations=recommendations,
        score_distribution=scores
    )


# ==================== ANALYTICS ====================

@bp.route('/analytics')
@login_required
@require_superadmin
def analytics():
    """Analytics and reporting dashboard"""
    from app.services.lead_analytics import LeadAnalytics
    
    funnel = LeadAnalytics.get_conversion_funnel(30)
    by_distributor = LeadAnalytics.get_source_analysis()
    by_user = LeadAnalytics.get_assignment_analytics()
    interaction_stats = LeadAnalytics.get_interaction_stats()
    response_time = LeadAnalytics.get_response_time_stats()
    
    return render_template(
        'admin/facebook_leads/analytics.html',
        funnel=funnel,
        by_distributor=by_distributor,
        by_user=by_user,
        interaction_stats=interaction_stats,
        response_time=response_time
    )


@bp.route('/analytics/report')
@login_required
@require_superadmin
def analytics_report():
    """Generate and download report"""
    from app.services.lead_analytics import LeadAnalytics
    
    report_type = request.args.get('type', 'monthly')
    format_type = request.args.get('format', 'html')
    
    if format_type == 'json':
        report = LeadAnalytics.export_report_json(report_type)
        return jsonify(json.loads(report))
    
    else:
        report = LeadAnalytics.export_report_html(report_type)
        return report, 200, {'Content-Type': 'text/html; charset=utf-8'}
