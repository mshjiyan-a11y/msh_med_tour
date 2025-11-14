from flask import Blueprint, render_template, redirect, url_for, request, flash, abort
from flask_login import login_required, current_user
from app.models import Patient, Encounter, HotelReservation, AuditLog, QuoteApproval, Notification, Appointment, Document
from app.forms import PatientForm, HotelReservationForm
from app import db
from datetime import datetime
import secrets

bp = Blueprint('main', __name__)

@bp.before_request
def guard_disabled_modules():
    try:
        from app.models.settings import AppSettings
        settings = AppSettings.get()
        # Block hotel routes when disabled (allow superadmin)
        hotel_endpoints = {
            'main.add_hotel_reservation',
            'main.edit_hotel_reservation',
            'main.delete_hotel_reservation',
            'main.hotel_reservation_pdf',
            'main.hotel_reservation_email'
        }
        if not settings.enable_hotel and request.endpoint in hotel_endpoints:
            from flask_login import current_user
            if not getattr(current_user, 'is_superadmin', lambda: False)():
                abort(404)
    except Exception:
        # If settings unavailable, do not block
        pass

@bp.route('/')
@bp.route('/dashboard')
@login_required
def dashboard():
    from app import cache
    from sqlalchemy import func, extract
    from datetime import datetime, timedelta
    
    # Get statistics for the current distributor
    dist_id = current_user.distributor_id
    
    # Cache key unique to distributor
    cache_key = f'dashboard_stats_{dist_id}'
    stats = cache.get(cache_key)
    
    if not stats:
        patients_count = Patient.query.filter_by(distributor_id=dist_id).count()
        encounters_count = Encounter.query.filter_by(distributor_id=dist_id).count()
        stats = {'patients_count': patients_count, 'encounters_count': encounters_count}
        cache.set(cache_key, stats, timeout=300)
    else:
        patients_count = stats['patients_count']
        encounters_count = stats['encounters_count']
    
    # Recent encounters
    recent_encounters = Encounter.query.filter_by(distributor_id=dist_id)\
        .order_by(Encounter.created_at.desc()).limit(5).all()
    
    # Monthly statistics (last 6 months)
    today = datetime.utcnow()
    six_months_ago = today - timedelta(days=180)
    
    monthly_stats = db.session.query(
        func.strftime('%Y-%m', Encounter.created_at).label('month'),
        func.count(Encounter.id).label('count')
    ).filter(
        Encounter.distributor_id == dist_id,
        Encounter.created_at >= six_months_ago
    ).group_by('month').order_by('month').all()
    
    # Module usage statistics
    from app.models import HairAnnotation, DentalProcedure, EyeRefraction
    
    hair_count = db.session.query(func.count(func.distinct(HairAnnotation.encounter_id)))\
        .join(Encounter).filter(Encounter.distributor_id == dist_id).scalar()
    dental_count = db.session.query(func.count(func.distinct(DentalProcedure.encounter_id)))\
        .join(Encounter).filter(Encounter.distributor_id == dist_id).scalar()
    eye_count = db.session.query(func.count(func.distinct(EyeRefraction.encounter_id)))\
        .join(Encounter).filter(Encounter.distributor_id == dist_id).scalar()
    
    module_stats = {
        'hair': hair_count,
        'dental': dental_count,
        'eye': eye_count
    }
    
    # New patients this month
    first_day_of_month = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    new_patients_this_month = Patient.query.filter(
        Patient.distributor_id == dist_id,
        Patient.created_at >= first_day_of_month
    ).count()
    
    return render_template('main/dashboard.html',
                         patients_count=patients_count,
                         encounters_count=encounters_count,
                         recent_encounters=recent_encounters,
                         monthly_stats=monthly_stats,
                         module_stats=module_stats,
                         new_patients_this_month=new_patients_this_month)

@bp.route('/search')
@login_required
def global_search():
    """Global search across patients, encounters, documents."""
    q = request.args.get('q', '', type=str)
    category = request.args.get('category', 'all', type=str)
    
    if not q or len(q) < 2:
        return render_template('main/search_results.html', query=q, patients=[], encounters=[], documents=[], appointments=[])
    
    search_filter = f'%{q}%'
    
    patients = []
    encounters = []
    documents = []
    appointments = []
    
    if category in ('all', 'patients'):
        patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).filter(
            db.or_(
                Patient.first_name.ilike(search_filter),
                Patient.last_name.ilike(search_filter),
                Patient.phone.ilike(search_filter),
                Patient.email.ilike(search_filter),
                Patient.passport_number.ilike(search_filter)
            )
        ).limit(20).all()
    
    if category in ('all', 'encounters'):
        encounters = Encounter.query.filter_by(distributor_id=current_user.distributor_id).filter(
            db.or_(
                Encounter.note.ilike(search_filter),
                Encounter.status.ilike(search_filter)
            )
        ).limit(20).all()
    
    if category in ('all', 'documents'):
        documents = Document.query.filter_by(distributor_id=current_user.distributor_id).filter(
            db.or_(
                Document.title.ilike(search_filter),
                Document.description.ilike(search_filter),
                Document.filename.ilike(search_filter),
                Document.tags.ilike(search_filter)
            )
        ).limit(20).all()
    
    if category in ('all', 'appointments'):
        appointments = Appointment.query.filter_by(distributor_id=current_user.distributor_id).filter(
            db.or_(
                Appointment.title.ilike(search_filter),
                Appointment.description.ilike(search_filter),
                Appointment.doctor_name.ilike(search_filter)
            )
        ).limit(20).all()
    
    return render_template('main/search_results.html', 
                         query=q, 
                         category=category,
                         patients=patients, 
                         encounters=encounters, 
                         documents=documents,
                         appointments=appointments)


@bp.route('/update_theme', methods=['POST'])
@login_required
def update_theme():
    """Update user theme preference"""
    theme = request.form.get('theme', 'light')
    if theme not in ['light', 'dark']:
        theme = 'light'
    
    current_user.theme = theme
    db.session.commit()
    
    return jsonify({'success': True, 'theme': theme})


@bp.route('/update_language', methods=['POST'])
@login_required
def update_language():
    """Update user language preference"""
    language = request.form.get('language', 'tr')
    if language not in ['tr', 'en', 'ar']:
        language = 'tr'
    
    current_user.language = language
    db.session.commit()
    
    return jsonify({'success': True, 'language': language})


