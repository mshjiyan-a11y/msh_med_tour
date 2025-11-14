"""
Basitleştirilmiş Örnek Veri Oluşturucu
Sadece temel alanlarla çalışır
"""
from app import create_app, db
from app.models import (
    Patient, Lead, LeadNote, Encounter, Message, 
    PatientJourney, JourneyStep, Flight, Transfer,
    HotelReservation, User, Distributor
)
from datetime import datetime, timedelta
import random

app = create_app()

def create_simple_data():
    with app.app_context():
        print("=== Basit Örnek Veri Oluşturuluyor ===\n")
        
        # Get existing distributor and user
        distributor = Distributor.query.first()
        if not distributor:
            print("❌ Distributor bulunamadı!")
            return
        
        user = User.query.filter_by(distributor_id=distributor.id).first()
        if not user:
            print("❌ User bulunamadı!")
            return
        
        dist_id = distributor.id
        user_id = user.id
        
        # 1. 10 Lead oluştur
        print("1. Leads oluşturuluyor...")
        leads_data = [
            {'first_name': 'Ahmet', 'last_name': 'Yılmaz', 'email': 'ahmet@test.com', 'phone': '+90 532 111 1111', 'country': 'Turkey', 'interested_service': 'hair', 'message': 'Saç ekimi', 'status': 'new'},
            {'first_name': 'Fatma', 'last_name': 'Demir', 'email': 'fatma@test.com', 'phone': '+90 533 222 2222', 'country': 'Turkey', 'interested_service': 'dental', 'message': 'Diş implantı', 'status': 'contacted'},
            {'first_name': 'Mohammed', 'last_name': 'Al-Rashid', 'email': 'mohammed@test.com', 'phone': '+966 50 333 3333', 'country': 'Saudi Arabia', 'interested_service': 'hair', 'message': 'Hair transplant', 'status': 'qualified'},
            {'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah@test.com', 'phone': '+44 20 444 4444', 'country': 'UK', 'interested_service': 'aesthetic', 'message': 'Rhinoplasty', 'status': 'contacted'},
            {'first_name': 'Ali', 'last_name': 'Hassan', 'email': 'ali@test.com', 'phone': '+971 50 555 5555', 'country': 'UAE', 'interested_service': 'dental', 'message': 'Dental implants', 'status': 'new'},
            {'first_name': 'Elena', 'last_name': 'Petrova', 'email': 'elena@test.com', 'phone': '+7 495 666 6666', 'country': 'Russia', 'interested_service': 'aesthetic', 'message': 'Cosmetic surgery', 'status': 'qualified'},
            {'first_name': 'John', 'last_name': 'Smith', 'email': 'john@test.com', 'phone': '+1 555 777 7777', 'country': 'USA', 'interested_service': 'bariatric', 'message': 'Weight loss surgery', 'status': 'contacted'},
            {'first_name': 'Zeynep', 'last_name': 'Kaya', 'email': 'zeynep@test.com', 'phone': '+90 534 888 8888', 'country': 'Turkey', 'interested_service': 'ivf', 'message': 'IVF tedavisi', 'status': 'new'},
            {'first_name': 'Ahmed', 'last_name': 'Ibrahim', 'email': 'ahmed@test.com', 'phone': '+20 10 999 9999', 'country': 'Egypt', 'interested_service': 'eye', 'message': 'LASIK surgery', 'status': 'qualified'},
            {'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria@test.com', 'phone': '+34 91 000 0000', 'country': 'Spain', 'interested_service': 'dental', 'message': 'Veneers', 'status': 'contacted'}
        ]
        
        leads = []
        for ld in leads_data:
            lead = Lead(distributor_id=dist_id, source='website', **ld)
            db.session.add(lead)
            leads.append(lead)
        db.session.commit()
        print(f"   ✓ {len(leads)} lead oluşturuldu")
        
        # 2. İlk 5 lead'i hastaya dönüştür
        print("\n2. İlk 5 lead hastaya dönüştürülüyor...")
        patients = []
        
        for i in range(5):
            lead = leads[i]
            patient = Patient(
                distributor_id=dist_id,
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
                user_id=user_id,
                note=f'{lead.first_name} {lead.last_name} hastaya dönüştürüldü - {datetime.now().strftime("%d.%m.%Y")}'
            )
            db.session.add(note)
        
        db.session.commit()
        print(f"   ✓ {len(patients)} hasta oluşturuldu")
        
        # 3. Her hasta için muayene oluştur
        print("\n3. Muayeneler oluşturuluyor...")
        encounters = []
        
        for patient in patients:
            encounter = Encounter(
                distributor_id=dist_id,
                patient_id=patient.id,
                date=datetime.now() - timedelta(days=random.randint(1, 20)),
                note=f'{patient.first_name} için muayene - tedavi planı hazırlandı',
                status='final',
                created_by=user_id
            )
            db.session.add(encounter)
            encounters.append(encounter)
        
        db.session.commit()
        print(f"   ✓ {len(encounters)} muayene oluşturuldu")
        
        # 4. Yolculuk planları
        print("\n4. Yolculuk planları oluşturuluyor...")
        journeys = []
        
        for i, patient in enumerate(patients):
            journey = PatientJourney(
                distributor_id=dist_id,
                patient_id=patient.id,
                journey_code=f'TRV-2025-{str(i+1).zfill(3)}',
                arrival_date=datetime.now() + timedelta(days=15 + i*7),
                departure_date=datetime.now() + timedelta(days=22 + i*7),
                status='planned',
                coordinator_id=user_id,
                purpose=f'{patient.full_name} - Treatment Journey',
                created_by=user_id
            )
            db.session.add(journey)
            journeys.append(journey)
        
        db.session.commit()
        
        # Journey steps
        for journey in journeys:
            steps_data = [
                {'step_type': 'arrival', 'title': 'Havaalanı Karşılama', 'scheduled_date': journey.arrival_date, 'status': 'pending'},
                {'step_type': 'consultation', 'title': 'İlk Konsültasyon', 'scheduled_date': journey.arrival_date + timedelta(days=1), 'status': 'pending'},
                {'step_type': 'procedure', 'title': 'Tedavi/Ameliyat', 'scheduled_date': journey.arrival_date + timedelta(days=2), 'status': 'pending'},
                {'step_type': 'follow_up', 'title': 'Kontrol Muayenesi', 'scheduled_date': journey.arrival_date + timedelta(days=5), 'status': 'pending'},
                {'step_type': 'departure', 'title': 'Havaalanı Uğurlama', 'scheduled_date': journey.departure_date, 'status': 'pending'}
            ]
            
            for seq, step_data in enumerate(steps_data, 1):
                step = JourneyStep(journey_id=journey.id, sequence=seq, **step_data)
                db.session.add(step)
        
        db.session.commit()
        print(f"   ✓ {len(journeys)} yolculuk planı + adımları oluşturuldu")
        
        # 5. Uçuş bilgileri
        print("\n5. Uçuş bilgileri ekleniyor...")
        airlines = ['Turkish Airlines', 'Emirates', 'Lufthansa', 'British Airways', 'Qatar Airways']
        
        for i, journey in enumerate(journeys):
            # Gidiş
            outbound = Flight(
                journey_id=journey.id,
                flight_type='outbound',
                airline=airlines[i],
                flight_number=f'{["TK", "EK", "LH", "BA", "QR"][i]}{random.randint(100, 999)}',
                departure_airport=['IST', 'DXB', 'LHR', 'JFK', 'DOH'][i],
                arrival_airport='SAW',
                departure_time=journey.arrival_date.replace(hour=10, minute=0),
                arrival_time=journey.arrival_date.replace(hour=14, minute=0),
                booking_reference=f'BK{random.randint(10000, 99999)}'
            )
            db.session.add(outbound)
            
            # Dönüş
            return_flight = Flight(
                journey_id=journey.id,
                flight_type='return',
                airline=airlines[i],
                flight_number=f'{["TK", "EK", "LH", "BA", "QR"][i]}{random.randint(100, 999)}',
                departure_airport='SAW',
                arrival_airport=['IST', 'DXB', 'LHR', 'JFK', 'DOH'][i],
                departure_time=journey.departure_date.replace(hour=16, minute=0),
                arrival_time=journey.departure_date.replace(hour=20, minute=0),
                booking_reference=f'BK{random.randint(10000, 99999)}'
            )
            db.session.add(return_flight)
        
        db.session.commit()
        print(f"   ✓ {len(journeys) * 2} uçuş bilgisi eklendi")
        
        # 6. Transfer hizmetleri
        print("\n6. Transfer hizmetleri ekleniyor...")
        
        for i, journey in enumerate(journeys):
            # Havaalanı karşılama
            pickup = Transfer(
                journey_id=journey.id,
                transfer_type='airport_pickup',
                from_location='SAW Airport',
                to_location='Hotel Luxury Istanbul',
                scheduled_time=journey.arrival_date.replace(hour=14, minute=30),
                vehicle_type='VIP Van',
                driver_name='Mehmet Yılmaz',
                driver_phone='+90 555 123 4567',
                cost=75.00,
                currency='EUR',
                status='confirmed'
            )
            db.session.add(pickup)
            
            # Havaalanı uğurlama
            dropoff = Transfer(
                journey_id=journey.id,
                transfer_type='airport_dropoff',
                from_location='Hotel Luxury Istanbul',
                to_location='SAW Airport',
                scheduled_time=journey.departure_date.replace(hour=13, minute=0),
                vehicle_type='VIP Van',
                driver_name='Mehmet Yılmaz',
                driver_phone='+90 555 123 4567',
                cost=75.00,
                currency='EUR',
                status='confirmed'
            )
            db.session.add(dropoff)
        
        db.session.commit()
        print(f"   ✓ {len(journeys) * 2} transfer hizmeti eklendi")
        
        # 7. Otel rezervasyonları
        print("\n7. Otel rezervasyonları ekleniyor...")
        hotels = [
            {'name': 'Grand Hyatt Istanbul', 'address': 'Harbiye, Taşkışla Cad, 34367 Şişli'},
            {'name': 'Swissotel The Bosphorus', 'address': 'Visnezade Mah., Acisu Sok. No:19, 34357 Beşiktaş'},
            {'name': 'Four Seasons Sultanahmet', 'address': 'Tevkifhane Sk. No:1, 34122 Fatih'},
            {'name': 'Raffles Istanbul', 'address': 'Zorlu Center, Koru Sk. No:2, 34340 Beşiktaş'},
            {'name': 'The Ritz-Carlton Istanbul', 'address': 'Suzer Plaza, Elmadag, 34367 Sisli'}
        ]
        
        for i, journey in enumerate(journeys):
            hotel = hotels[i]
            
            total_nights = (journey.departure_date - journey.arrival_date).days
            reservation = HotelReservation(
                distributor_id=dist_id,
                patient_id=journey.patient_id,
                journey_id=journey.id,
                hotel_name=hotel['name'],
                hotel_address=hotel['address'],
                check_in_date=journey.arrival_date.date(),
                check_out_date=journey.departure_date.date(),
                room_type='Deluxe Room',
                number_of_rooms=1,
                number_of_guests=1,
                total_nights=total_nights,
                price_per_night=180.00,
                total_price=180.00 * total_nights,
                currency='EUR',
                booking_reference=f'HTL{random.randint(10000, 99999)}',
                confirmation_number=f'CONF{random.randint(100000, 999999)}',
                status='confirmed'
            )
            db.session.add(reservation)
        
        db.session.commit()
        print(f"   ✓ {len(journeys)} otel rezervasyonu eklendi")
        
        # 8. Mesajlaşmalar
        print("\n8. Mesajlaşmalar ekleniyor...")
        
        messages_per_patient = [
            ['Merhaba, randevu hakkında bilgi alabilir miyim?', 'Tabii ki! Uygun tarihleri göndereceğim.'],
            ['What is the total package price?', 'I will send you the detailed quote.'],
            ['متى يمكنني السفر؟', 'يمكنك السفر في أي وقت'],
            ['I have some questions about the procedure', 'Our doctor will explain everything.'],
            ['Ameliyat sonrası ne kadar kalmalıyım?', '7 gün yeterli olacaktır.']
        ]
        
        for i, patient in enumerate(patients):
            for j, msg_text in enumerate(messages_per_patient[i]):
                is_from_patient = j % 2 == 0
                
                message = Message(
                    distributor_id=dist_id,
                    patient_id=patient.id,
                    sender_id=None if is_from_patient else user_id,
                    content=msg_text,
                    message_type='text',
                    is_read=not is_from_patient,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 10))
                )
                db.session.add(message)
        
        db.session.commit()
        print(f"   ✓ Mesajlar eklendi")
        
        print("\n" + "="*50)
        print("✅ TÜM ÖRNEK VERİLER BAŞARIYLA OLUŞTURULDU!")
        print("="*50)
        print(f"\n📊 Özet:")
        print(f"   • {Lead.query.filter_by(distributor_id=dist_id).count()} Lead")
        print(f"   • {Patient.query.filter_by(distributor_id=dist_id).count()} Hasta")
        print(f"   • {Encounter.query.filter_by(distributor_id=dist_id).count()} Muayene")
        print(f"   • {PatientJourney.query.filter_by(distributor_id=dist_id).count()} Yolculuk Planı")
        print(f"   • {Flight.query.join(PatientJourney).filter(PatientJourney.distributor_id==dist_id).count()} Uçuş")
        print(f"   • {Transfer.query.join(PatientJourney).filter(PatientJourney.distributor_id==dist_id).count()} Transfer")
        print(f"   • {HotelReservation.query.filter_by(distributor_id=dist_id).count()} Otel Rezervasyonu")
        print(f"   • {Message.query.filter_by(distributor_id=dist_id).count()} Mesaj")

if __name__ == '__main__':
    create_simple_data()
