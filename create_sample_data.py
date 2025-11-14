"""
Sample Data Generator - Örnek veriler oluştur
5 hasta, leads, muayeneler, mesajlar, yolculuklar, oteller
"""
from app import create_app, db
from app.models import (
    Patient, Lead, LeadNote, Encounter, Message, 
    PatientJourney, JourneyStep, Flight, Transfer,
    HotelReservation, CurrencyRate, PriceListItem,
    HairAnnotation, DentalProcedure, EyeRefraction,
    CommunicationLog, User, Distributor
)
from datetime import datetime, timedelta
import random

app = create_app()

def create_sample_data():
    with app.app_context():
        print("=== Örnek Veri Oluşturuluyor ===\n")
        
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
        
        # 1. Leads oluştur (10 adet)
        print("1. Leads oluşturuluyor...")
        leads_data = [
            {
                'first_name': 'Ahmet', 'last_name': 'Yılmaz', 'email': 'ahmet@example.com',
                'phone': '+90 532 123 4567', 'country': 'Türkiye', 'interested_service': 'hair',
                'message': 'Saç ekimi fiyatları hakkında bilgi almak istiyorum', 'status': 'new'
            },
            {
                'first_name': 'Fatma', 'last_name': 'Demir', 'email': 'fatma@example.com',
                'phone': '+90 533 234 5678', 'country': 'Türkiye', 'interested_service': 'dental',
                'message': 'Implant tedavisi için randevu', 'status': 'contacted'
            },
            {
                'first_name': 'Mohammed', 'last_name': 'Al-Rashid', 'email': 'mohammed@example.com',
                'phone': '+966 50 345 6789', 'country': 'Saudi Arabia', 'interested_service': 'hair',
                'message': 'Hair transplant package information needed', 'status': 'qualified'
            },
            {
                'first_name': 'Sarah', 'last_name': 'Johnson', 'email': 'sarah@example.com',
                'phone': '+44 20 7946 0958', 'country': 'United Kingdom', 'interested_service': 'aesthetic',
                'message': 'Rhinoplasty and accommodation details', 'status': 'contacted'
            },
            {
                'first_name': 'Ali', 'last_name': 'Hassan', 'email': 'ali@example.com',
                'phone': '+971 50 456 7890', 'country': 'UAE', 'interested_service': 'dental',
                'message': 'Full mouth dental implants quote', 'status': 'new'
            },
            {
                'first_name': 'Elena', 'last_name': 'Petrova', 'email': 'elena@example.com',
                'phone': '+7 495 123 4567', 'country': 'Russia', 'interested_service': 'aesthetic',
                'message': 'Breast augmentation consultation', 'status': 'qualified'
            },
            {
                'first_name': 'John', 'last_name': 'Smith', 'email': 'john@example.com',
                'phone': '+1 555 123 4567', 'country': 'USA', 'interested_service': 'bariatric',
                'message': 'Gastric sleeve surgery information', 'status': 'contacted'
            },
            {
                'first_name': 'Zeynep', 'last_name': 'Kaya', 'email': 'zeynep@example.com',
                'phone': '+90 534 345 6789', 'country': 'Türkiye', 'interested_service': 'ivf',
                'message': 'IVF tedavisi fiyatları', 'status': 'new'
            },
            {
                'first_name': 'Ahmed', 'last_name': 'Ibrahim', 'email': 'ahmed@example.com',
                'phone': '+20 10 1234 5678', 'country': 'Egypt', 'interested_service': 'eye',
                'message': 'LASIK surgery package', 'status': 'qualified'
            },
            {
                'first_name': 'Maria', 'last_name': 'Garcia', 'email': 'maria@example.com',
                'phone': '+34 91 123 4567', 'country': 'Spain', 'interested_service': 'dental',
                'message': 'Veneers and teeth whitening', 'status': 'contacted'
            }
        ]
        
        leads = []
        for lead_data in leads_data:
            lead = Lead(
                distributor_id=dist_id,
                source='website',
                **lead_data
            )
            db.session.add(lead)
            leads.append(lead)
        
        db.session.commit()
        print(f"   ✓ {len(leads)} lead oluşturuldu\n")
        
        # 2. İlk 5 lead'i hastaya dönüştür
        print("2. Leads hastaya dönüştürülüyor...")
        patients = []
        
        for i, lead in enumerate(leads[:5]):
            patient = Patient(
                distributor_id=dist_id,
                first_name=lead.first_name,
                last_name=lead.last_name,
                email=lead.email,
                phone=lead.phone,
                nationality=lead.country,
                dob=datetime(1990 - i*2, 1 + i, 15).date(),
                gender='M' if i % 2 == 0 else 'F',
                is_active=True
            )
            db.session.add(patient)
            patients.append(patient)
            
            # Lead'i converted olarak işaretle
            lead.status = 'converted'
            lead.converted_to_patient_id = patient.id
            
            # Lead note ekle
            note = LeadNote(
                lead_id=lead.id,
                user_id=user_id,
                note=f'{lead.first_name} hastaya dönüştürüldü - {datetime.now().strftime("%Y-%m-%d %H:%M")}'
            )
            db.session.add(note)
        
        db.session.commit()
        print(f"   ✓ {len(patients)} hasta oluşturuldu\n")
        
        # 3. Muayeneler ekle
        print("3. Muayeneler oluşturuluyor...")
        encounters = []
        
        for i, patient in enumerate(patients):
            encounter = Encounter(
                distributor_id=dist_id,
                patient_id=patient.id,
                encounter_type=['hair', 'dental', 'aesthetic', 'eye', 'bariatric'][i],
                chief_complaint=['Hair loss treatment', 'Dental implants', 'Nose job consultation', 'LASIK evaluation', 'Weight loss surgery'][i],
                diagnosis=['Androgenetic alopecia', 'Multiple missing teeth', 'Deviated septum', 'Myopia', 'Morbid obesity'][i],
                treatment_plan=['FUE hair transplant 4000 grafts', 'Full mouth dental implants', 'Rhinoplasty', 'LASIK both eyes', 'Gastric sleeve'][i],
                estimated_cost=random.randint(3000, 8000),
                currency='USD',
                status='completed',
                appointment_date=datetime.now() - timedelta(days=random.randint(1, 30))
            )
            db.session.add(encounter)
            encounters.append(encounter)
        
        db.session.commit()
        
        # Muayene detayları ekle
        # Hair
        hair_annotation = HairAnnotation(
            encounter_id=encounters[0].id,
            region_id='crown',
            label='Thinning',
            note='Moderate hair loss in crown area'
        )
        db.session.add(hair_annotation)
        
        # Dental
        dental_proc = DentalProcedure(
            encounter_id=encounters[1].id,
            tooth_no='14',
            treatment_type='Implant',
            note='Single implant upper right molar',
            price=1500
        )
        db.session.add(dental_proc)
        
        # Eye
        eye_refraction = EyeRefraction(
            encounter_id=encounters[3].id,
            od_sph=-2.5,
            od_cyl=-0.5,
            od_ax=180,
            os_sph=-3.0,
            os_cyl=-0.75,
            os_ax=175,
            planned_procedure='LASIK'
        )
        db.session.add(eye_refraction)
        
        db.session.commit()
        print(f"   ✓ {len(encounters)} muayene oluşturuldu\n")
        
        # 4. Yolculuk planları oluştur
        print("4. Yolculuk planları oluşturuluyor...")
        journeys = []
        
        for i, patient in enumerate(patients):
            journey = PatientJourney(
                distributor_id=dist_id,
                patient_id=patient.id,
                journey_name=f'{patient.first_name} {patient.last_name} - Treatment Journey',
                start_date=datetime.now() + timedelta(days=10 + i*5),
                end_date=datetime.now() + timedelta(days=17 + i*5),
                status='planned',
                assigned_coordinator_id=user_id,
                total_nights=7,
                number_of_guests=1 + (i % 2)
            )
            db.session.add(journey)
            journeys.append(journey)
        
        db.session.commit()
        
        # Journey steps ekle
        for i, journey in enumerate(journeys):
            steps = [
                {
                    'step_type': 'arrival',
                    'title': 'Airport Pickup',
                    'description': 'VIP transfer from airport to hotel',
                    'scheduled_date': journey.start_date,
                    'status': 'pending'
                },
                {
                    'step_type': 'consultation',
                    'title': 'Initial Consultation',
                    'description': 'Meeting with doctor and final planning',
                    'scheduled_date': journey.start_date + timedelta(days=1),
                    'status': 'pending'
                },
                {
                    'step_type': 'procedure',
                    'title': 'Treatment/Surgery',
                    'description': 'Main medical procedure',
                    'scheduled_date': journey.start_date + timedelta(days=2),
                    'status': 'pending'
                },
                {
                    'step_type': 'follow_up',
                    'title': 'Post-op Check',
                    'description': 'Follow-up examination',
                    'scheduled_date': journey.start_date + timedelta(days=5),
                    'status': 'pending'
                },
                {
                    'step_type': 'departure',
                    'title': 'Airport Drop-off',
                    'description': 'Transfer to airport',
                    'scheduled_date': journey.end_date,
                    'status': 'pending'
                }
            ]
            
            for seq, step_data in enumerate(steps, 1):
                step = JourneyStep(
                    journey_id=journey.id,
                    sequence=seq,
                    **step_data
                )
                db.session.add(step)
        
        db.session.commit()
        print(f"   ✓ {len(journeys)} yolculuk planı oluşturuldu\n")
        
        # 5. Uçuş bilgileri ekle
        print("5. Uçuş bilgileri ekleniyor...")
        
        airlines = ['Turkish Airlines', 'Emirates', 'Lufthansa', 'British Airways', 'Qatar Airways']
        
        for i, journey in enumerate(journeys):
            # Gidiş uçuşu
            outbound = Flight(
                journey_id=journey.id,
                flight_type='outbound',
                airline=airlines[i],
                flight_number=f'{["TK", "EK", "LH", "BA", "QR"][i]}{random.randint(100, 999)}',
                departure_airport=['IST', 'DXB', 'LHR', 'JFK', 'DOH'][i],
                arrival_airport='SAW',
                departure_time=journey.start_date.replace(hour=10, minute=30),
                arrival_time=journey.start_date.replace(hour=14, minute=15),
                booking_reference=f'ABC{random.randint(100, 999)}XY'
            )
            db.session.add(outbound)
            
            # Dönüş uçuşu
            return_flight = Flight(
                journey_id=journey.id,
                flight_type='return',
                airline=airlines[i],
                flight_number=f'{["TK", "EK", "LH", "BA", "QR"][i]}{random.randint(100, 999)}',
                departure_airport='SAW',
                arrival_airport=['IST', 'DXB', 'LHR', 'JFK', 'DOH'][i],
                departure_time=journey.end_date.replace(hour=16, minute=30),
                arrival_time=journey.end_date.replace(hour=20, minute=45),
                booking_reference=f'XYZ{random.randint(100, 999)}AB'
            )
            db.session.add(return_flight)
        
        db.session.commit()
        print(f"   ✓ {len(journeys) * 2} uçuş bilgisi eklendi\n")
        
        # 6. Transfer hizmetleri ekle
        print("6. Transfer hizmetleri ekleniyor...")
        
        for i, journey in enumerate(journeys):
            # Havaalanı karşılama
            pickup = Transfer(
                journey_id=journey.id,
                transfer_type='airport_pickup',
                from_location='SAW Airport',
                to_location='Hotel Luxury Istanbul',
                scheduled_time=journey.start_date.replace(hour=14, minute=30),
                vehicle_type=['VIP Van', 'Luxury Sedan', 'Mercedes Vito', 'BMW 5 Series', 'Mercedes S Class'][i],
                driver_name=['Mehmet', 'Ali', 'Hasan', 'Mustafa', 'Ahmet'][i],
                driver_phone=f'+90 555 {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}',
                cost=50 + i*10,
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
                scheduled_time=journey.end_date.replace(hour=13, minute=30),
                vehicle_type=['VIP Van', 'Luxury Sedan', 'Mercedes Vito', 'BMW 5 Series', 'Mercedes S Class'][i],
                driver_name=['Mehmet', 'Ali', 'Hasan', 'Mustafa', 'Ahmet'][i],
                driver_phone=f'+90 555 {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}',
                cost=50 + i*10,
                currency='EUR',
                status='confirmed'
            )
            db.session.add(dropoff)
        
        db.session.commit()
        print(f"   ✓ {len(journeys) * 2} transfer hizmeti eklendi\n")
        
        # 7. Otel rezervasyonları ekle
        print("7. Otel rezervasyonları ekleniyor...")
        
        hotels = [
            {'name': 'Grand Hyatt Istanbul', 'address': 'Harbiye, Taşkışla Cad, 34367 Şişli'},
            {'name': 'Swissotel The Bosphorus', 'address': 'Visnezade Mah., Acisu Sok. No:19, 34357 Beşiktaş'},
            {'name': 'Four Seasons Sultanahmet', 'address': 'Tevkifhane Sk. No:1, 34122 Fatih'},
            {'name': 'Raffles Istanbul', 'address': 'Zorlu Center, Koru Sk. No:2, 34340 Beşiktaş'},
            {'name': 'The Ritz-Carlton Istanbul', 'address': 'Suzer Plaza, Elmadag, Askerocagi Cad. No:15, 34367 Sisli'}
        ]
        
        for i, journey in enumerate(journeys):
            hotel_info = hotels[i]
            
            reservation = HotelReservation(
                distributor_id=dist_id,
                patient_id=journey.patient_id,
                journey_id=journey.id,
                hotel_name=hotel_info['name'],
                hotel_address=hotel_info['address'],
                check_in_date=journey.start_date.date(),
                check_out_date=journey.end_date.date(),
                room_type=['Deluxe Room', 'Executive Suite', 'Junior Suite', 'Premium Room', 'Grand Suite'][i],
                number_of_rooms=1,
                number_of_guests=journey.number_of_guests,
                total_nights=journey.total_nights,
                price_per_night=150 + i*30,
                total_price=(150 + i*30) * journey.total_nights,
                currency='EUR',
                booking_reference=f'HTL{random.randint(10000, 99999)}',
                confirmation_number=f'CONF{random.randint(100000, 999999)}',
                special_requests=['Non-smoking room', 'High floor', 'Sea view', 'Near elevator', 'Quiet room'][i],
                status='confirmed'
            )
            db.session.add(reservation)
        
        db.session.commit()
        print(f"   ✓ {len(journeys)} otel rezervasyonu eklendi\n")
        
        # 8. Mesajlaşmalar ekle
        print("8. Mesajlaşmalar ekleniyor...")
        
        messages_data = [
            ['Merhaba, randevu talebim hakkında bilgi alabilir miyim?', 'Tabii ki! Size en uygun tarihi ayarlayalım.'],
            ['What is included in the package price?', 'The package includes surgery, accommodation, transfers and medications.'],
            ['متى يمكنني السفر؟', 'يمكنك السفر في أي وقت، نحن جاهزون لاستقبالك'],
            ['I have some concerns about the procedure', 'Don\'t worry, our doctor will explain everything in detail during consultation.'],
            ['Ameliyat sonrası ne kadar süre kalmalıyım?', 'Genellikle 7 gün yeterli oluyor iyileşme için.']
        ]
        
        for i, patient in enumerate(patients):
            for msg_text in messages_data[i]:
                is_from_patient = messages_data[i].index(msg_text) % 2 == 0
                
                message = Message(
                    distributor_id=dist_id,
                    patient_id=patient.id,
                    sender_id=None if is_from_patient else user_id,
                    content=msg_text,
                    message_type='text',
                    is_read=not is_from_patient,
                    created_at=datetime.now() - timedelta(days=random.randint(1, 10), hours=random.randint(0, 23))
                )
                db.session.add(message)
                
                # Communication log
                log = CommunicationLog(
                    distributor_id=dist_id,
                    patient_id=patient.id,
                    user_id=user_id if not is_from_patient else None,
                    communication_type='chat',
                    direction='inbound' if is_from_patient else 'outbound',
                    content=msg_text,
                    status='completed'
                )
                db.session.add(log)
        
        db.session.commit()
        print(f"   ✓ {sum([len(msgs) for msgs in messages_data])} mesaj eklendi\n")
        
        # 9. Fiyat listesi ekle
        print("9. Fiyat listesi ekleniyor...")
        
        price_items = [
            {
                'category': 'hair',
                'service_code': 'HAIR-FUE-3000',
                'service_name_tr': 'FUE Saç Ekimi (3000 Greft)',
                'service_name_en': 'FUE Hair Transplant (3000 Grafts)',
                'service_name_ar': 'زراعة الشعر FUE (3000 بصيلة)',
                'base_price': 2500,
                'currency': 'USD'
            },
            {
                'category': 'dental',
                'service_code': 'DENTAL-IMP-SINGLE',
                'service_name_tr': 'Tek Diş İmplant',
                'service_name_en': 'Single Dental Implant',
                'service_name_ar': 'زراعة سن واحد',
                'base_price': 800,
                'currency': 'USD'
            },
            {
                'category': 'eye',
                'service_code': 'EYE-LASIK-BOTH',
                'service_name_tr': 'LASIK (İki Göz)',
                'service_name_en': 'LASIK (Both Eyes)',
                'service_name_ar': 'عملية الليزك (كلتا العينين)',
                'base_price': 1800,
                'currency': 'USD'
            },
            {
                'category': 'aesthetic',
                'service_code': 'AEST-RHINO',
                'service_name_tr': 'Rinoplasti (Burun Estetiği)',
                'service_name_en': 'Rhinoplasty',
                'service_name_ar': 'عملية تجميل الأنف',
                'base_price': 3500,
                'currency': 'USD'
            },
            {
                'category': 'bariatric',
                'service_code': 'BARI-SLEEVE',
                'service_name_tr': 'Gastrik Sleeve',
                'service_name_en': 'Gastric Sleeve Surgery',
                'service_name_ar': 'عملية تكميم المعدة',
                'base_price': 4500,
                'currency': 'USD'
            }
        ]
        
        for item_data in price_items:
            item = PriceListItem(
                distributor_id=dist_id,
                is_active=True,
                is_featured=True,
                display_order=price_items.index(item_data),
                **item_data
            )
            db.session.add(item)
        
        db.session.commit()
        print(f"   ✓ {len(price_items)} fiyat listesi öğesi eklendi\n")
        
        print("=== ✅ TÜM ÖRNEK VERİLER BAŞARIYLA OLUŞTURULDU ===\n")
        print("📊 Özet:")
        print(f"   • {Lead.query.filter_by(distributor_id=dist_id).count()} Lead")
        print(f"   • {Patient.query.filter_by(distributor_id=dist_id).count()} Hasta")
        print(f"   • {Encounter.query.filter_by(distributor_id=dist_id).count()} Muayene")
        print(f"   • {PatientJourney.query.filter_by(distributor_id=dist_id).count()} Yolculuk Planı")
        print(f"   • {Flight.query.join(PatientJourney).filter(PatientJourney.distributor_id==dist_id).count()} Uçuş")
        print(f"   • {Transfer.query.join(PatientJourney).filter(PatientJourney.distributor_id==dist_id).count()} Transfer")
        print(f"   • {HotelReservation.query.filter_by(distributor_id=dist_id).count()} Otel Rezervasyonu")
        print(f"   • {Message.query.filter_by(distributor_id=dist_id).count()} Mesaj")
        print(f"   • {PriceListItem.query.filter_by(distributor_id=dist_id).count()} Fiyat Listesi Öğesi")

if __name__ == '__main__':
    create_sample_data()