@bp.route('/patients')
@login_required
def patients():
    from datetime import datetime, timedelta
    
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '', type=str)
    nationality = request.args.get('nationality', '', type=str)
    gender = request.args.get('gender', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    
    query = Patient.query.filter_by(distributor_id=current_user.distributor_id)
    
    # Search filter
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(search_filter),
                Patient.last_name.ilike(search_filter),
                Patient.phone.ilike(search_filter),
                Patient.email.ilike(search_filter),
                Patient.passport_number.ilike(search_filter)
            )
        )
    
    # Nationality filter
    if nationality:
        query = query.filter(Patient.nationality.ilike(f"%{nationality}%"))
    
    # Gender filter (M or F)
    if gender:
        query = query.filter(Patient.gender == gender)
    
    # Date range filter
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Patient.created_at >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d')
            # Add one day to include the full end date
            to_date = to_date + timedelta(days=1)
            query = query.filter(Patient.created_at < to_date)
        except ValueError:
            pass
    
    # Get unique nationalities for filter dropdown
    nationalities = db.session.query(Patient.nationality).filter(
        Patient.distributor_id == current_user.distributor_id,
        Patient.nationality.isnot(None),
        Patient.nationality != ''
    ).distinct().all()
    nationalities = [n[0] for n in nationalities]
    
    patients = query.order_by(Patient.created_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('main/patients.html', 
                         patients=patients, 
                         search=search,
                         nationality=nationality,
                         gender=gender,
                         date_from=date_from,
                         date_to=date_to,
                         nationalities=nationalities)

@bp.route('/patients/export')
@login_required
def export_patients():
    """Export patient list to Excel"""
    from flask import send_file
    from app.utils.export import export_patients_to_excel
    
    query = Patient.query.filter_by(distributor_id=current_user.distributor_id)
    
    # Apply search if provided
    search = request.args.get('search', '', type=str)
    if search:
        search_filter = f"%{search}%"
        query = query.filter(
            db.or_(
                Patient.first_name.ilike(search_filter),
                Patient.last_name.ilike(search_filter),
                Patient.phone.ilike(search_filter),
                Patient.email.ilike(search_filter)
            )
        )
    
    patients = query.order_by(Patient.created_at.desc()).all()
    excel_file = export_patients_to_excel(patients)
    
    filename = f"hastalar_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/patient/new', methods=['GET', 'POST'])
@login_required
def new_patient():
    form = PatientForm()
    if form.validate_on_submit():
        # determine distributor_id safely
        from app.models import Distributor
        dist_id = getattr(current_user, 'distributor_id', None)
        if not dist_id and getattr(current_user, 'distributor', None):
            dist_id = getattr(current_user.distributor, 'id', None)
        if not dist_id:
            first = Distributor.query.first()
            if first:
                dist_id = first.id

        if not dist_id:
            flash('Kayıt için sistemde tanımlı bir distribütör yok. Yönetici ile iletişime geçin.', 'danger')
            return redirect(url_for('main.patients'))

        patient = Patient(
            distributor_id=dist_id,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            phone=form.phone.data,
            email=form.email.data,
            dob=form.dob.data,
            nationality=form.nationality.data,
            notes=form.notes.data
        )
        db.session.add(patient)
        db.session.commit()
        
        # Clear dashboard cache
        from app import cache
        cache.delete(f'dashboard_stats_{dist_id}')
        
        flash('Hasta başarıyla eklendi', 'success')
        return redirect(url_for('main.patients'))
        
    return render_template('main/patient_form.html', form=form)

@bp.route('/patient/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    patient = Patient.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    form = PatientForm(obj=patient)
    
    if form.validate_on_submit():
        patient.first_name = form.first_name.data
        patient.last_name = form.last_name.data
        patient.phone = form.phone.data
        patient.email = form.email.data
        patient.dob = form.dob.data
        patient.nationality = form.nationality.data
        patient.passport_number = form.passport_number.data
        patient.notes = form.notes.data
        
        db.session.commit()
        flash('Hasta bilgileri güncellendi', 'success')
        return redirect(url_for('main.patient_detail', id=patient.id))
        
    return render_template('main/patient_form.html', form=form, patient=patient)

@bp.route('/patient/<int:id>')
@login_required
def patient_detail(id):
    patient = Patient.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    encounters = Encounter.query.filter_by(patient_id=patient.id)\
        .order_by(Encounter.date.desc()).all()
    # Hotel reservations for this patient
    from app.models import HotelReservation
    reservations = HotelReservation.query.filter_by(patient_id=patient.id)\
        .order_by(HotelReservation.check_in.desc()).all()
    # Documents for this patient
    documents = Document.query.filter_by(patient_id=patient.id, is_archived=False)\
        .order_by(Document.uploaded_at.desc()).limit(10).all()
    return render_template('main/patient_detail.html', patient=patient, encounters=encounters, reservations=reservations, documents=documents)

@bp.route('/encounter/new/<int:patient_id>', methods=['GET', 'POST'])
@login_required
def new_encounter(patient_id):
    from app.models import (
        HairAnnotation, HairPatternSelection, DentalProcedure, 
        EyeRefraction, EyeTreatmentSelection, Distributor,
        AestheticProcedure, BariatricSurgery, IVFTreatment, 
        CheckUpPackage
    )
    
    patient = Patient.query.filter_by(id=patient_id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        # Determine distributor_id safely
        dist_id = getattr(current_user, 'distributor_id', None)
        if not dist_id:
            first = Distributor.query.first()
            if first:
                dist_id = first.id
        
        # Create encounter
        encounter_date = request.form.get('date')
        if encounter_date:
            encounter_date = datetime.strptime(encounter_date, '%Y-%m-%d')
        else:
            encounter_date = datetime.utcnow()
            
        encounter = Encounter(
            distributor_id=dist_id,
            patient_id=patient.id,
            date=encounter_date,
            note=request.form.get('note', ''),
            status=request.form.get('status', 'draft'),
            created_by=current_user.id
        )
        db.session.add(encounter)
        db.session.flush()  # Get encounter.id
        
        # Hair module
        if request.form.get('enable_hair'):
            pattern = request.form.get('hair_pattern')
            if pattern:
                hair_pattern = HairPatternSelection(
                    encounter_id=encounter.id,
                    pattern_key=pattern,
                    note=request.form.get('hair_notes', '')
                )
                db.session.add(hair_pattern)
            
            grafts = request.form.get('hair_grafts')
            if grafts:
                hair_anno = HairAnnotation(
                    encounter_id=encounter.id,
                    region_id='general',
                    label=f'Toplam {grafts} greft',
                    note=request.form.get('hair_notes', '')
                )
                db.session.add(hair_anno)
        
        # Dental module
        if request.form.get('enable_dental'):
            teeth = request.form.getlist('dental_tooth[]')
            treatments = request.form.getlist('dental_treatment[]')
            prices = request.form.getlist('dental_price[]')
            currencies = request.form.getlist('dental_currency[]')
            notes = request.form.getlist('dental_note[]')
            
            for i in range(len(teeth)):
                if teeth[i] and treatments[i]:
                    dental = DentalProcedure(
                        encounter_id=encounter.id,
                        tooth_no=int(teeth[i]),
                        treatment_type=treatments[i],
                        price=float(prices[i]) if prices[i] else 0,
                        currency=currencies[i] if i < len(currencies) else 'EUR',
                        note=notes[i] if i < len(notes) else ''
                    )
                    db.session.add(dental)
        
        # Eye module
        if request.form.get('enable_eye'):
            od_sph = request.form.get('od_sph')
            if od_sph:
                eye_refraction = EyeRefraction(
                    encounter_id=encounter.id,
                    od_sph=float(od_sph) if od_sph else None,
                    od_cyl=float(request.form.get('od_cyl')) if request.form.get('od_cyl') else None,
                    od_ax=int(request.form.get('od_ax')) if request.form.get('od_ax') else None,
                    os_sph=float(request.form.get('os_sph')) if request.form.get('os_sph') else None,
                    os_cyl=float(request.form.get('os_cyl')) if request.form.get('os_cyl') else None,
                    os_ax=int(request.form.get('os_ax')) if request.form.get('os_ax') else None,
                    planned_procedure=request.form.get('eye_procedure', '')
                )
                db.session.add(eye_refraction)
            
            eye_procedure = request.form.get('eye_procedure')
            eye_price = request.form.get('eye_price')
            if eye_procedure and eye_price:
                eye_treatment = EyeTreatmentSelection(
                    encounter_id=encounter.id,
                    code=eye_procedure.upper().replace(' ', '_'),
                    title=eye_procedure,
                    side='OU',  # Both eyes
                    price=float(eye_price),
                    currency='EUR',
                    note=request.form.get('eye_notes', '')
                )
                db.session.add(eye_treatment)
        
        # Aesthetic Surgery module
        if request.form.get('enable_aesthetic'):
            aesthetic_procedure = request.form.get('aesthetic_procedure')
            aesthetic_price = request.form.get('aesthetic_price')
            if aesthetic_procedure:
                aesthetic = AestheticProcedure(
                    encounter_id=encounter.id,
                    procedure_type=aesthetic_procedure,
                    price=float(aesthetic_price) if aesthetic_price else 0,
                    currency=request.form.get('aesthetic_currency', 'USD'),
                    notes=request.form.get('aesthetic_notes', '')
                )
                db.session.add(aesthetic)
        
        # Bariatric Surgery module
        if request.form.get('enable_bariatric'):
            bariatric_surgery = request.form.get('bariatric_surgery')
            bariatric_weight = request.form.get('bariatric_weight')
            bariatric_height = request.form.get('bariatric_height')
            if bariatric_surgery and bariatric_weight and bariatric_height:
                bariatric = BariatricSurgery(
                    encounter_id=encounter.id,
                    surgery_type=bariatric_surgery,
                    weight_kg=float(bariatric_weight),
                    height_cm=float(bariatric_height),
                    price=float(request.form.get('bariatric_price', 0)),
                    currency=request.form.get('bariatric_currency', 'USD'),
                    notes=request.form.get('bariatric_notes', '')
                )
                db.session.add(bariatric)
        
        # IVF Treatment module
        if request.form.get('enable_ivf'):
            ivf_treatment = request.form.get('ivf_treatment')
            if ivf_treatment:
                ivf = IVFTreatment(
                    encounter_id=encounter.id,
                    treatment_type=ivf_treatment,
                    cycle_number=int(request.form.get('ivf_cycle', 1)),
                    female_age=int(request.form.get('ivf_age')) if request.form.get('ivf_age') else None,
                    price=float(request.form.get('ivf_price', 0)),
                    currency=request.form.get('ivf_currency', 'USD'),
                    notes=request.form.get('ivf_notes', '')
                )
                db.session.add(ivf)
        
        # Check-Up Package module
        if request.form.get('enable_checkup'):
            checkup_package = request.form.get('checkup_package')
            if checkup_package:
                # Get selected tests
                tests = []
                if request.form.get('checkup_test_blood'):
                    tests.append('Kan Testi')
                if request.form.get('checkup_test_xray'):
                    tests.append('X-Ray')
                if request.form.get('checkup_test_ecg'):
                    tests.append('EKG')
                if request.form.get('checkup_test_ultrasound'):
                    tests.append('Ultrason')
                
                checkup = CheckUpPackage(
                    encounter_id=encounter.id,
                    package_type=checkup_package,
                    tests_included=', '.join(tests),
                    price=float(request.form.get('checkup_price', 0)),
                    currency=request.form.get('checkup_currency', 'USD'),
                    notes=request.form.get('checkup_notes', '')
                )
                db.session.add(checkup)
        
        # Audit log: encounter created
        from app.utils.audit import log_change, persist_audit
        log_change(distributor_id=dist_id, user_id=current_user.id, action='create', entity_type='encounter', entity_id=encounter.id, encounter_id=encounter.id, note='Muayene oluşturuldu')
        # Bildirim: distribütör adminlerine haber ver
        try:
            from app.utils.notifications import notify_distributor_admins
            link = url_for('main.encounter_detail', id=encounter.id, _external=True)
            notify_distributor_admins(distributor_id=dist_id,
                                      title='Yeni Muayene Kaydı',
                                      message=f"{patient.first_name} {patient.last_name} için yeni muayene oluşturuldu.",
                                      link_url=link,
                                      level='info', ntype='encounter', created_by=current_user.id)
        except Exception:
            pass
        db.session.commit()
        persist_audit()
        flash('Muayene kaydı başarıyla oluşturuldu', 'success')
        return redirect(url_for('main.encounter_detail', id=encounter.id))
    
    # GET request
    from app.models import AppSettings
    app_settings = AppSettings.query.first()
    today = datetime.utcnow().strftime('%Y-%m-%d')
    return render_template('main/encounter_form.html', patient=patient, today=today, app_settings=app_settings)

@bp.route('/encounter/<int:id>')
@login_required
def encounter_detail(id):
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    # Fetch last 25 audit logs for this encounter
    logs = AuditLog.query.filter_by(encounter_id=encounter.id).order_by(AuditLog.created_at.desc()).limit(25).all()
    return render_template('main/encounter_detail.html', encounter=encounter, audit_logs=logs)

@bp.route('/encounter/<int:id>/pdf')
@login_required
def encounter_pdf(id):
    print(f"🔍 PDF Route called for encounter {id}")
    print(f"  Current user: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    print(f"  User distributor_id: {current_user.distributor_id if current_user.is_authenticated else 'N/A'}")
    from flask import send_file
    from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
    
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    distributor = encounter.distributor
    
    # Generate PDF with new professional generator
    generator = ProfessionalEncounterPDF(encounter, distributor)
    pdf_buffer = generator.generate()
    
    # Create filename
    filename = f"muayene_{encounter.id}_{encounter.patient.first_name}_{encounter.patient.last_name}.pdf"
    # Inline preview support
    inline = request.args.get('inline', '0') == '1'

    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=not inline,
        download_name=filename
    )

@bp.route('/encounter/<int:id>/pdf/preview')
@login_required
def encounter_pdf_preview(id):
    print(f"🔍 PDF Preview Route called for encounter {id}")
    print(f"  Current user: {current_user.username if current_user.is_authenticated else 'Anonymous'}")
    
    # Renders an HTML page with embedded PDF for live preview
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    print(f"  Encounter found: {encounter.patient.full_name}")
    pdf_url = url_for('main.encounter_pdf', id=id, inline=1)
    print(f"  PDF URL: {pdf_url}")
    return render_template('main/encounter_pdf_preview.html', encounter=encounter, pdf_url=pdf_url)

@bp.route('/encounter/<int:id>/export.csv')
@login_required
def export_encounter_csv(id):
    import csv
    from io import StringIO
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()

    si = StringIO()
    writer = csv.writer(si)
    writer.writerow(['module', 'item', 'quantity', 'price', 'currency', 'note'])

    # Hair: summarize by total grafts (quantity)
    total_grafts = 0
    for ann in encounter.hair_annotations:
        # Try to extract numeric from label if possible
        try:
            import re
            m = re.search(r'(\d+)', ann.label or '')
            if m:
                total_grafts += int(m.group(1))
        except Exception:
            pass
    if total_grafts:
        writer.writerow(['hair', 'grafts', total_grafts, '', '', ''])

    # Dental
    for d in encounter.dental_procedures:
        writer.writerow(['dental', d.treatment_type, 1, d.price or 0, d.currency or 'EUR', d.note or '' ])

    # Eye treatments
    for t in encounter.eye_treatments:
        writer.writerow(['eye', t.title, 1, t.price or 0, t.currency or 'EUR', t.note or '' ])

    # Aesthetic
    if encounter.aesthetic_procedure:
        a = encounter.aesthetic_procedure
        writer.writerow(['aesthetic', a.procedure_type, 1, a.price or 0, a.currency or 'USD', a.notes or '' ])

    # Bariatric
    if encounter.bariatric_surgery:
        b = encounter.bariatric_surgery
        writer.writerow(['bariatric', b.surgery_type, 1, b.price or 0, b.currency or 'USD', b.notes or '' ])

    # IVF
    if encounter.ivf_treatment:
        v = encounter.ivf_treatment
        writer.writerow(['ivf', v.treatment_type, 1, v.price or 0, v.currency or 'USD', v.notes or '' ])

    # Check-up
    if encounter.checkup_package:
        c = encounter.checkup_package
        writer.writerow(['checkup', c.package_type, 1, c.price or 0, c.currency or 'USD', c.notes or '' ])

    output = si.getvalue()
    from flask import Response
    filename = f"encounter_{encounter.id}_items.csv"
    return Response(output, mimetype='text/csv', headers={
        'Content-Disposition': f'attachment; filename={filename}'
    })

@bp.route('/encounter/<int:id>/import', methods=['POST'])
@login_required
def import_encounter_csv(id):
    """Import items from CSV. Supports dental/eye/aesthetic/bariatric/ivf/checkup basic rows.
    CSV columns: module,item,quantity,price,currency,note
    """
    from io import StringIO
    import csv
    from app.models import DentalProcedure, EyeTreatmentSelection, AestheticProcedure, BariatricSurgery, IVFTreatment, CheckUpPackage, HairAnnotation
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()

    file = request.files.get('file')
    if not file or not file.filename.lower().endswith('.csv'):
        flash('Lütfen CSV dosyası yükleyin.', 'warning')
        return redirect(url_for('main.encounter_detail', id=id))

    # Simple import: append items; existing data is kept
    stream = StringIO(file.stream.read().decode('utf-8'))
    reader = csv.DictReader(stream)
    added = 0
    for row in reader:
        module = (row.get('module') or '').strip().lower()
        item = (row.get('item') or '').strip()
        qty = int(row.get('quantity') or '1')
        price = float(row.get('price') or '0')
        currency = (row.get('currency') or 'EUR').upper()
        note = row.get('note') or ''

        if module == 'dental' and item:
            db.session.add(DentalProcedure(encounter_id=id, tooth_no=0, treatment_type=item, price=price, currency=currency, note=note))
            added += 1
        elif module == 'eye' and item:
            db.session.add(EyeTreatmentSelection(encounter_id=id, code=item.upper().replace(' ', '_'), title=item, side='OU', price=price, currency=currency, note=note))
            added += 1
        elif module == 'aesthetic' and item:
            # Replace existing
            AestheticProcedure.query.filter_by(encounter_id=id).delete()
            db.session.add(AestheticProcedure(encounter_id=id, procedure_type=item, price=price, currency=currency, notes=note))
            added += 1
        elif module == 'bariatric' and item:
            BariatricSurgery.query.filter_by(encounter_id=id).delete()
            db.session.add(BariatricSurgery(encounter_id=id, surgery_type=item, weight_kg=0, height_cm=0, price=price, currency=currency, notes=note))
            added += 1
        elif module == 'ivf' and item:
            IVFTreatment.query.filter_by(encounter_id=id).delete()
            db.session.add(IVFTreatment(encounter_id=id, treatment_type=item, cycle_number=1, female_age=None, price=price, currency=currency, notes=note))
            added += 1
        elif module == 'checkup' and item:
            CheckUpPackage.query.filter_by(encounter_id=id).delete()
            db.session.add(CheckUpPackage(encounter_id=id, package_type=item, tests_included='', price=price, currency=currency, notes=note))
            added += 1
        elif module == 'hair' and item and qty:
            db.session.add(HairAnnotation(encounter_id=id, region_id='import', label=f'{item}: {qty}', note=note))
            added += 1

    db.session.commit()
    flash(f'CSV içe aktarma tamamlandı. Eklenen kayıt: {added}', 'success')
    return redirect(url_for('main.encounter_detail', id=id))

@bp.route('/encounter/<int:id>/email_quote', methods=['POST'])
@login_required
def encounter_email_quote(id):
    """Generate price quote PDF and email it to patient's email"""
    from app.utils.pdf_generator import QuotePDFGenerator
    from app.utils.email import send_encounter_price_quote

    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    patient = encounter.patient

    if not patient.email:
        flash('Hasta için e-posta adresi bulunamadı. Hasta kartından e-posta ekleyin.', 'warning')
        return redirect(url_for('main.encounter_detail', id=id))

    # Generate Quote PDF in memory
    generator = QuotePDFGenerator(encounter, encounter.distributor)
    pdf_buffer = generator.generate()
    pdf_bytes = pdf_buffer.getvalue()

    try:
        send_encounter_price_quote(encounter, pdf_bytes)
        flash('Fiyat teklifi e-posta ile gönderildi.', 'success')
    except Exception as e:
        flash(f'E-posta gönderilemedi: {e}', 'danger')

    return redirect(url_for('main.encounter_detail', id=id))

 

@bp.route('/encounter/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_encounter(id):
    from app.models import (
        HairAnnotation, HairPatternSelection, DentalProcedure, 
        EyeRefraction, EyeTreatmentSelection,
        AestheticProcedure, BariatricSurgery, IVFTreatment, 
        CheckUpPackage
    )
    
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    patient = encounter.patient
    
    if request.method == 'POST':
        from app.utils.audit import log_change, persist_audit
        print(f"🔍 DEBUG - POST request for encounter {id}")
        print(f"  Form keys: {list(request.form.keys())}")
        eye_keys = [k for k in request.form.keys() if 'eye' in k.lower()]
        print(f"  Eye keys: {eye_keys}")
        for k in eye_keys:
            print(f"    {k}: {request.form.get(k)}")
        
        old_date = encounter.date
        old_note = encounter.note
        old_status = encounter.status
        # Update basic encounter info
        encounter_date = request.form.get('date')
        if encounter_date:
            encounter.date = datetime.strptime(encounter_date, '%Y-%m-%d')
        encounter.note = request.form.get('note', '')
        encounter.status = request.form.get('status', 'draft')
        # Log field changes if different
        if old_date != encounter.date:
            log_change(encounter.distributor_id, current_user.id, 'update', 'encounter', encounter.id, 'date', old_date, encounter.date, encounter_id=encounter.id)
        if old_note != encounter.note:
            log_change(encounter.distributor_id, current_user.id, 'update', 'encounter', encounter.id, 'note', old_note, encounter.note, encounter_id=encounter.id)
        if old_status != encounter.status:
            log_change(encounter.distributor_id, current_user.id, 'update', 'encounter', encounter.id, 'status', old_status, encounter.status, encounter_id=encounter.id)
        
        # Delete existing module data
        # Delete existing module data (log clearing)
        if HairAnnotation.query.filter_by(encounter_id=encounter.id).count():
            HairAnnotation.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'hair_annotations', encounter.id, note='Saç anotasyonları temizlendi', encounter_id=encounter.id)
        if HairPatternSelection.query.filter_by(encounter_id=encounter.id).count():
            HairPatternSelection.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'hair_patterns', encounter.id, note='Saç paternleri temizlendi', encounter_id=encounter.id)
        if DentalProcedure.query.filter_by(encounter_id=encounter.id).count():
            DentalProcedure.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'dental_procedures', encounter.id, note='Diş işlemleri temizlendi', encounter_id=encounter.id)
        if EyeRefraction.query.filter_by(encounter_id=encounter.id).count():
            EyeRefraction.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'eye_refraction', encounter.id, note='Göz refraksiyon verileri temizlendi', encounter_id=encounter.id)
        if EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).count():
            EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'eye_treatments', encounter.id, note='Göz tedavileri temizlendi', encounter_id=encounter.id)
        if AestheticProcedure.query.filter_by(encounter_id=encounter.id).count():
            AestheticProcedure.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'aesthetic_procedure', encounter.id, note='Estetik cerrahi kaydı temizlendi', encounter_id=encounter.id)
        if BariatricSurgery.query.filter_by(encounter_id=encounter.id).count():
            BariatricSurgery.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'bariatric_surgery', encounter.id, note='Bariatrik cerrahi kaydı temizlendi', encounter_id=encounter.id)
        if IVFTreatment.query.filter_by(encounter_id=encounter.id).count():
            IVFTreatment.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'ivf_treatment', encounter.id, note='Tüp bebek kaydı temizlendi', encounter_id=encounter.id)
        if CheckUpPackage.query.filter_by(encounter_id=encounter.id).count():
            CheckUpPackage.query.filter_by(encounter_id=encounter.id).delete()
            log_change(encounter.distributor_id, current_user.id, 'delete', 'checkup_package', encounter.id, note='Check-Up paketi temizlendi', encounter_id=encounter.id)
        
        # Hair module
        if request.form.get('enable_hair'):
            # Hair regions from interactive diagram
            region_ids = request.form.getlist('hair_region_id[]')
            region_names = request.form.getlist('hair_region_name[]')
            region_grafts = request.form.getlist('hair_region_grafts[]')
            region_notes = request.form.getlist('hair_region_note[]')
            
            for i in range(len(region_ids)):
                if region_ids[i] and region_grafts[i]:
                    hair_anno = HairAnnotation(
                        encounter_id=encounter.id,
                        region_id=region_ids[i],
                        label=f'{region_names[i]}: {region_grafts[i]} greft',
                        note=region_notes[i] if i < len(region_notes) else ''
                    )
                    db.session.add(hair_anno)
                    log_change(encounter.distributor_id, current_user.id, 'create', 'hair_annotation', hair_anno.id, note=hair_anno.label, encounter_id=encounter.id)
            
            # Hair pattern if provided
            pattern = request.form.get('hair_pattern')
            if pattern:
                hair_pattern = HairPatternSelection(
                    encounter_id=encounter.id,
                    pattern_key=pattern,
                    note=request.form.get('hair_pattern_notes', '')
                )
                db.session.add(hair_pattern)
                log_change(encounter.distributor_id, current_user.id, 'create', 'hair_pattern', hair_pattern.id, note=hair_pattern.pattern_key, encounter_id=encounter.id)
        
        # Dental module
        if request.form.get('enable_dental'):
            teeth = request.form.getlist('dental_tooth[]')
            treatments = request.form.getlist('dental_treatment[]')
            prices = request.form.getlist('dental_price[]')
            currencies = request.form.getlist('dental_currency[]')
            notes = request.form.getlist('dental_note[]')
            
            for i in range(len(teeth)):
                if teeth[i] and treatments[i]:
                    dental = DentalProcedure(
                        encounter_id=encounter.id,
                        tooth_no=int(teeth[i]),
                        treatment_type=treatments[i],
                        price=float(prices[i]) if prices[i] else 0,
                        currency=currencies[i] if i < len(currencies) else 'EUR',
                        note=notes[i] if i < len(notes) else ''
                    )
                    db.session.add(dental)
                    log_change(encounter.distributor_id, current_user.id, 'create', 'dental_procedure', dental.id, note=dental.treatment_type, encounter_id=encounter.id)
        
        # Eye module - Debug logging
        if request.form.get('enable_eye'):
            print(f"🔍 DEBUG - Eye module enabled. Form data:")
            print(f"  enable_eye: {request.form.get('enable_eye')}")
            print(f"  eye_od_sph: {request.form.get('eye_od_sph')}")
            print(f"  eye_os_sph: {request.form.get('eye_os_sph')}")
            print(f"  eye_od_cyl: {request.form.get('eye_od_cyl')}")
            print(f"  eye_os_cyl: {request.form.get('eye_os_cyl')}")
            print(f"  eye_od_axis: {request.form.get('eye_od_axis')}")
            print(f"  eye_os_axis: {request.form.get('eye_os_axis')}")
            print(f"  eye_treatments: {request.form.getlist('eye_treatments')}")
            
            # Get eye data from hidden inputs
            od_sph = request.form.get('eye_od_sph')
            os_sph = request.form.get('eye_os_sph')
            
            if od_sph or os_sph:
                eye_refraction = EyeRefraction(
                    encounter_id=encounter.id,
                    od_sph=float(od_sph) if od_sph else None,
                    od_cyl=float(request.form.get('eye_od_cyl')) if request.form.get('eye_od_cyl') else None,
                    od_ax=int(request.form.get('eye_od_axis')) if request.form.get('eye_od_axis') else None,
                    os_sph=float(os_sph) if os_sph else None,
                    os_cyl=float(request.form.get('eye_os_cyl')) if request.form.get('eye_os_cyl') else None,
                    os_ax=int(request.form.get('eye_os_axis')) if request.form.get('eye_os_axis') else None,
                    planned_procedure=request.form.get('eye_procedure', '')
                )
                db.session.add(eye_refraction)
                log_change(encounter.distributor_id, current_user.id, 'create', 'eye_refraction', eye_refraction.id, note='Refraksiyon değerleri eklendi', encounter_id=encounter.id)
            
            # Eye treatments
            eye_treatments = request.form.getlist('eye_treatments')
            for treatment in eye_treatments:
                if treatment:
                    eye_treatment = EyeTreatmentSelection(
                        encounter_id=encounter.id,
                        code=treatment.upper().replace(' ', '_'),
                        title=treatment,
                        side='OU',
                        price=0,
                        currency='EUR',
                        note=''
                    )
                    db.session.add(eye_treatment)
                    log_change(encounter.distributor_id, current_user.id, 'create', 'eye_treatment', eye_treatment.id, note=eye_treatment.title, encounter_id=encounter.id)
        
        # Aesthetic Surgery module
        if request.form.get('enable_aesthetic'):
            aesthetic_procedure = request.form.get('aesthetic_procedure')
            aesthetic_price = request.form.get('aesthetic_price')
            if aesthetic_procedure:
                aesthetic = AestheticProcedure(
                    encounter_id=encounter.id,
                    procedure_type=aesthetic_procedure,
                    price=float(aesthetic_price) if aesthetic_price else 0,
                    currency=request.form.get('aesthetic_currency', 'USD'),
                    notes=request.form.get('aesthetic_notes', '')
                )
                db.session.add(aesthetic)
                log_change(encounter.distributor_id, current_user.id, 'create', 'aesthetic_procedure', aesthetic.id, note=aesthetic.procedure_type, encounter_id=encounter.id)
        
        # Bariatric Surgery module
        if request.form.get('enable_bariatric'):
            bariatric_surgery = request.form.get('bariatric_surgery')
            bariatric_weight = request.form.get('bariatric_weight')
            bariatric_height = request.form.get('bariatric_height')
            if bariatric_surgery and bariatric_weight and bariatric_height:
                bariatric = BariatricSurgery(
                    encounter_id=encounter.id,
                    surgery_type=bariatric_surgery,
                    weight_kg=float(bariatric_weight),
                    height_cm=float(bariatric_height),
                    price=float(request.form.get('bariatric_price', 0)),
                    currency=request.form.get('bariatric_currency', 'USD'),
                    notes=request.form.get('bariatric_notes', '')
                )
                db.session.add(bariatric)
                log_change(encounter.distributor_id, current_user.id, 'create', 'bariatric_surgery', bariatric.id, note=bariatric.surgery_type, encounter_id=encounter.id)
        
        # IVF Treatment module
        if request.form.get('enable_ivf'):
            ivf_treatment = request.form.get('ivf_treatment')
            if ivf_treatment:
                ivf = IVFTreatment(
                    encounter_id=encounter.id,
                    treatment_type=ivf_treatment,
                    cycle_number=int(request.form.get('ivf_cycle', 1)),
                    female_age=int(request.form.get('ivf_age')) if request.form.get('ivf_age') else None,
                    price=float(request.form.get('ivf_price', 0)),
                    currency=request.form.get('ivf_currency', 'USD'),
                    notes=request.form.get('ivf_notes', '')
                )
                db.session.add(ivf)
                log_change(encounter.distributor_id, current_user.id, 'create', 'ivf_treatment', ivf.id, note=ivf.treatment_type, encounter_id=encounter.id)
        
        # Check-Up Package module
        if request.form.get('enable_checkup'):
            checkup_package = request.form.get('checkup_package')
            if checkup_package:
                # Get selected tests
                tests = []
                if request.form.get('checkup_test_blood'):
                    tests.append('Kan Testi')
                if request.form.get('checkup_test_xray'):
                    tests.append('X-Ray')
                if request.form.get('checkup_test_ecg'):
                    tests.append('EKG')
                if request.form.get('checkup_test_ultrasound'):
                    tests.append('Ultrason')
                
                checkup = CheckUpPackage(
                    encounter_id=encounter.id,
                    package_type=checkup_package,
                    tests_included=', '.join(tests),
                    price=float(request.form.get('checkup_price', 0)),
                    currency=request.form.get('checkup_currency', 'USD'),
                    notes=request.form.get('checkup_notes', '')
                )
                db.session.add(checkup)
                log_change(encounter.distributor_id, current_user.id, 'create', 'checkup_package', checkup.id, note=checkup.package_type, encounter_id=encounter.id)
        
        db.session.commit()
        persist_audit()
    flash('Muayene başarıyla güncellendi', 'success')
    return redirect(url_for('main.encounter_detail', id=encounter.id))
    
    # GET request - load existing data
    from app.models import AppSettings
    app_settings = AppSettings.query.first()
    return render_template('main/encounter_edit.html', 
                         encounter=encounter, 
                         patient=patient,
                         app_settings=app_settings)

