"""Basit ornek veri ekleyici"""
from app import create_app, db
from app.models import Patient, Lead, LeadNote, Encounter, Message, User, Distributor
from datetime import datetime, timedelta
import random

app = create_app()

with app.app_context():
    print("Ornek veri ekleniyor...\n")
    
    dist = Distributor.query.first()
    user = User.query.filter_by(distributor_id=dist.id).first()
    
    # 1. 10 Lead
    print("1. Leads...")
    leads_data = [
        ('Ahmet', 'Yilmaz', 'ahmet@test.com', '+90 532 111 1111', 'Turkey', 'hair', 'Sac ekimi', 'new'),
        ('Fatma', 'Demir', 'fatma@test.com', '+90 533 222 2222', 'Turkey', 'dental', 'Dis implanti', 'contacted'),
        ('Mohammed', 'Al-Rashid', 'mohammed@test.com', '+966 50 333 3333', 'Saudi Arabia', 'hair', 'Hair transplant', 'qualified'),
        ('Sarah', 'Johnson', 'sarah@test.com', '+44 20 444 4444', 'UK', 'aesthetic', 'Rhinoplasty', 'contacted'),
        ('Ali', 'Hassan', 'ali@test.com', '+971 50 555 5555', 'UAE', 'dental', 'Dental implants', 'new'),
        ('Elena', 'Petrova', 'elena@test.com', '+7 495 666 6666', 'Russia', 'aesthetic', 'Surgery', 'qualified'),
        ('John', 'Smith', 'john@test.com', '+1 555 777 7777', 'USA', 'bariatric', 'Weight loss', 'contacted'),
        ('Zeynep', 'Kaya', 'zeynep@test.com', '+90 534 888 8888', 'Turkey', 'ivf', 'IVF tedavisi', 'new'),
        ('Ahmed', 'Ibrahim', 'ahmed@test.com', '+20 10 999 9999', 'Egypt', 'eye', 'LASIK', 'qualified'),
        ('Maria', 'Garcia', 'maria@test.com', '+34 91 000 0000', 'Spain', 'dental', 'Veneers', 'contacted')
    ]
    
    leads = []
    for fn, ln, em, ph, co, serv, msg, st in leads_data:
        lead = Lead(
            distributor_id=dist.id,
            source='website',
            first_name=fn,
            last_name=ln,
            email=em,
            phone=ph,
            country=co,
            interested_service=serv,
            message=msg,
            status=st
        )
        db.session.add(lead)
        leads.append(lead)
    db.session.commit()
    print(f"   {len(leads)} lead eklendi")
    
    # 2. 5 Hasta
    print("\n2. Hastalar...")
    patients = []
    for i in range(5):
        lead = leads[i]
        patient = Patient(
            distributor_id=dist.id,
            first_name=lead.first_name,
            last_name=lead.last_name,
            email=lead.email,
            phone=lead.phone,
            nationality=lead.country,
            dob=datetime(1985 + i, 1 + i, 10 + i).date(),
            gender='M' if i % 2 == 0 else 'F',
            is_active=True
        )
        db.session.add(patient)
        patients.append(patient)
        
        lead.status = 'converted'
        lead.converted_to_patient_id = patient.id
        
        note = LeadNote(
            lead_id=lead.id,
            user_id=user.id,
            note=f'{lead.first_name} hastaya donusturuldu'
        )
        db.session.add(note)
    
    db.session.commit()
    print(f"   {len(patients)} hasta eklendi")
    
    # 3. Muayeneler
    print("\n3. Muayeneler...")
    for patient in patients:
        enc = Encounter(
            distributor_id=dist.id,
            patient_id=patient.id,
            date=datetime.now() - timedelta(days=random.randint(1, 20)),
            note=f'{patient.first_name} muayenesi',
            status='final',
            created_by=user.id
        )
        db.session.add(enc)
    db.session.commit()
    print(f"   {len(patients)} muayene eklendi")
    
    # 4. Mesajlar
    print("\n4. Mesajlar...")
    messages = [
        ['Merhaba, bilgi alabilir miyim?', 'Tabii, yardimci olayim.'],
        ['What is the price?', 'I will send the quote.'],
        ['متى يمكنني السفر؟', 'في أي وقت'],
        ['I have questions', 'Please ask.'],
        ['Ne kadar kalmaliyim?', '7 gun yeterli.']
    ]
    
    msg_count = 0
    for i, patient in enumerate(patients):
        for j, msg_text in enumerate(messages[i]):
            is_from_patient = j % 2 == 0
            msg = Message(
                distributor_id=dist.id,
                patient_id=patient.id,
                sender_id=None if is_from_patient else user.id,
                content=msg_text,
                message_type='text',
                is_read=not is_from_patient
            )
            db.session.add(msg)
            msg_count += 1
    
    db.session.commit()
    print(f"   {msg_count} mesaj eklendi")
    
    print("\n" + "="*50)
    print("BASARILI!")
    print("="*50)
    print(f"Toplam:")
    print(f"  {Lead.query.filter_by(distributor_id=dist.id).count()} Lead")
    print(f"  {Patient.query.filter_by(distributor_id=dist.id).count()} Hasta")
    print(f"  {Encounter.query.filter_by(distributor_id=dist.id).count()} Muayene")
    print(f"  {Message.query.filter_by(distributor_id=dist.id).count()} Mesaj")
