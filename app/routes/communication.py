# Communication & Support Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db, socketio
from app.models import (
    Message, CommunicationLog, PatientFeedback, SupportTicket, 
    TicketReply, ChatSession, Patient, PatientJourney, User
)
from datetime import datetime, timedelta
import secrets

bp = Blueprint('communication', __name__, url_prefix='/communication')


@bp.route('/messages')
@login_required
def messages():
    """Mesaj merkezi - tum hasta mesajlari"""
    patient_id = request.args.get('patient_id', type=int)
    
    query = Message.query.filter_by(distributor_id=current_user.distributor_id)
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    
    messages = query.order_by(Message.created_at.desc()).all()
    patients_with_messages = Patient.query.join(Message).filter(
        Message.distributor_id == current_user.distributor_id
    ).distinct().all()
    
    return render_template('communication/messages.html', 
                         messages=messages,
                         patients=patients_with_messages,
                         selected_patient_id=patient_id)


@bp.route('/messages/send', methods=['POST'])
@login_required
def send_message():
    """Yeni mesaj gonder"""
    patient_id = request.form.get('patient_id', type=int)
    content = request.form.get('content')
    journey_id = request.form.get('journey_id', type=int)
    
    if not patient_id or not content:
        flash('Hasta ve mesaj içeriği gerekli', 'danger')
        return redirect(url_for('communication.messages'))
    
    # Otomatik dil tespiti
    from app.utils.translation_service import detect_language, translate_text, should_translate
    
    detected_language = detect_language(content)
    
    # Hedef dil: hasta veya kullanıcı tercihine göre (şimdilik tr varsayılan)
    patient = Patient.query.get(patient_id)
    target_language = getattr(patient, 'preferred_language', None) or 'tr'
    
    # Çeviri gerekiyorsa yap
    translated_content = None
    if should_translate(detected_language, target_language):
        translated_content = translate_text(content, target_language, detected_language)

    message = Message(
        distributor_id=current_user.distributor_id,
        sender_id=current_user.id,
        patient_id=patient_id,
        journey_id=journey_id,
        content=content,
        message_type='text',
        detected_language=detected_language,
        target_language=target_language if translated_content else None,
        translated_content=translated_content
    )
    
    db.session.add(message)
    
    # Communication log kaydi
    log = CommunicationLog(
        distributor_id=current_user.distributor_id,
        patient_id=patient_id,
        user_id=current_user.id,
        journey_id=journey_id,
        communication_type='chat',
        direction='outbound',
        content=content,
        status='completed'
    )
    db.session.add(log)
    
    db.session.commit()
    
    # Bildirim: Yeni mesaj geldiğinde ilgili koordinatöre bildir
    try:
        from app.models import Notification
        # Journey varsa atanan koordinatöre, yoksa tüm adminlere
        if journey_id:
            journey = PatientJourney.query.get(journey_id)
            if journey and journey.assigned_coordinator_id:
                notif = Notification(
                    distributor_id=current_user.distributor_id,
                    user_id=journey.assigned_coordinator_id,
                    title='Yeni Mesaj',
                    message=f'{patient.first_name} {patient.last_name} yeni mesaj gönderdi',
                    link_url=url_for('communication.messages', patient_id=patient_id, _external=True),
                    level='info',
                    notification_type='message'
                )
                db.session.add(notif)
        else:
            # Tüm adminlere bildirim
            from app.utils.notifications import notify_distributor_admins
            notify_distributor_admins(
                current_user.distributor_id,
                'Yeni Mesaj',
                f'{patient.first_name} {patient.last_name} mesaj gönderdi',
                url_for('communication.messages', patient_id=patient_id, _external=True),
                'info',
                'message'
            )
        db.session.commit()
    except Exception as e:
        # Bildirim hatası uygulamayı durdurmamalı
        pass
    
    # Chatbot otomatik yanıt kontrolü (sadece hasta mesajlarına)
    from app.utils.chatbot_service import should_auto_respond, generate_response, get_chatbot_signature
    
    # Opsiyonel: Hasta mesajları geldiğinde otomatik yanıt (throttle kontrollü)
    # Burada staff gönderiyor -> auto respond devre dışı, sadece hasta inbound API ile aktif

    # Emit real-time event to patient's room
    try:
        room = f"patient_{patient_id}"
        from app.utils.translation_service import get_language_name
        socketio.emit('new_message', {
            'id': message.id,
            'patient_id': patient_id,
            'sender_id': current_user.id,
            'sender_username': getattr(current_user, 'username', None),
            'content': message.content,
            'message_type': message.message_type,
            'detected_language': message.detected_language,
            'detected_language_name': get_language_name(message.detected_language) if message.detected_language else None,
            'target_language': message.target_language,
            'translated_content': message.translated_content,
            'created_at': message.created_at.strftime('%d.%m.%Y %H:%M')
        }, to=room)
    except Exception:
        pass

    flash('Mesaj gönderildi', 'success')
    return redirect(url_for('communication.messages', patient_id=patient_id))