@bp.route('/appointments_old')
@login_required
def appointments_old():
    """Legacy encounters as appointments view - deprecated, redirects to new appointments."""
    return redirect(url_for('main.appointments_list'))

@bp.route('/appointments/export')
@login_required
def export_appointments():
    """Export encounters/appointments to Excel"""
    from flask import send_file
    from app.utils.export import export_encounters_to_excel
    
    encounters = Encounter.query.filter_by(distributor_id=current_user.distributor_id)\
        .order_by(Encounter.date.desc()).all()
    
    excel_file = export_encounters_to_excel(encounters)
    filename = f"muayeneler_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    
    return send_file(
        excel_file,
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/encounter/<int:id>/delete', methods=['POST'])
@login_required
def delete_encounter(id):
    from app.models import HairAnnotation, HairPatternSelection, DentalProcedure, EyeRefraction, EyeTreatmentSelection
    
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    patient_id = encounter.patient_id
    
    # Delete all related records (cascade)
    HairAnnotation.query.filter_by(encounter_id=encounter.id).delete()
    HairPatternSelection.query.filter_by(encounter_id=encounter.id).delete()
    DentalProcedure.query.filter_by(encounter_id=encounter.id).delete()
    EyeRefraction.query.filter_by(encounter_id=encounter.id).delete()
    EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).delete()
    
    from app.utils.audit import log_change, persist_audit
    db.session.delete(encounter)
    log_change(encounter.distributor_id, current_user.id, 'delete', 'encounter', encounter.id, encounter_id=encounter.id, note='Muayene silindi')
    db.session.commit()
    persist_audit()
    
    flash('Muayene başarıyla silindi', 'success')
    return redirect(url_for('main.patient_detail', id=patient_id))

