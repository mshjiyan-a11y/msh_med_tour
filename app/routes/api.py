from flask import Blueprint, jsonify, request, url_for
from flask_login import login_required, current_user
from app.models import (
    Encounter, HairAnnotation, HairPatternSelection,
    DentalProcedure, EyeRefraction, EyeTreatmentSelection,
    Lead, LeadNote, APIKey,
    AestheticProcedure, BariatricSurgery, IVFTreatment, 
    CheckUpPackage, CheckUpTest
)
from app import db
from app.utils.email import send_new_lead_notification
from functools import wraps
from datetime import datetime
import secrets
import json
from app import socketio

bp = Blueprint('api', __name__, url_prefix='/api')


def require_api_key(f):
    """Decorator to validate API key"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.headers.get('X-API-Key') or request.args.get('api_key')
        
        if not api_key:
            return jsonify({'error': 'API key required'}), 401
        
        key_obj = APIKey.query.filter_by(api_key=api_key, is_active=True).first()
        
        if not key_obj:
            return jsonify({'error': 'Invalid API key'}), 401
        
        # Check expiration
        if key_obj.expires_at and key_obj.expires_at < datetime.utcnow():
            return jsonify({'error': 'API key expired'}), 401
        
        # Update usage stats
        key_obj.last_used_at = datetime.utcnow()
        key_obj.usage_count += 1
        db.session.commit()
        
        # Add to request context
        request.api_key_obj = key_obj
        request.distributor = key_obj.distributor
        
        return f(*args, **kwargs)
    
    return decorated_function


# ========== LEAD MANAGEMENT API ==========

@bp.route('/v1/leads', methods=['POST'])
@require_api_key
def create_lead():
    """Create a new lead from web form or external source"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Validate required fields
        if not data.get('first_name') and not data.get('last_name'):
            return jsonify({'error': 'At least first_name or last_name required'}), 400
        
        # Check source permission
        source = data.get('source', 'website')
        if request.api_key_obj.allowed_sources:
            allowed = request.api_key_obj.allowed_sources.split(',')
            if source not in allowed:
                return jsonify({'error': f'Source {source} not allowed for this API key'}), 403
        
        # Create lead
        lead = Lead(
            distributor_id=request.distributor.id,
            source=source,
            source_id=data.get('source_id'),
            campaign_name=data.get('campaign_name'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            phone=data.get('phone'),
            country=data.get('country'),
            city=data.get('city'),
            age=data.get('age'),
            interested_service=data.get('interested_service'),
            message=data.get('message'),
            status='new',
            priority=data.get('priority', 'medium'),
            raw_data=json.dumps(data),
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent', '')[:255]
        )
        
        db.session.add(lead)
        db.session.commit()
        
        # Send email notification
        try:
            send_new_lead_notification(lead, request.distributor)
        except Exception as email_error:
            # Log error but don't fail the API call
            print(f"Email notification failed: {email_error}")
        
        return jsonify({
            'success': True,
            'lead_id': lead.id,
            'message': 'Lead created successfully',
            'data': {
                'id': lead.id,
                'full_name': lead.full_name,
                'status': lead.status,
                'created_at': lead.created_at.isoformat()
            }
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@bp.route('/v1/leads/<int:lead_id>', methods=['GET'])
@require_api_key
def get_lead(lead_id):
    """Get lead details"""
    if not request.api_key_obj.can_read_leads:
        return jsonify({'error': 'Permission denied'}), 403
    
    lead = Lead.query.filter_by(
        id=lead_id,
        distributor_id=request.distributor.id
    ).first_or_404()
    
    return jsonify({
        'id': lead.id,
        'full_name': lead.full_name,
        'email': lead.email,
        'phone': lead.phone,
        'source': lead.source,
        'status': lead.status,
        'interested_service': lead.interested_service,
        'created_at': lead.created_at.isoformat()
    })


@bp.route('/v1/facebook/webhook', methods=['GET', 'POST'])
def facebook_webhook():
    """Facebook Lead Ads Webhook"""
    
    # Webhook verification
    if request.method == 'GET':
        verify_token = request.args.get('hub.verify_token')
        challenge = request.args.get('hub.challenge')
        
        VERIFY_TOKEN = 'msh_med_tour_2025_verify'
        
        if verify_token == VERIFY_TOKEN:
            return challenge
        else:
            return 'Invalid verify token', 403
    
    # Receive lead data
    elif request.method == 'POST':
        try:
            data = request.get_json()
            
            if data.get('object') == 'page':
                for entry in data.get('entry', []):
                    for change in entry.get('changes', []):
                        if change.get('field') == 'leadgen':
                            lead_data = change.get('value', {})
                            leadgen_id = lead_data.get('leadgen_id')
                            # TODO: Process with Graph API
                            print(f"Facebook Lead received: {leadgen_id}")
            
            return jsonify({'success': True}), 200
            
        except Exception as e:
            print(f"Facebook webhook error: {e}")
            return jsonify({'error': str(e)}), 500


# ========== EXISTING ENCOUNTER API ==========

@bp.route('/encounter/<int:encounter_id>/hair', methods=['POST'])
@login_required
def save_hair_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Save annotations
    if 'annotations' in data:
        # Clear existing annotations
        HairAnnotation.query.filter_by(encounter_id=encounter_id).delete()
        
        for annotation in data['annotations']:
            new_annotation = HairAnnotation(
                encounter_id=encounter_id,
                region_id=annotation['region_id'],
                label=annotation['label'],
                note=annotation.get('note', '')
            )
            db.session.add(new_annotation)
    
    # Save pattern selection
    if 'pattern' in data:
        # Clear existing pattern
        HairPatternSelection.query.filter_by(encounter_id=encounter_id).delete()
        
        new_pattern = HairPatternSelection(
            encounter_id=encounter_id,
            pattern_key=data['pattern']['key'],
            note=data['pattern'].get('note', '')
        )
        db.session.add(new_pattern)
    
    db.session.commit()
    return jsonify({'status': 'success'})


# ========== MESSAGING API ==========

@bp.route('/v1/messages', methods=['POST'])
@require_api_key
def create_message():
    """Create an inbound patient message and optionally auto-reply via chatbot.

    Request JSON:
    - patient_id: int (required)
    - content: str (required)
    - journey_id: int (optional)
    """
    from app.models import Message, CommunicationLog, Patient, PatientJourney
    from app.utils.translation_service import detect_language, translate_text, should_translate, get_language_name
    from app.utils.chatbot_service import should_auto_respond, generate_response, get_chatbot_signature

    data = request.get_json(silent=True) or {}
    patient_id = data.get('patient_id')
    content = (data.get('content') or '').strip()
    journey_id = data.get('journey_id')

    if not patient_id or not content:
        return jsonify({'error': 'patient_id and content are required'}), 400

    # Validate patient belongs to distributor of API key
    patient = Patient.query.filter_by(id=patient_id, distributor_id=request.distributor.id).first()
    if not patient:
        return jsonify({'error': 'patient not found'}), 404

    # Language detect and optional translation to staff language (default tr)
    detected_language = detect_language(content)
    target_language = getattr(patient, 'preferred_language', None) or 'tr'
    translated_content = None
    if should_translate(detected_language, target_language):
        translated_content = translate_text(content, target_language, detected_language)

    # Persist inbound message (sender_id None => patient side)
    msg = Message(
        distributor_id=request.distributor.id,
        sender_id=None,
        patient_id=patient_id,
        journey_id=journey_id,
        content=content,
        message_type='text',
        detected_language=detected_language,
        target_language=target_language if translated_content else None,
        translated_content=translated_content,
        is_bot_message=False
    )
    db.session.add(msg)

    # Communication log
    clog = CommunicationLog(
        distributor_id=request.distributor.id,
        patient_id=patient_id,
        user_id=None,
        journey_id=journey_id,
        communication_type='chat',
        direction='inbound',
        content=content,
        status='completed'
    )
    db.session.add(clog)
    db.session.commit()

    # Emit inbound to room
    room = f"patient_{patient_id}"
    socketio.emit('new_message', {
        'id': msg.id,
        'patient_id': patient_id,
        'sender_id': None,
        'sender_username': 'Hasta',
        'content': msg.content,
        'message_type': msg.message_type,
        'detected_language': msg.detected_language,
        'detected_language_name': get_language_name(msg.detected_language) if msg.detected_language else None,
        'target_language': msg.target_language,
        'translated_content': msg.translated_content,
        'created_at': msg.created_at.strftime('%d.%m.%Y %H:%M')
    }, to=room)

    bot_message_id = None
    # Auto-respond if eligible
    try:
        if should_auto_respond(content, sender_is_staff=False, patient_id=patient_id):
            bot_text, rtype = generate_response(content, detected_language)
            if bot_text:
                bot_full = f"{bot_text}{get_chatbot_signature()}"
                bot_msg = Message(
                    distributor_id=request.distributor.id,
                    sender_id=None,
                    patient_id=patient_id,
                    journey_id=journey_id,
                    content=bot_full,
                    message_type='text',
                    detected_language=detected_language,
                    is_bot_message=True
                )
                db.session.add(bot_msg)
                db.session.commit()
                bot_message_id = bot_msg.id

                socketio.emit('new_message', {
                    'id': bot_msg.id,
                    'patient_id': patient_id,
                    'sender_id': None,
                    'sender_username': '🤖 Asistan',
                    'content': bot_msg.content,
                    'message_type': 'text',
                    'detected_language': bot_msg.detected_language,
                    'is_bot': True,
                    'created_at': bot_msg.created_at.strftime('%d.%m.%Y %H:%M')
                }, to=room)
    except Exception as e:
        # Fail-safe: don't block inbound processing
        pass

    return jsonify({
        'success': True,
        'message_id': msg.id,
        'bot_message_id': bot_message_id
    }), 201

@bp.route('/encounter/<int:encounter_id>/dental', methods=['POST'])
@login_required
def save_dental_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Clear existing procedures
    DentalProcedure.query.filter_by(encounter_id=encounter_id).delete()
    
    # Save new procedures
    for procedure in data['procedures']:
        new_procedure = DentalProcedure(
            encounter_id=encounter_id,
            tooth_no=procedure['tooth_no'],
            treatment_type=procedure['treatment_type'],
            note=procedure.get('note', ''),
            price=procedure.get('price', 0)
        )
        db.session.add(new_procedure)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/encounter/<int:encounter_id>/eye', methods=['POST'])
@login_required
def save_eye_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Save refraction data
    if 'refraction' in data:
        # Clear existing refraction
        EyeRefraction.query.filter_by(encounter_id=encounter_id).delete()
        
        refraction = data['refraction']
        new_refraction = EyeRefraction(
            encounter_id=encounter_id,
            od_sph=refraction.get('od_sph'),
            od_cyl=refraction.get('od_cyl'),
            od_ax=refraction.get('od_ax'),
            os_sph=refraction.get('os_sph'),
            os_cyl=refraction.get('os_cyl'),
            os_ax=refraction.get('os_ax'),
            planned_procedure=refraction.get('planned_procedure'),
            note=refraction.get('note', '')
        )
        db.session.add(new_refraction)
    
    # Save treatment selections
    if 'treatments' in data:
        # Clear existing treatments
        EyeTreatmentSelection.query.filter_by(encounter_id=encounter_id).delete()
        
        for treatment in data['treatments']:
            new_treatment = EyeTreatmentSelection(
                encounter_id=encounter_id,
                code=treatment['code'],
                title=treatment['title'],
                side=treatment.get('side'),
                price=treatment.get('price', 0),
                note=treatment.get('note', '')
            )
            db.session.add(new_treatment)
    
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/encounter/<int:encounter_id>/aesthetic', methods=['POST'])
@login_required
def save_aesthetic_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Clear existing aesthetic data
    AestheticProcedure.query.filter_by(encounter_id=encounter_id).delete()
    
    # Create new aesthetic procedure
    aesthetic = AestheticProcedure(
        encounter_id=encounter_id,
        procedure_type=data.get('procedure_type'),
        price=data.get('price', 0),
        currency=data.get('currency', 'USD'),
        notes=data.get('notes', '')
    )
    db.session.add(aesthetic)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/encounter/<int:encounter_id>/bariatric', methods=['POST'])
@login_required
def save_bariatric_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Clear existing bariatric data
    BariatricSurgery.query.filter_by(encounter_id=encounter_id).delete()
    
    # Create new bariatric surgery record
    bariatric = BariatricSurgery(
        encounter_id=encounter_id,
        surgery_type=data.get('surgery_type'),
        weight_kg=data.get('weight_kg'),
        height_cm=data.get('height_cm'),
        price=data.get('price', 0),
        currency=data.get('currency', 'USD'),
        notes=data.get('notes', '')
    )
    # BMI will be calculated automatically by the model
    db.session.add(bariatric)
    db.session.commit()
    return jsonify({'status': 'success', 'bmi': bariatric.bmi})

@bp.route('/encounter/<int:encounter_id>/ivf', methods=['POST'])
@login_required
def save_ivf_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Clear existing IVF data
    IVFTreatment.query.filter_by(encounter_id=encounter_id).delete()
    
    # Create new IVF treatment record
    ivf = IVFTreatment(
        encounter_id=encounter_id,
        treatment_type=data.get('treatment_type'),
        cycle_number=data.get('cycle_number', 1),
        female_age=data.get('female_age'),
        price=data.get('price', 0),
        currency=data.get('currency', 'USD'),
        notes=data.get('notes', '')
    )
    db.session.add(ivf)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/encounter/<int:encounter_id>/checkup', methods=['POST'])
@login_required
def save_checkup_data(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    data = request.get_json()
    
    # Clear existing checkup data
    CheckUpPackage.query.filter_by(encounter_id=encounter_id).delete()
    
    # Create new checkup package
    checkup = CheckUpPackage(
        encounter_id=encounter_id,
        package_type=data.get('package_type'),
        tests_included=data.get('tests_included', ''),
        price=data.get('price', 0),
        currency=data.get('currency', 'USD'),
        notes=data.get('notes', '')
    )
    db.session.add(checkup)
    db.session.commit()
    return jsonify({'status': 'success'})

@bp.route('/encounter/<int:encounter_id>/pdf', methods=['POST'])
@login_required
def generate_pdf(encounter_id):
    encounter = Encounter.query.filter_by(
        id=encounter_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    # PDF generation logic will be implemented here
    # This will use ReportLab to generate the PDF
    
    return jsonify({
        'status': 'success',
        'pdf_url': url_for('static', filename=f'pdfs/{encounter.uuid}.pdf')
    })