@bp.route('/logs')
@login_required
def communication_logs():
    """Tum iletisim gecmisi"""
    patient_id = request.args.get('patient_id', type=int)
    comm_type = request.args.get('type')
    
    query = CommunicationLog.query.filter_by(distributor_id=current_user.distributor_id)
    
    if patient_id:
        query = query.filter_by(patient_id=patient_id)
    if comm_type:
        query = query.filter_by(communication_type=comm_type)
    
    logs = query.order_by(CommunicationLog.created_at.desc()).all()
    
    return render_template('communication/logs.html', logs=logs)


@bp.route('/logs/add', methods=['GET', 'POST'])
@login_required
def add_communication_log():
    """Manuel iletisim kaydı ekle (telefon, email vb)"""
    if request.method == 'POST':
        log = CommunicationLog(
            distributor_id=current_user.distributor_id,
            patient_id=request.form.get('patient_id', type=int),
            user_id=current_user.id,
            journey_id=request.form.get('journey_id', type=int),
            communication_type=request.form.get('communication_type'),
            direction=request.form.get('direction'),
            subject=request.form.get('subject'),
            content=request.form.get('content'),
            phone_number=request.form.get('phone_number'),
            email_address=request.form.get('email_address'),
            duration_seconds=request.form.get('duration_seconds', type=int),
            status='completed'
        )
        
        db.session.add(log)
        db.session.commit()
        
        flash('İletişim kaydı eklendi', 'success')
        return redirect(url_for('communication.communication_logs'))
    
    patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).all()
    return render_template('communication/log_form.html', patients=patients)


@bp.route('/feedback')
@login_required
def feedback_list():
    """Hasta geri bildirimleri listesi"""
    status = request.args.get('status')
    
    query = PatientFeedback.query.filter_by(distributor_id=current_user.distributor_id)
    
    if status:
        query = query.filter_by(status=status)
    
    feedbacks = query.order_by(PatientFeedback.created_at.desc()).all()
    
    # NPS hesaplama
    all_nps = PatientFeedback.query.filter_by(
        distributor_id=current_user.distributor_id
    ).filter(
        PatientFeedback.referral_likelihood.isnot(None)
    ).all()
    
    if all_nps:
        promoters = len([f for f in all_nps if f.nps_category == 'promoter'])
        detractors = len([f for f in all_nps if f.nps_category == 'detractor'])
        nps_score = ((promoters - detractors) / len(all_nps)) * 100
    else:
        nps_score = None
    
    return render_template('communication/feedback_list.html', 
                         feedbacks=feedbacks,
                         nps_score=nps_score)