@bp.route('/patient/<int:id>/delete', methods=['POST'])
@login_required
def delete_patient(id):
    from app.models import HairAnnotation, HairPatternSelection, DentalProcedure, EyeRefraction, EyeTreatmentSelection
    
    patient = Patient.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    # Delete all encounters and their related records
    for encounter in patient.encounters:
        HairAnnotation.query.filter_by(encounter_id=encounter.id).delete()
        HairPatternSelection.query.filter_by(encounter_id=encounter.id).delete()
        DentalProcedure.query.filter_by(encounter_id=encounter.id).delete()
        EyeRefraction.query.filter_by(encounter_id=encounter.id).delete()
        EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).delete()
        db.session.delete(encounter)
    
    # Delete patient
    db.session.delete(patient)
    db.session.commit()
    
    flash('Hasta ve tüm muayene kayıtları başarıyla silindi', 'success')
    return redirect(url_for('main.patients'))

@bp.route('/clinics')
@login_required
def clinics():
    return render_template('main/clinics.html')

@bp.route('/users')
@login_required
def users():
    return render_template('main/users.html')

@bp.route('/profile')
@login_required
def profile():
    return render_template('main/profile.html')


# ========== HOTEL RESERVATION ROUTES ==========

@bp.route('/patient/<int:patient_id>/hotel/new', methods=['GET', 'POST'])
@login_required
def add_hotel_reservation(patient_id):
    """Add hotel reservation for patient"""
    patient = Patient.query.filter_by(
        id=patient_id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    form = HotelReservationForm()
    
    if form.validate_on_submit():
        reservation = HotelReservation(
            patient_id=patient.id,
            distributor_id=current_user.distributor_id,
            hotel_name=form.hotel_name.data,
            hotel_address=form.hotel_address.data,
            hotel_phone=form.hotel_phone.data,
            hotel_stars=form.hotel_stars.data,
            room_type=form.room_type.data,
            check_in=form.check_in.data,
            check_out=form.check_out.data,
            price_per_night=form.price_per_night.data or 0,
            currency=form.currency.data or 'EUR',
            transfer_included=form.transfer_included.data,
            transfer_type=form.transfer_type.data,
            transfer_cost=form.transfer_cost.data or 0,
            airport_code=form.airport_code.data,
            airport_name=form.airport_name.data,
            flight_number=form.flight_number.data,
            arrival_time=form.arrival_time.data,
            departure_time=form.departure_time.data,
            breakfast_included=form.breakfast_included.data,
            wifi_included=form.wifi_included.data,
            status=form.status.data,
            confirmation_number=form.confirmation_number.data,
            notes=form.notes.data,
            special_requests=form.special_requests.data
        )
        
        reservation.calculate_fields()
        
        db.session.add(reservation)
        db.session.commit()
        
        # Bildirim: yeni otel rezervasyonu
        try:
            from app.utils.notifications import notify_distributor_admins
            link = url_for('main.patient_detail', id=patient.id, _external=True)
            notify_distributor_admins(current_user.distributor_id, 'Otel Rezervasyonu Oluşturuldu', f'{patient.first_name} {patient.last_name} için {reservation.hotel_name} kaydı yapıldı.', link, 'info', 'reservation')
        except Exception:
            pass

        flash('Otel rezervasyonu başarıyla oluşturuldu', 'success')
        return redirect(url_for('main.patient_detail', id=patient.id))
    
    return render_template('main/hotel_reservation_form.html',
                         form=form,
                         patient=patient,
                         reservation=None)

@bp.route('/hotel/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_hotel_reservation(id):
    """Edit hotel reservation"""
    reservation = HotelReservation.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    form = HotelReservationForm(obj=reservation)
    
    if form.validate_on_submit():
        reservation.hotel_name = form.hotel_name.data
        reservation.hotel_address = form.hotel_address.data
        reservation.hotel_phone = form.hotel_phone.data
        reservation.hotel_stars = form.hotel_stars.data
        reservation.room_type = form.room_type.data
        reservation.check_in = form.check_in.data
        reservation.check_out = form.check_out.data
        reservation.price_per_night = form.price_per_night.data or 0
        reservation.currency = form.currency.data or 'EUR'
        reservation.transfer_included = form.transfer_included.data
        reservation.transfer_type = form.transfer_type.data
        reservation.transfer_cost = form.transfer_cost.data or 0
        reservation.airport_code = form.airport_code.data
        reservation.airport_name = form.airport_name.data
        reservation.flight_number = form.flight_number.data
        reservation.arrival_time = form.arrival_time.data
        reservation.departure_time = form.departure_time.data
        reservation.breakfast_included = form.breakfast_included.data
        reservation.wifi_included = form.wifi_included.data
        reservation.status = form.status.data
        reservation.confirmation_number = form.confirmation_number.data
        reservation.notes = form.notes.data
        reservation.special_requests = form.special_requests.data
        reservation.updated_at = datetime.utcnow()
        
        reservation.calculate_fields()
        
        db.session.commit()
        
        flash('Otel rezervasyonu güncellendi', 'success')
        return redirect(url_for('main.patient_detail', id=reservation.patient_id))
    
    return render_template('main/hotel_reservation_form.html',
                         form=form,
                         patient=reservation.patient,
                         reservation=reservation)

@bp.route('/hotel/<int:id>/delete', methods=['POST'])
@login_required
def delete_hotel_reservation(id):
    """Delete hotel reservation"""
    reservation = HotelReservation.query.filter_by(
        id=id,
        distributor_id=current_user.distributor_id
    ).first_or_404()
    
    patient_id = reservation.patient_id
    
    db.session.delete(reservation)
    db.session.commit()
    
    flash('Otel rezervasyonu silindi', 'success')
    return redirect(url_for('main.patient_detail', id=patient_id))

@bp.route('/hotel/<int:id>/pdf')
@login_required
def hotel_reservation_pdf(id):
    from flask import send_file
    from app.models import HotelReservation
    from app.utils.pdf_generator import HotelReservationPDFGenerator

    reservation = HotelReservation.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    generator = HotelReservationPDFGenerator(reservation, reservation.distributor)
    pdf_buffer = generator.generate()
    filename = f"otel_rezervasyon_{reservation.id}_{reservation.patient.first_name}_{reservation.patient.last_name}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )

@bp.route('/hotel/<int:id>/email', methods=['POST'])
@login_required
def hotel_reservation_email(id):
    from app.models import HotelReservation
    from app.utils.pdf_generator import HotelReservationPDFGenerator
    from app.utils.email import send_email

    reservation = HotelReservation.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    patient = reservation.patient
    if not patient.email:
        flash('Hasta için e-posta adresi bulunamadı. Hasta kartından e-posta ekleyin.', 'warning')
        return redirect(url_for('main.patient_detail', id=patient.id))

    generator = HotelReservationPDFGenerator(reservation, reservation.distributor)
    pdf_buffer = generator.generate()
    pdf_bytes = pdf_buffer.getvalue()

    subject = f"Otel Rezervasyon Onayı - {reservation.hotel_name}"
    text_body = f"""
Sayın {patient.first_name} {patient.last_name},

Otel rezervasyon onayınız ekte PDF olarak iletilmiştir.

Otel: {reservation.hotel_name}
Giriş: {reservation.check_in.strftime('%d.%m.%Y')}
Çıkış: {reservation.check_out.strftime('%d.%m.%Y')}
Toplam: {reservation.total_cost:.2f} €

İyi konaklamalar dileriz.
{reservation.distributor.name}
"""
    html_body = f"""
    <p>Sayın <strong>{patient.first_name} {patient.last_name}</strong>,</p>
    <p>Otel rezervasyon onayınız ekte PDF olarak iletilmiştir.</p>
    <p>
        <strong>Otel:</strong> {reservation.hotel_name}<br>
        <strong>Giriş:</strong> {reservation.check_in.strftime('%d.%m.%Y')}<br>
        <strong>Çıkış:</strong> {reservation.check_out.strftime('%d.%m.%Y')}<br>
        <strong>Toplam:</strong> {reservation.total_cost:.2f} €
    </p>
    <p>İyi konaklamalar dileriz.<br>{reservation.distributor.name}</p>
    """

    try:
        send_email(subject, [patient.email], text_body, html_body, attachments=[(f"otel_rezervasyon_{reservation.id}.pdf", 'application/pdf', pdf_bytes)])
        flash('Otel rezervasyon onayı e-posta ile gönderildi.', 'success')
    except Exception as e:
        flash(f'E-posta gönderilemedi: {e}', 'danger')

    return redirect(url_for('main.patient_detail', id=patient.id))

@bp.route('/encounter/<int:id>/request_approval', methods=['POST'])
@login_required
def request_approval(id):
    """Create approval token and link for encounter quote"""
    encounter = Encounter.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    # Check if approval already exists
    approval = QuoteApproval.query.filter_by(encounter_id=id).first()
    if not approval:
        token = secrets.token_urlsafe(32)
        approval = QuoteApproval(encounter_id=id, token=token, status='pending')
        db.session.add(approval)
        db.session.commit()
    
    # Generate link
    approval_url = url_for('main.approve_quote', token=approval.token, _external=True)
    
    flash(f'Onay linki oluşturuldu: {approval_url}', 'success')
    return redirect(url_for('main.encounter_detail', id=id))

@bp.route('/approve/<token>', methods=['GET', 'POST'])
def approve_quote(token):
    """Public page for approving quote"""
    approval = QuoteApproval.query.filter_by(token=token).first_or_404()
    encounter = approval.encounter
    
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'approve':
            approval.status = 'approved'
            approval.approved_at = datetime.utcnow()
            approval.approved_by_name = request.form.get('name')
            approval.approved_by_email = request.form.get('email')
            approval.notes = request.form.get('notes')
            encounter.status = 'approved'
            db.session.commit()
            # Bildirim: Oluşturan kullanıcıya ve adminlere bilgi ver
            try:
                from app.utils.notifications import notify_distributor_admins, notify_users
                link = url_for('main.encounter_detail', id=encounter.id, _external=True)
                notify_distributor_admins(encounter.distributor_id, 'Teklif Onaylandı', f'Muayene #{encounter.id} teklifi onaylandı.', link, 'success', 'approval')
                if encounter.created_by:
                    notify_users([encounter.created_by], 'Teklif Onaylandı', f'Muayene #{encounter.id} teklifi onaylandı.', link, 'success', 'approval', encounter.distributor_id)
            except Exception:
                pass
            flash('Teklif onaylandı. Teşekkür ederiz!', 'success')
        elif action == 'reject':
            approval.status = 'rejected'
            approval.approved_at = datetime.utcnow()
            approval.approved_by_name = request.form.get('name')
            approval.approved_by_email = request.form.get('email')
            approval.notes = request.form.get('notes')
            db.session.commit()
            try:
                from app.utils.notifications import notify_distributor_admins, notify_users
                link = url_for('main.encounter_detail', id=encounter.id, _external=True)
                notify_distributor_admins(encounter.distributor_id, 'Teklif Reddedildi', f'Muayene #{encounter.id} teklifi reddedildi.', link, 'warning', 'approval')
                if encounter.created_by:
                    notify_users([encounter.created_by], 'Teklif Reddedildi', f'Muayene #{encounter.id} teklifi reddedildi.', link, 'warning', 'approval', encounter.distributor_id)
            except Exception:
                pass
            flash('Teklif reddedildi.', 'info')
        return redirect(url_for('main.approve_quote', token=token))
    
    return render_template('main/approve_quote.html', approval=approval, encounter=encounter)


# ========== NOTIFICATION ROUTES ==========

@bp.route('/notifications')
@login_required
def notifications():
    """List notifications for current user/distributor."""
    page = request.args.get('page', 1, type=int)
    q = Notification.query.order_by(Notification.created_at.desc())
    # Scope by distributor
    if current_user.distributor_id:
        q = q.filter(db.or_(Notification.distributor_id == current_user.distributor_id,
                            Notification.distributor_id.is_(None)))
    # Scope by user unless admin
    if not current_user.is_admin():
        q = q.filter(db.or_(Notification.user_id == current_user.id,
                            Notification.user_id.is_(None)))
    notifs = q.paginate(page=page, per_page=20)
    return render_template('main/notifications.html', notifications=notifs)


@bp.route('/notifications/<int:id>/read', methods=['POST'])
@login_required
def notification_mark_read(id):
    n = Notification.query.get_or_404(id)
    # Permission: same distributor and either targeted to user or broadcast; admins allowed
    if current_user.distributor_id and n.distributor_id not in (None, current_user.distributor_id):
        abort(403)
    if n.user_id and n.user_id != current_user.id and not current_user.is_admin():
        abort(403)
    n.mark_read()
    db.session.commit()
    flash('Bildirim okundu olarak işaretlendi.', 'info')
    return redirect(request.referrer or url_for('main.notifications'))


@bp.route('/notifications/read_all', methods=['POST'])
@login_required
def notification_mark_all_read():
    q = Notification.query.filter_by(is_read=False)
    if current_user.distributor_id:
        q = q.filter(db.or_(Notification.distributor_id == current_user.distributor_id,
                            Notification.distributor_id.is_(None)))
    if not current_user.is_admin():
        q = q.filter(db.or_(Notification.user_id == current_user.id,
                            Notification.user_id.is_(None)))
    updated = 0
    for n in q.all():
        n.mark_read()
        updated += 1
    db.session.commit()
    flash(f'{updated} bildirim okundu olarak işaretlendi.', 'success')
    return redirect(request.referrer or url_for('main.notifications'))


# ========== APPOINTMENT/CALENDAR ROUTES ==========

@bp.route('/appointments/calendar')
@login_required
def appointments_calendar():
    """Calendar view for appointments."""
    from datetime import datetime, timedelta
    import calendar as cal
    
    # Get month/year from query params or default to current
    year = request.args.get('year', datetime.utcnow().year, type=int)
    month = request.args.get('month', datetime.utcnow().month, type=int)
    view = request.args.get('view', 'month', type=str)  # month, week
    
    # Month view
    if view == 'month':
        # First and last day of month
        first_day = datetime(year, month, 1)
        last_day_num = cal.monthrange(year, month)[1]
        last_day = datetime(year, month, last_day_num, 23, 59, 59)
        
        # Get appointments for this month
        appointments = Appointment.query.filter(
            Appointment.distributor_id == current_user.distributor_id,
            Appointment.start_time >= first_day,
            Appointment.start_time <= last_day
        ).order_by(Appointment.start_time.asc()).all()
        
        # Build calendar grid
        month_cal = cal.monthcalendar(year, month)
        
        return render_template('main/appointments_calendar.html',
                             appointments=appointments,
                             year=year,
                             month=month,
                             month_name=cal.month_name[month],
                             month_cal=month_cal,
                             view=view,
                             timedelta=timedelta)
    
    # Week view
    else:
        # Get week start (Monday)
        date_str = request.args.get('date', datetime.utcnow().strftime('%Y-%m-%d'))
        current_date = datetime.strptime(date_str, '%Y-%m-%d')
        week_start = current_date - timedelta(days=current_date.weekday())
        week_end = week_start + timedelta(days=6, hours=23, minutes=59, seconds=59)
        
        appointments = Appointment.query.filter(
            Appointment.distributor_id == current_user.distributor_id,
            Appointment.start_time >= week_start,
            Appointment.start_time <= week_end
        ).order_by(Appointment.start_time.asc()).all()
        
        # Build week days
        week_days = [week_start + timedelta(days=i) for i in range(7)]
        
        return render_template('main/appointments_calendar.html',
                             appointments=appointments,
                             week_start=week_start,
                             week_days=week_days,
                             view=view,
                             timedelta=timedelta)


@bp.route('/appointments/list')
@login_required
def appointments_list():
    """List view with filters."""
    page = request.args.get('page', 1, type=int)
    status = request.args.get('status', '', type=str)
    patient_search = request.args.get('patient', '', type=str)
    date_from = request.args.get('date_from', '', type=str)
    date_to = request.args.get('date_to', '', type=str)
    
    query = Appointment.query.filter_by(distributor_id=current_user.distributor_id)
    
    if status:
        query = query.filter(Appointment.status == status)
    
    if patient_search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{patient_search}%'),
                Patient.last_name.ilike(f'%{patient_search}%')
            )
        )
    
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d')
            query = query.filter(Appointment.start_time >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            from datetime import timedelta
            to_date = datetime.strptime(date_to, '%Y-%m-%d') + timedelta(days=1)
            query = query.filter(Appointment.start_time < to_date)
        except ValueError:
            pass
    
    appointments = query.order_by(Appointment.start_time.desc()).paginate(page=page, per_page=20)
    
    return render_template('main/appointments_list.html',
                         appointments=appointments,
                         status=status,
                         patient_search=patient_search,
                         date_from=date_from,
                         date_to=date_to)


@bp.route('/appointments/new', methods=['GET', 'POST'])
@login_required
def new_appointment():
    """Create new appointment."""
    if request.method == 'POST':
        patient_id = request.form.get('patient_id', type=int)
        title = request.form.get('title')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        
        if not all([patient_id, title, start_str, end_str]):
            flash('Lütfen tüm zorunlu alanları doldurun.', 'warning')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        try:
            start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Geçersiz tarih/saat formatı.', 'danger')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        if end_time <= start_time:
            flash('Bitiş zamanı başlangıç zamanından sonra olmalıdır.', 'warning')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        # Check for conflicts (optional: same doctor/room)
        conflict = check_appointment_conflict(current_user.distributor_id, start_time, end_time,
                                             request.form.get('doctor_name'), request.form.get('room_number'))
        if conflict:
            flash(f'Çakışma tespit edildi: {conflict.title} ({conflict.start_time.strftime("%d.%m.%Y %H:%M")})', 'warning')
        
        appointment = Appointment(
            distributor_id=current_user.distributor_id,
            patient_id=patient_id,
            encounter_id=request.form.get('encounter_id') or None,
            created_by=current_user.id,
            title=title,
            description=request.form.get('description'),
            appointment_type=request.form.get('appointment_type', 'consultation'),
            start_time=start_time,
            end_time=end_time,
            status='scheduled',
            doctor_name=request.form.get('doctor_name'),
            room_number=request.form.get('room_number'),
            notes=request.form.get('notes')
        )
        
        db.session.add(appointment)
        db.session.commit()
        
        # Notification
        try:
            from app.utils.notifications import notify_distributor_admins
            link = url_for('main.appointments_list', _external=True)
            notify_distributor_admins(current_user.distributor_id, 'Yeni Randevu',
                                    f'{appointment.patient.first_name} {appointment.patient.last_name} için randevu oluşturuldu: {title}',
                                    link, 'info', 'appointment')
        except Exception:
            pass
        
        flash('Randevu başarıyla oluşturuldu.', 'success')
        return redirect(url_for('main.appointments_list'))
    
    # GET: render form
    patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).order_by(Patient.first_name).all()
    return render_template('main/appointment_form.html', patients=patients, appointment=None)


