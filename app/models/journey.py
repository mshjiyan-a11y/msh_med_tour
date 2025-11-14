from app import db
from datetime import datetime


class PatientJourney(db.Model):
    """Hasta tedavi yolculuğu - geliş/dönüş arası tüm süreç koordinasyonu"""
    __tablename__ = 'patient_journeys'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True, index=True)
    coordinator_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # sorumlu personel
    
    # Yolculuk bilgileri
    journey_code = db.Column(db.String(50), unique=True, nullable=False, index=True)  # örn: TRV-2025-001
    journey_type = db.Column(db.String(50), default='medical_tourism')  # medical_tourism, follow_up, emergency
    
    # Tarihler
    arrival_date = db.Column(db.DateTime, nullable=False, index=True)
    departure_date = db.Column(db.DateTime, nullable=False, index=True)
    actual_arrival = db.Column(db.DateTime, nullable=True)  # gerçekleşen varış
    actual_departure = db.Column(db.DateTime, nullable=True)  # gerçekleşen ayrılış
    
    # Durum
    status = db.Column(db.String(30), default='planned', index=True)
    # planned, confirmed, in_progress, completed, cancelled
    
    # Detaylar
    purpose = db.Column(db.Text, nullable=True)  # tedavi amacı açıklama
    special_requirements = db.Column(db.Text, nullable=True)  # özel ihtiyaçlar (diyabet, tekerlekli sandalye vb)
    emergency_contact = db.Column(db.String(200), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Maliyet özeti
    estimated_cost = db.Column(db.Float, default=0)
    actual_cost = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    distributor = db.relationship('Distributor', backref='patient_journeys')
    patient = db.relationship('Patient', backref='journeys')
    encounter = db.relationship('Encounter', backref='journey')
    coordinator = db.relationship('User', foreign_keys=[coordinator_id], backref='coordinated_journeys')
    creator = db.relationship('User', foreign_keys=[created_by])
    steps = db.relationship('JourneyStep', backref='journey', lazy='dynamic', 
                           order_by='JourneyStep.sequence, JourneyStep.scheduled_date', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<PatientJourney {self.journey_code}>'
    
    def duration_days(self):
        """Toplam yolculuk süresi (gün)"""
        if self.arrival_date and self.departure_date:
            return (self.departure_date - self.arrival_date).days
        return 0
    
    def is_active(self):
        """Şu anda aktif mi (yolculuk devam ediyor mu)"""
        now = datetime.utcnow()
        return self.status == 'in_progress' and self.arrival_date <= now <= self.departure_date
    
    def progress_percentage(self):
        """Tamamlanma yüzdesi (adımlara göre)"""
        total = self.steps.count()
        if total == 0:
            return 0
        completed = self.steps.filter_by(status='completed').count()
        return int((completed / total) * 100)
    
    def get_current_step(self):
        """Şu anki aktif adımı getir"""
        return self.steps.filter_by(status='in_progress').first()
    
    def get_next_step(self):
        """Sıradaki adımı getir"""
        return self.steps.filter_by(status='pending').order_by('scheduled_date').first()


class JourneyStep(db.Model):
    """Yolculuk adımları - her bir aktivite/görev"""
    __tablename__ = 'journey_steps'
    
    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=False, index=True)
    # Drag-drop sıralama için
    sequence = db.Column(db.Integer, nullable=True, index=True)
    
    # Adım bilgileri
    step_type = db.Column(db.String(50), nullable=False, index=True)
    # flight_arrival, airport_pickup, hotel_checkin, hospital_visit, treatment, 
    # lab_test, followup_checkup, hotel_checkout, airport_dropoff, flight_departure
    
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # Zaman
    scheduled_date = db.Column(db.DateTime, nullable=False, index=True)
    scheduled_end = db.Column(db.DateTime, nullable=True)
    actual_start = db.Column(db.DateTime, nullable=True)
    actual_end = db.Column(db.DateTime, nullable=True)
    duration_minutes = db.Column(db.Integer, nullable=True)
    
    # Durum
    status = db.Column(db.String(30), default='pending', index=True)
    # pending, confirmed, in_progress, completed, cancelled, delayed
    
    # İlişkiler (opsiyonel)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=True)
    hotel_reservation_id = db.Column(db.Integer, db.ForeignKey('hotel_reservations.id'), nullable=True)
    
    # Lokasyon ve iletişim
    location = db.Column(db.String(300), nullable=True)  # adres veya tesis adı
    contact_person = db.Column(db.String(100), nullable=True)
    contact_phone = db.Column(db.String(30), nullable=True)
    
    # Notlar ve uyarılar
    notes = db.Column(db.Text, nullable=True)
    alert_message = db.Column(db.String(500), nullable=True)  # uyarı/hatırlatma mesajı
    is_critical = db.Column(db.Boolean, default=False)  # kritik adım işareti
    
    # Maliyet
    cost = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Relationships
    appointment = db.relationship('Appointment', backref='journey_step')
    hotel_reservation = db.relationship('HotelReservation', backref='journey_step')
    completer = db.relationship('User', foreign_keys=[completed_by])
    
    def __repr__(self):
        return f'<JourneyStep {self.title}>'
    
    def is_overdue(self):
        """Geçmiş/gecikmiş mi"""
        if self.status in ['completed', 'cancelled']:
            return False
        return self.scheduled_date < datetime.utcnow()
    
    def mark_completed(self, user_id=None):
        """Adımı tamamlandı olarak işaretle"""
        self.status = 'completed'
        self.actual_end = datetime.utcnow()
        if user_id:
            self.completed_by = user_id


class Flight(db.Model):
    """Uçuş bilgileri"""
    __tablename__ = 'flights'
    
    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=False, index=True)
    journey_step_id = db.Column(db.Integer, db.ForeignKey('journey_steps.id'), nullable=True)
    
    # Uçuş tipi
    flight_type = db.Column(db.String(20), nullable=False)  # arrival, departure
    
    # Uçuş detayları
    airline = db.Column(db.String(100), nullable=True)
    flight_number = db.Column(db.String(50), nullable=True)
    booking_reference = db.Column(db.String(50), nullable=True)
    
    # Güzergah
    departure_airport = db.Column(db.String(100), nullable=True)  # havalimanı adı veya kodu
    arrival_airport = db.Column(db.String(100), nullable=True)
    departure_city = db.Column(db.String(100), nullable=True)
    arrival_city = db.Column(db.String(100), nullable=True)
    
    # Zaman
    scheduled_departure = db.Column(db.DateTime, nullable=False)
    scheduled_arrival = db.Column(db.DateTime, nullable=False)
    actual_departure = db.Column(db.DateTime, nullable=True)
    actual_arrival = db.Column(db.DateTime, nullable=True)
    
    # Durum
    status = db.Column(db.String(30), default='scheduled')
    # scheduled, boarding, in_flight, landed, delayed, cancelled
    
    # Yolcu bilgileri
    passenger_count = db.Column(db.Integer, default=1)
    seat_numbers = db.Column(db.String(100), nullable=True)  # virgülle ayrılmış
    baggage_info = db.Column(db.String(200), nullable=True)
    
    # Ek bilgiler
    terminal = db.Column(db.String(20), nullable=True)
    gate = db.Column(db.String(20), nullable=True)
    notes = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    journey = db.relationship('PatientJourney', backref='flights')
    step = db.relationship('JourneyStep', backref='flight')
    
    def __repr__(self):
        return f'<Flight {self.flight_number or "N/A"} {self.departure_airport}->{self.arrival_airport}>'