@bp.route('/feedback/<int:id>')
@login_required
def feedback_detail(id):
    """Geri bildirim detayi"""
    feedback = PatientFeedback.query.filter_by(
        id=id, 
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    return render_template('communication/feedback_detail.html', feedback=feedback)


@bp.route('/feedback/<int:id>/respond', methods=['POST'])
@login_required
def respond_to_feedback(id):
    """Geri bildirime yanitla"""
    feedback = PatientFeedback.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    feedback.response = request.form.get('response')
    feedback.responded_by = current_user.id
    feedback.responded_at = datetime.utcnow()
    feedback.status = 'approved'  # veya request.form.get('status')
    
    db.session.commit()
    
    # Bildirim: Düşük puanlı feedback için yöneticilere uyarı
    try:
        if feedback.rating and feedback.rating <= 2:
            from app.utils.notifications import notify_distributor_admins
            notify_distributor_admins(
                current_user.distributor_id,
                'Düşük Puanlı Geri Bildirim',
                f'{feedback.patient.first_name} {feedback.patient.last_name} düşük puan verdi (⭐{feedback.rating})',
                url_for('communication.feedback_detail', id=id, _external=True),
                'warning',
                'feedback'
            )
    except Exception:
        pass
    
    flash('Geri bildirime yanıt verildi', 'success')
    return redirect(url_for('communication.feedback_detail', id=id))


@bp.route('/tickets')
@login_required
def tickets():
    """Destek talepleri listesi"""
    status = request.args.get('status')
    priority = request.args.get('priority')
    
    query = SupportTicket.query.filter_by(distributor_id=current_user.distributor_id)
    
    if status:
        query = query.filter_by(status=status)
    if priority:
        query = query.filter_by(priority=priority)
    
    # Kendi atanan ticketlar varsa ön sıraya
    if not current_user.is_admin():
        query = query.filter_by(assigned_to=current_user.id)
    
    tickets = query.order_by(
        SupportTicket.priority.desc(),
        SupportTicket.created_at.desc()
    ).all()
    
    return render_template('communication/tickets.html', tickets=tickets)


@bp.route('/tickets/new', methods=['GET', 'POST'])
@login_required
def new_ticket():
    """Yeni destek talebi olustur"""
    if request.method == 'POST':
        # Ticket number olustur
        year = datetime.utcnow().year
        count = SupportTicket.query.filter_by(distributor_id=current_user.distributor_id).count() + 1
        ticket_number = f"TKT-{year}-{count:05d}"
        
        # SLA hesapla (priority'ye göre)
        priority = request.form.get('priority', 'medium')
        if priority == 'urgent':
            due_hours = 4
        elif priority == 'high':
            due_hours = 24
        elif priority == 'medium':
            due_hours = 48
        else:
            due_hours = 72
        
        ticket = SupportTicket(
            distributor_id=current_user.distributor_id,
            ticket_number=ticket_number,
            patient_id=request.form.get('patient_id', type=int),
            journey_id=request.form.get('journey_id', type=int),
            category=request.form.get('category'),
            priority=priority,
            subject=request.form.get('subject'),
            description=request.form.get('description'),
            assigned_to=request.form.get('assigned_to', type=int),
            due_date=datetime.utcnow() + timedelta(hours=due_hours),
            status='open'
        )
        
        db.session.add(ticket)
        db.session.commit()
        
        flash(f'Destek talebi oluşturuldu: {ticket_number}', 'success')
        return redirect(url_for('communication.ticket_detail', id=ticket.id))
    
    patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).all()
    staff = User.query.filter_by(distributor_id=current_user.distributor_id).all()
    
    return render_template('communication/ticket_form.html', 
                         patients=patients,
                         staff=staff)


@bp.route('/tickets/<int:id>')
@login_required
def ticket_detail(id):
    """Destek talebi detayi"""
    ticket = SupportTicket.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    return render_template('communication/ticket_detail.html', ticket=ticket)


