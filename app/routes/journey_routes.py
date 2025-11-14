# Journey Management Routes
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app import db
from app.models import (
    PatientJourney, JourneyStep, Flight, Transfer,
    Patient, Encounter, Appointment, HotelReservation, User
)
from datetime import datetime, timedelta
import secrets

bp = Blueprint('journey', __name__, url_prefix='/journey')


@bp.route('/')
@login_required
def journey_list():
    """Tum yolculuklar listesi"""
    journeys = PatientJourney.query.filter_by(distributor_id=current_user.distributor_id)\
        .order_by(PatientJourney.arrival_date.desc()).all()
    return render_template('main/journey_list.html', journeys=journeys)


@bp.route('/patient/<int:patient_id>')
@login_required
def patient_journeys(patient_id):
    """Hasta tüm yolculukları"""
    patient = Patient.query.filter_by(id=patient_id, distributor_id=current_user.distributor_id).first_or_404()
    journeys = PatientJourney.query.filter_by(patient_id=patient_id, distributor_id=current_user.distributor_id)\
        .order_by(PatientJourney.arrival_date.desc()).all()
    return render_template('main/patient_journeys.html', patient=patient, journeys=journeys)


@bp.route('/patient/<int:patient_id>/new', methods=['GET', 'POST'])
@login_required
def new_journey(patient_id=None):
    """Yeni yolculuk oluştur"""
    patient = Patient.query.filter_by(id=patient_id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        # Journey code oluştur
        year = datetime.utcnow().year
        count = PatientJourney.query.filter_by(distributor_id=current_user.distributor_id).count() + 1
        journey_code = f"TRV-{year}-{count:04d}"
        
        journey = PatientJourney(
            distributor_id=current_user.distributor_id,
            patient_id=patient_id,
            journey_code=journey_code,
            journey_type=request.form.get('journey_type', 'medical_tourism'),
            arrival_date=datetime.strptime(request.form.get('arrival_date'), '%Y-%m-%dT%H:%M'),
            departure_date=datetime.strptime(request.form.get('departure_date'), '%Y-%m-%dT%H:%M'),
            purpose=request.form.get('purpose'),
            special_requirements=request.form.get('special_requirements'),
            emergency_contact=request.form.get('emergency_contact'),
            coordinator_id=request.form.get('coordinator_id') if request.form.get('coordinator_id') else current_user.id,
            status='planned',
            created_by=current_user.id
        )
        
        # Encounter bağlantısı varsa
        encounter_id = request.form.get('encounter_id')
        if encounter_id:
            journey.encounter_id = int(encounter_id)
        
        db.session.add(journey)
        db.session.flush()
        
        # Otomatik adımlar oluştur (varsa seçili)
        if request.form.get('auto_create_steps'):
            create_default_steps(journey)
        
        db.session.commit()
        
        # Bildirim gönder
        try:
            from app.utils.notifications import notify_users
            if journey.coordinator_id and journey.coordinator_id != current_user.id:
                link = url_for('journey.journey_detail', id=journey.id, _external=True)
                notify_users([journey.coordinator_id], 
                           'Yeni Yolculuk Koordinasyonu',
                           f'{patient.full_name} için yeni yolculuk atandı.',
                           link, 'info', 'journey', current_user.distributor_id)
        except Exception:
            pass
        
        flash('Yolculuk başarıyla oluşturuldu', 'success')
    return redirect(url_for('journey.journey_detail', id=journey.id))
    
    # GET - Form göster
    from app.models import User
    coordinators = User.query.filter_by(distributor_id=current_user.distributor_id, is_active=True).all()
    encounters = Encounter.query.filter_by(patient_id=patient_id, distributor_id=current_user.distributor_id)\
        .order_by(Encounter.date.desc()).limit(10).all()
    
    return render_template('main/journey_form.html', 
                         patient=patient, 
                         coordinators=coordinators,
                         encounters=encounters)


@bp.route('/<int:id>')
@login_required
def journey_detail(id):
    """Yolculuk detay timeline"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    steps = JourneyStep.query.filter_by(journey_id=id).order_by(JourneyStep.sequence, JourneyStep.scheduled_date).all()
    flights = Flight.query.filter_by(journey_id=id).order_by(Flight.scheduled_departure).all()
    transfers = Transfer.query.filter_by(journey_id=id).order_by(Transfer.scheduled_pickup).all()
    
    return render_template('main/journey_detail.html', 
                         journey=journey, 
                         steps=steps, 
                         flights=flights, 
                         transfers=transfers)


@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_journey(id):
    """Yolculuk düzenle"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        journey.journey_type = request.form.get('journey_type')
        journey.arrival_date = datetime.strptime(request.form.get('arrival_date'), '%Y-%m-%dT%H:%M')
        journey.departure_date = datetime.strptime(request.form.get('departure_date'), '%Y-%m-%dT%H:%M')
        journey.purpose = request.form.get('purpose')
        journey.special_requirements = request.form.get('special_requirements')
        journey.emergency_contact = request.form.get('emergency_contact')
        journey.status = request.form.get('status')
        
        coordinator_id = request.form.get('coordinator_id')
        if coordinator_id:
            journey.coordinator_id = int(coordinator_id)
        
        db.session.commit()
        flash('Yolculuk güncellendi', 'success')
    return redirect(url_for('journey.journey_detail', id=journey.id))
    
    from app.models import User
    coordinators = User.query.filter_by(distributor_id=current_user.distributor_id, is_active=True).all()
    return render_template('main/journey_form.html', journey=journey, patient=journey.patient, coordinators=coordinators)


@bp.route('/<int:id>/add-step', methods=['GET', 'POST'])
@login_required
def add_journey_step(id):
    """Yolculuğa adım ekle"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        step = JourneyStep(
            journey_id=journey.id,
            step_type=request.form.get('step_type'),
            title=request.form.get('title'),
            description=request.form.get('description'),
            scheduled_date=datetime.strptime(request.form.get('scheduled_date'), '%Y-%m-%dT%H:%M'),
            location=request.form.get('location'),
            contact_person=request.form.get('contact_person'),
            contact_phone=request.form.get('contact_phone'),
            notes=request.form.get('notes'),
            is_critical=request.form.get('is_critical') == 'on',
            status='pending'
        )
        
        # Süre varsa
        if request.form.get('duration_minutes'):
            step.duration_minutes = int(request.form.get('duration_minutes'))
            step.scheduled_end = step.scheduled_date + timedelta(minutes=step.duration_minutes)
        
        # İlişkili randevu varsa
        if request.form.get('appointment_id'):
            step.appointment_id = int(request.form.get('appointment_id'))
        
        # Sequence ataması (son + 1)
        last_step = JourneyStep.query.filter_by(journey_id=journey.id).order_by(JourneyStep.sequence.desc()).first()
        step.sequence = (last_step.sequence + 1) if last_step and last_step.sequence is not None else 1
        db.session.add(step)
        db.session.commit()
        
        flash('Adım eklendi', 'success')
        return redirect(url_for('journey.journey_detail', id=journey.id))
    
    # GET
    appointments = Appointment.query.filter_by(patient_id=journey.patient_id, distributor_id=current_user.distributor_id)\
        .filter(Appointment.start_time >= journey.arrival_date, Appointment.start_time <= journey.departure_date)\
        .order_by(Appointment.start_time).all()
    
    return render_template('main/journey_step_form.html', journey=journey, appointments=appointments)


@bp.route('/step/<int:id>/update-status', methods=['POST'])
@login_required
def update_step_status(id):
    """Adım durumunu güncelle (AJAX)"""
    step = JourneyStep.query.get_or_404(id)
    
    # Yetki kontrolü
    if step.journey.distributor_id != current_user.distributor_id:
        return jsonify({'success': False, 'message': 'Yetkisiz erişim'}), 403
    
    new_status = request.json.get('status')
    if new_status not in ['pending', 'confirmed', 'in_progress', 'completed', 'cancelled', 'delayed']:
        return jsonify({'success': False, 'message': 'Geçersiz durum'}), 400
    
    step.status = new_status
    
    if new_status == 'completed':
        step.mark_completed(current_user.id)
    elif new_status == 'in_progress' and not step.actual_start:
        step.actual_start = datetime.utcnow()
    
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'status': step.status,
        'progress': step.journey.progress_percentage()
    })


@bp.route('/<int:id>/add-flight', methods=['GET', 'POST'])
@login_required
def add_flight(id):
    """Uçuş bilgisi ekle"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        flight = Flight(
            journey_id=journey.id,
            flight_type=request.form.get('flight_type'),
            airline=request.form.get('airline'),
            flight_number=request.form.get('flight_number'),
            booking_reference=request.form.get('booking_reference'),
            departure_airport=request.form.get('departure_airport'),
            arrival_airport=request.form.get('arrival_airport'),
            departure_city=request.form.get('departure_city'),
            arrival_city=request.form.get('arrival_city'),
            scheduled_departure=datetime.strptime(request.form.get('scheduled_departure'), '%Y-%m-%dT%H:%M'),
            scheduled_arrival=datetime.strptime(request.form.get('scheduled_arrival'), '%Y-%m-%dT%H:%M'),
            passenger_count=int(request.form.get('passenger_count', 1)),
            seat_numbers=request.form.get('seat_numbers'),
            baggage_info=request.form.get('baggage_info'),
            terminal=request.form.get('terminal'),
            gate=request.form.get('gate'),
            notes=request.form.get('notes'),
            status='scheduled'
        )
        
        db.session.add(flight)
        db.session.flush()
        
        # Otomatik adım oluştur
        step_title = f"{'Varış Uçuşu' if flight.flight_type == 'arrival' else 'Dönüş Uçuşu'}: {flight.flight_number}"
        step = JourneyStep(
            journey_id=journey.id,
            step_type=f"flight_{flight.flight_type}",
            title=step_title,
            description=f"{flight.departure_city} → {flight.arrival_city}",
            scheduled_date=flight.scheduled_arrival if flight.flight_type == 'arrival' else flight.scheduled_departure,
            location=f"{flight.arrival_airport if flight.flight_type == 'arrival' else flight.departure_airport}",
            notes=f"Uçuş No: {flight.flight_number}, PNR: {flight.booking_reference}",
            status='pending'
        )
        flight.journey_step_id = step.id
        db.session.add(step)
        
        db.session.commit()
        flash('Uçuş bilgisi eklendi', 'success')
    return redirect(url_for('journey.journey_detail', id=journey.id))
    
    return render_template('main/flight_form.html', journey=journey)