@bp.route('/appointments/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_appointment(id):
    """Edit existing appointment."""
    appointment = Appointment.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    if request.method == 'POST':
        title = request.form.get('title')
        start_str = request.form.get('start_time')
        end_str = request.form.get('end_time')
        
        if not all([title, start_str, end_str]):
            flash('Lütfen tüm zorunlu alanları doldurun.', 'warning')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        try:
            start_time = datetime.strptime(start_str, '%Y-%m-%dT%H:%M')
            end_time = datetime.strptime(end_str, '%Y-%m-%dT%H:%M')
        except ValueError:
            flash('Geçersiz tarih/saat formatı.', 'danger')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        if end_time <= start_time:
            flash('Bitiş zamanı başlangıç zamanından sonra olmalıdır.', 'warning')
            return redirect(request.referrer or url_for('main.appointments_list'))
        
        # Check conflict (exclude current appointment)
        conflict = check_appointment_conflict(current_user.distributor_id, start_time, end_time,
                                             request.form.get('doctor_name'), request.form.get('room_number'),
                                             exclude_id=id)
        if conflict:
            flash(f'Çakışma tespit edildi: {conflict.title} ({conflict.start_time.strftime("%d.%m.%Y %H:%M")})', 'warning')
        
        appointment.title = title
        appointment.description = request.form.get('description')
        appointment.appointment_type = request.form.get('appointment_type', 'consultation')
        appointment.start_time = start_time
        appointment.end_time = end_time
        appointment.status = request.form.get('status', 'scheduled')
        appointment.doctor_name = request.form.get('doctor_name')
        appointment.room_number = request.form.get('room_number')
        appointment.notes = request.form.get('notes')
        appointment.updated_at = datetime.utcnow()
        
        db.session.commit()
        flash('Randevu güncellendi.', 'success')
        return redirect(url_for('main.appointments_list'))
    
    patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).order_by(Patient.first_name).all()
    return render_template('main/appointment_form.html', patients=patients, appointment=appointment)