class Transfer(db.Model):
    """Transfer/Ulaşım hizmetleri"""
    __tablename__ = 'transfers'
    
    id = db.Column(db.Integer, primary_key=True)
    journey_id = db.Column(db.Integer, db.ForeignKey('patient_journeys.id'), nullable=False, index=True)
    journey_step_id = db.Column(db.Integer, db.ForeignKey('journey_steps.id'), nullable=True)
    
    # Transfer tipi
    transfer_type = db.Column(db.String(50), nullable=False)
    # airport_pickup, airport_dropoff, hospital_transfer, hotel_to_hospital, 
    # city_tour, custom
    
    # Lokasyon
    pickup_location = db.Column(db.String(300), nullable=False)
    pickup_address = db.Column(db.Text, nullable=True)
    dropoff_location = db.Column(db.String(300), nullable=False)
    dropoff_address = db.Column(db.Text, nullable=True)
    
    # Zaman
    scheduled_pickup = db.Column(db.DateTime, nullable=False, index=True)
    actual_pickup = db.Column(db.DateTime, nullable=True)
    estimated_duration = db.Column(db.Integer, nullable=True)  # dakika
    actual_duration = db.Column(db.Integer, nullable=True)
    
    # Araç ve sürücü
    vehicle_type = db.Column(db.String(50), nullable=True)  # sedan, van, minibus, wheelchair_accessible
    vehicle_plate = db.Column(db.String(30), nullable=True)
    driver_name = db.Column(db.String(100), nullable=True)
    driver_phone = db.Column(db.String(30), nullable=True)
    
    # Yolcu bilgileri
    passenger_count = db.Column(db.Integer, default=1)
    has_luggage = db.Column(db.Boolean, default=True)
    wheelchair_required = db.Column(db.Boolean, default=False)
    
    # Durum
    status = db.Column(db.String(30), default='scheduled', index=True)
    # scheduled, driver_assigned, en_route_pickup, passenger_picked_up, 
    # en_route_destination, completed, cancelled
    
    # Maliyet
    cost = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    
    # Ek bilgiler
    notes = db.Column(db.Text, nullable=True)
    special_instructions = db.Column(db.Text, nullable=True)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    journey = db.relationship('PatientJourney', backref='transfers')
    step = db.relationship('JourneyStep', backref='transfer')
    
    def __repr__(self):
        return f'<Transfer {self.transfer_type}: {self.pickup_location}->{self.dropoff_location}>'