@bp.route('/<int:id>/add-transfer', methods=['GET', 'POST'])
@login_required
def add_transfer(id):
    """Transfer bilgisi ekle"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        transfer = Transfer(
            journey_id=journey.id,
            transfer_type=request.form.get('transfer_type'),
            pickup_location=request.form.get('pickup_location'),
            pickup_address=request.form.get('pickup_address'),
            dropoff_location=request.form.get('dropoff_location'),
            dropoff_address=request.form.get('dropoff_address'),
            scheduled_pickup=datetime.strptime(request.form.get('scheduled_pickup'), '%Y-%m-%dT%H:%M'),
            vehicle_type=request.form.get('vehicle_type'),
            vehicle_plate=request.form.get('vehicle_plate'),
            driver_name=request.form.get('driver_name'),
            driver_phone=request.form.get('driver_phone'),
            passenger_count=int(request.form.get('passenger_count', 1)),
            has_luggage=request.form.get('has_luggage') == 'on',
            wheelchair_required=request.form.get('wheelchair_required') == 'on',
            estimated_duration=int(request.form.get('estimated_duration', 30)),
            cost=float(request.form.get('cost', 0)),
            currency=request.form.get('currency', 'EUR'),
            notes=request.form.get('notes'),
            special_instructions=request.form.get('special_instructions'),
            status='scheduled'
        )
        
        db.session.add(transfer)
        db.session.flush()
        
        # Otomatik adım oluştur
        transfer_names = {
            'airport_pickup': 'Havalimanı Karşılama',
            'airport_dropoff': 'Havalimanına Transfer',
            'hospital_transfer': 'Hastane Transferi',
            'hotel_to_hospital': 'Otel → Hastane',
            'custom': 'Özel Transfer'
        }
        step_title = transfer_names.get(transfer.transfer_type, transfer.transfer_type)
        
        step = JourneyStep(
            journey_id=journey.id,
            step_type=transfer.transfer_type,
            title=step_title,
            description=f"{transfer.pickup_location} → {transfer.dropoff_location}",
            scheduled_date=transfer.scheduled_pickup,
            duration_minutes=transfer.estimated_duration,
            location=transfer.pickup_location,
            contact_person=transfer.driver_name,
            contact_phone=transfer.driver_phone,
            notes=f"Araç: {transfer.vehicle_type}, Plaka: {transfer.vehicle_plate}",
            status='pending'
        )
        transfer.journey_step_id = step.id
        db.session.add(step)
        
        db.session.commit()
        flash('Transfer eklendi', 'success')
    return redirect(url_for('journey.journey_detail', id=journey.id))
    
    return render_template('main/transfer_form.html', journey=journey)


def create_default_steps(journey):
    """Varsayılan adımları oluştur"""
    steps_to_create = []
    
    # 1. Varış uçuşu
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='flight_arrival',
        title='Varış Uçuşu',
        description='Havalimanına iniş',
        scheduled_date=journey.arrival_date,
        status='pending',
        is_critical=True
    ))
    
    # 2. Havalimanı karşılama
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='airport_pickup',
        title='Havalimanı Karşılama',
        description='Karşılama ve otel transferi',
        scheduled_date=journey.arrival_date + timedelta(minutes=30),
        duration_minutes=60,
        status='pending'
    ))
    
    # 3. Otel check-in
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='hotel_checkin',
        title='Otel Check-in',
        description='Otele yerleşme',
        scheduled_date=journey.arrival_date + timedelta(hours=2),
        duration_minutes=30,
        status='pending'
    ))
    
    # 4. Hastane ziyareti (ertesi gün sabah)
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='hospital_visit',
        title='İlk Hastane Muayenesi',
        description='Doktor görüşmesi ve tetkikler',
        scheduled_date=(journey.arrival_date + timedelta(days=1)).replace(hour=9, minute=0),
        duration_minutes=120,
        status='pending',
        is_critical=True
    ))
    
    # 5. Otel check-out (son gün)
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='hotel_checkout',
        title='Otel Check-out',
        description='Otel çıkışı',
        scheduled_date=journey.departure_date - timedelta(hours=4),
        duration_minutes=30,
        status='pending'
    ))
    
    # 6. Havalimanına transfer
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='airport_dropoff',
        title='Havalimanına Transfer',
        description='Dönüş uçuşu için transfer',
        scheduled_date=journey.departure_date - timedelta(hours=3),
        duration_minutes=60,
        status='pending',
        is_critical=True
    ))
    
    # 7. Dönüş uçuşu
    steps_to_create.append(JourneyStep(
        journey_id=journey.id,
        step_type='flight_departure',
        title='Dönüş Uçuşu',
        description='Kalkış',
        scheduled_date=journey.departure_date,
        status='pending',
        is_critical=True
    ))
    
    # Sıra ver ve ekle
    for idx, step in enumerate(steps_to_create, start=1):
        step.sequence = idx
        db.session.add(step)



@bp.route('/<int:id>/reorder-steps', methods=['POST'])
@login_required
def reorder_steps(id):
    """Adim siralamasini guncelle (AJAX drag-drop)"""
    journey = PatientJourney.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    step_ids = request.json.get('step_ids', [])
    if not step_ids:
        return jsonify({'success': False, 'message': 'Adim listesi bos'}), 400
    
    # Her adima yeni sequence ata
    for idx, step_id in enumerate(step_ids, start=1):
        step = JourneyStep.query.get(step_id)
        if step and step.journey_id == journey.id:
            step.sequence = idx
    
    db.session.commit()
    return jsonify({'success': True, 'message': 'Siralama guncellendi'})