@bp.route('/appointments/<int:id>/cancel', methods=['POST'])
@login_required
def cancel_appointment(id):
    """Cancel appointment."""
    appointment = Appointment.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    appointment.status = 'cancelled'
    appointment.cancellation_reason = request.form.get('reason', '')
    appointment.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Notify
    try:
        from app.utils.notifications import notify_distributor_admins
        notify_distributor_admins(current_user.distributor_id, 'Randevu İptal Edildi',
                                f'{appointment.patient.first_name} {appointment.patient.last_name} randevusu iptal edildi.',
                                None, 'warning', 'appointment')
    except Exception:
        pass
    
    flash('Randevu iptal edildi.', 'info')
    return redirect(request.referrer or url_for('main.appointments_list'))


@bp.route('/appointments/<int:id>/delete', methods=['POST'])
@login_required
def delete_appointment(id):
    """Delete appointment (admin only)."""
    if not current_user.is_admin():
        abort(403)
    appointment = Appointment.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    db.session.delete(appointment)
    db.session.commit()
    flash('Randevu silindi.', 'success')
    return redirect(request.referrer or url_for('main.appointments_list'))


@bp.route('/appointments/send_reminders', methods=['POST'])
@login_required
def send_appointment_reminders():
    """Send reminders for upcoming appointments (within next 24h)."""
    if not current_user.is_admin():
        abort(403)
    
    from datetime import timedelta
    now = datetime.utcnow()
    tomorrow = now + timedelta(hours=24)
    
    upcoming = Appointment.query.filter(
        Appointment.distributor_id == current_user.distributor_id,
        Appointment.status == 'scheduled',
        Appointment.start_time >= now,
        Appointment.start_time <= tomorrow,
        Appointment.reminder_sent_at.is_(None)
    ).all()
    
    sent = 0
    for appt in upcoming:
        # Send notification
        try:
            from app.utils.notifications import notify_users
            link = url_for('main.appointments_list', _external=True)
            if appt.patient.email:
                # Could also send email via notify_users with channel='email'
                pass
            # In-app notification
            if appt.created_by:
                notify_users([appt.created_by], 'Randevu Hatırlatması',
                           f'{appt.patient.first_name} {appt.patient.last_name} randevusu: {appt.start_time.strftime("%d.%m.%Y %H:%M")}',
                           link, 'info', 'appointment', current_user.distributor_id)
            appt.reminder_sent_at = now
            appt.reminder_method = 'in_app'
            sent += 1
        except Exception as e:
            current_app.logger.warning(f'Reminder send failed for appointment {appt.id}: {e}')
    
    db.session.commit()
    flash(f'{sent} randevu hatırlatması gönderildi.', 'success')
    return redirect(request.referrer or url_for('main.appointments_list'))