@bp.route('/tickets/<int:id>/reply', methods=['POST'])
@login_required
def ticket_reply(id):
    """Ticket'a yanit ekle"""
    ticket = SupportTicket.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    reply = TicketReply(
        ticket_id=ticket.id,
        user_id=current_user.id,
        is_staff=True,
        message=request.form.get('message'),
        is_internal=request.form.get('is_internal') == 'true'
    )
    
    db.session.add(reply)
    
    # First response tracking
    if not ticket.first_response_at:
        ticket.first_response_at = datetime.utcnow()
        
        # Bildirim: İlk yanıt verildiğinde SLA tracking
        try:
            response_time = (ticket.first_response_at - ticket.created_at).total_seconds() / 3600
            if ticket.due_date and ticket.first_response_at > ticket.due_date:
                from app.utils.notifications import notify_distributor_admins
                notify_distributor_admins(
                    current_user.distributor_id,
                    'SLA İhlali',
                    f'#{ticket.ticket_number} SLA süresi aşıldı ({response_time:.1f} saat)',
                    url_for('communication.ticket_detail', id=id, _external=True),
                    'danger',
                    'ticket'
                )
        except Exception:
            pass
    
    # Status güncelle
    if request.form.get('change_status'):
        old_status = ticket.status
        ticket.status = request.form.get('new_status', 'in_progress')
        
        # Bildirim: Status değişikliği
        if old_status != ticket.status:
            try:
                from app.models import Notification
                notif = Notification(
                    distributor_id=current_user.distributor_id,
                    user_id=ticket.assigned_to,
                    title='Ticket Durumu Değişti',
                    message=f'#{ticket.ticket_number}: {old_status} → {ticket.status}',
                    link_url=url_for('communication.ticket_detail', id=id, _external=True),
                    level='info',
                    notification_type='ticket'
                )
                db.session.add(notif)
            except Exception:
                pass
    
    ticket.updated_at = datetime.utcnow()
    
    db.session.commit()
    
    flash('Yanıt eklendi', 'success')
    return redirect(url_for('communication.ticket_detail', id=id))


@bp.route('/tickets/<int:id>/resolve', methods=['POST'])
@login_required
def resolve_ticket(id):
    """Ticket'i coz"""
    ticket = SupportTicket.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    ticket.status = 'resolved'
    ticket.resolution = request.form.get('resolution')
    ticket.resolved_by = current_user.id
    ticket.resolved_at = datetime.utcnow()
    
    db.session.commit()
    
    # Bildirim: Ticket çözüldüğünde oluşturana bildir
    try:
        from app.models import Notification
        # Hastaya bildirim (hasta portal varsa)
        # Şimdilik sadece internal notification
        from app.utils.notifications import notify_users
        notify_users(
            [ticket.patient_id] if ticket.patient_id else [],
            'Destek Talebiniz Çözüldü',
            f'#{ticket.ticket_number} numaralı destek talebiniz çözüldü.',
            url_for('communication.ticket_detail', id=id, _external=True),
            'success',
            'ticket',
            current_user.distributor_id
        )
    except Exception:
        pass
    
    flash('Destek talebi çözüldü', 'success')
    return redirect(url_for('communication.ticket_detail', id=id))


@bp.route('/whatsapp/<int:patient_id>')
@login_required
def whatsapp_link(patient_id):
    """WhatsApp link olustur"""
    patient = Patient.query.filter_by(
        id=patient_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    if not patient.phone:
        flash('Hasta telefon numarası bulunamadı', 'danger')
        return redirect(url_for('main.patient_detail', id=patient_id))
    
    # Telefonu temizle (sadece rakamlar)
    phone = ''.join(filter(str.isdigit, patient.phone))
    
    # WhatsApp mesaj template
    message = f"Merhaba {patient.first_name}, MSH Med Tour ekibiyiz. Size nasıl yardımcı olabiliriz?"
    
    # WhatsApp link
    whatsapp_url = f"https://wa.me/{phone}?text={message}"
    
    # Log kaydi
    log = CommunicationLog(
        distributor_id=current_user.distributor_id,
        patient_id=patient_id,
        user_id=current_user.id,
        communication_type='whatsapp',
        direction='outbound',
        content=message,
        phone_number=patient.phone,
        status='completed'
    )
    db.session.add(log)
    db.session.commit()
    
    return redirect(whatsapp_url)


@bp.route('/chat/active')
@login_required
def active_chats():
    """Aktif chat oturumlari"""
    sessions = ChatSession.query.filter_by(
        distributor_id=current_user.distributor_id,
        status='active'
    ).order_by(ChatSession.started_at.desc()).all()
    
    return render_template('communication/active_chats.html', sessions=sessions)