def check_appointment_conflict(distributor_id, start_time, end_time, doctor_name=None, room_number=None, exclude_id=None):
    """Check if appointment conflicts with existing ones (same doctor or room)."""
    q = Appointment.query.filter(
        Appointment.distributor_id == distributor_id,
        Appointment.status.in_(['scheduled', 'confirmed']),
        db.or_(
            db.and_(Appointment.start_time < end_time, Appointment.end_time > start_time)
        )
    )
    if exclude_id:
        q = q.filter(Appointment.id != exclude_id)
    
    # If doctor specified, check doctor conflict
    if doctor_name:
        q = q.filter(Appointment.doctor_name == doctor_name)
        conflict = q.first()
        if conflict:
            return conflict
    
    # If room specified, check room conflict
    if room_number:
        q2 = Appointment.query.filter(
            Appointment.distributor_id == distributor_id,
            Appointment.status.in_(['scheduled', 'confirmed']),
            Appointment.room_number == room_number,
            db.or_(
                db.and_(Appointment.start_time < end_time, Appointment.end_time > start_time)
            )
        )
        if exclude_id:
            q2 = q2.filter(Appointment.id != exclude_id)
        conflict = q2.first()
        if conflict:
            return conflict
    
    return None


# ========== DOCUMENT MANAGEMENT ==========

@bp.route('/documents')
@login_required
def documents():
    """List documents with filters."""
    page = request.args.get('page', 1, type=int)
    doc_type = request.args.get('type', '', type=str)
    patient_search = request.args.get('patient', '', type=str)
    archived = request.args.get('archived', '0', type=str)
    
    query = Document.query.filter_by(distributor_id=current_user.distributor_id)
    
    if archived == '1':
        query = query.filter_by(is_archived=True)
    else:
        query = query.filter_by(is_archived=False)
    
    if doc_type:
        query = query.filter_by(document_type=doc_type)
    
    if patient_search:
        query = query.join(Patient).filter(
            db.or_(
                Patient.first_name.ilike(f'%{patient_search}%'),
                Patient.last_name.ilike(f'%{patient_search}%')
            )
        )
    
    documents = query.order_by(Document.uploaded_at.desc()).paginate(page=page, per_page=20)
    
    return render_template('main/documents.html',
                         documents=documents,
                         doc_type=doc_type,
                         patient_search=patient_search,
                         archived=archived)


@bp.route('/documents/upload', methods=['GET', 'POST'])
@login_required
def upload_document():
    """Upload new document."""
    if request.method == 'POST':
        from werkzeug.utils import secure_filename
        import uuid
        from flask import current_app
        
        file = request.files.get('file')
        if not file or not file.filename:
            flash('Lütfen bir dosya seçin.', 'warning')
            return redirect(request.referrer or url_for('main.documents'))
        
        title = request.form.get('title') or file.filename
        patient_id = request.form.get('patient_id') or None
        encounter_id = request.form.get('encounter_id') or None
        
        # Secure filename
        original_filename = secure_filename(file.filename)
        ext = os.path.splitext(original_filename)[1]
        stored_filename = f"{uuid.uuid4().hex}{ext}"
        
        # Save file
        upload_folder = current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads')
        os.makedirs(upload_folder, exist_ok=True)
        file_path = os.path.join(upload_folder, stored_filename)
        file.save(file_path)
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        doc = Document(
            distributor_id=current_user.distributor_id,
            patient_id=patient_id,
            encounter_id=encounter_id,
            uploaded_by=current_user.id,
            title=title,
            description=request.form.get('description'),
            filename=original_filename,
            stored_filename=stored_filename,
            file_path=f'uploads/{stored_filename}',
            file_size=file_size,
            mime_type=file.content_type,
            document_type=request.form.get('document_type', 'other'),
            tags=request.form.get('tags'),
            is_public=bool(request.form.get('is_public'))
        )
        
        db.session.add(doc)
        db.session.commit()
        
        flash('Doküman başarıyla yüklendi.', 'success')
        return redirect(url_for('main.documents'))
    
    patients = Patient.query.filter_by(distributor_id=current_user.distributor_id).order_by(Patient.first_name).all()
    return render_template('main/document_upload.html', patients=patients)


@bp.route('/documents/<int:id>/download')
@login_required
def download_document(id):
    """Download document."""
    from flask import send_file, current_app
    
    doc = Document.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), doc.stored_filename)
    
    if not os.path.exists(file_path):
        flash('Dosya bulunamadı.', 'danger')
        return redirect(url_for('main.documents'))
    
    return send_file(file_path, as_attachment=True, download_name=doc.filename)


@bp.route('/documents/<int:id>/view')
@login_required
def view_document(id):
    """View document inline (for images/PDFs)."""
    from flask import send_file, current_app
    
    doc = Document.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), doc.stored_filename)
    
    if not os.path.exists(file_path):
        flash('Dosya bulunamadı.', 'danger')
        return redirect(url_for('main.documents'))
    
    return send_file(file_path, mimetype=doc.mime_type)


@bp.route('/documents/<int:id>/archive', methods=['POST'])
@login_required
def archive_document(id):
    """Archive document."""
    doc = Document.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    doc.is_archived = True
    doc.archived_at = datetime.utcnow()
    db.session.commit()
    flash('Doküman arşivlendi.', 'info')
    return redirect(request.referrer or url_for('main.documents'))


@bp.route('/documents/<int:id>/unarchive', methods=['POST'])
@login_required
def unarchive_document(id):
    """Unarchive document."""
    doc = Document.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    doc.is_archived = False
    doc.archived_at = None
    db.session.commit()
    flash('Doküman arşivden çıkarıldı.', 'info')
    return redirect(request.referrer or url_for('main.documents'))


@bp.route('/documents/<int:id>/delete', methods=['POST'])
@login_required
def delete_document(id):
    """Delete document (admin only)."""
    if not current_user.is_admin():
        abort(403)
    
    from flask import current_app
    
    doc = Document.query.filter_by(id=id, distributor_id=current_user.distributor_id).first_or_404()
    
    # Delete physical file
    file_path = os.path.join(current_app.config.get('UPLOAD_FOLDER', 'app/static/uploads'), doc.stored_filename)
    if os.path.exists(file_path):
        os.remove(file_path)
    
    db.session.delete(doc)
    db.session.commit()
    flash('Doküman silindi.', 'success')
    return redirect(request.referrer or url_for('main.documents'))