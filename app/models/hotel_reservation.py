"""
Hotel Reservation Model
Tracks hotel bookings and transfers for medical tourism patients
"""
from app import db
from datetime import datetime, timedelta

class HotelReservation(db.Model):
    __tablename__ = 'hotel_reservations'
    
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Hotel Information
    hotel_name = db.Column(db.String(200), nullable=False)
    hotel_address = db.Column(db.Text)
    hotel_phone = db.Column(db.String(20))
    hotel_stars = db.Column(db.Integer)  # 1-5 stars
    room_type = db.Column(db.String(100))  # Single, Double, Suite, etc.
    
    # Booking Dates
    check_in = db.Column(db.Date, nullable=False)
    check_out = db.Column(db.Date, nullable=False)
    nights = db.Column(db.Integer)  # Auto-calculated
    
    # Pricing
    price_per_night = db.Column(db.Float, default=0)
    total_hotel_cost = db.Column(db.Float, default=0)  # Auto-calculated
    currency = db.Column(db.String(3), default='EUR')  # EUR, USD, TRY, GBP
    
    # Transfer Information
    transfer_included = db.Column(db.Boolean, default=False)
    transfer_type = db.Column(db.String(50))  # Airport pickup, Round trip, One way
    transfer_cost = db.Column(db.Float, default=0)
    
    # Airport Information
    airport_code = db.Column(db.String(10))  # IST, SAW, AYT, etc.
    airport_name = db.Column(db.String(200))
    flight_number = db.Column(db.String(50))
    arrival_time = db.Column(db.DateTime)
    departure_time = db.Column(db.DateTime)
    
    # Additional Services
    breakfast_included = db.Column(db.Boolean, default=True)
    wifi_included = db.Column(db.Boolean, default=True)
    
    # Status
    status = db.Column(db.String(20), default='pending')  # pending, confirmed, cancelled
    confirmation_number = db.Column(db.String(50))
    
    # Notes
    notes = db.Column(db.Text)
    special_requests = db.Column(db.Text)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    patient = db.relationship('Patient', backref='hotel_reservations')
    distributor = db.relationship('Distributor', backref='hotel_reservations')
    
    def __init__(self, **kwargs):
        super(HotelReservation, self).__init__(**kwargs)
        self.calculate_fields()
    
    def calculate_fields(self):
        """Auto-calculate nights and total cost"""
        if self.check_in and self.check_out:
            delta = self.check_out - self.check_in
            self.nights = delta.days
            
            if self.price_per_night:
                self.total_hotel_cost = self.price_per_night * self.nights
    
    @property
    def total_cost(self):
        """Total cost including hotel + transfer"""
        return (self.total_hotel_cost or 0) + (self.transfer_cost or 0)
    
    @property
    def status_badge_class(self):
        """Bootstrap badge class for status"""
        badges = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger'
        }
        return badges.get(self.status, 'secondary')
    
    @property
    def is_past(self):
        """Check if checkout date has passed"""
        return self.check_out < datetime.utcnow().date()
    
    @property
    def is_upcoming(self):
        """Check if checkin is in the future"""
        return self.check_in > datetime.utcnow().date()
    
    def __repr__(self):
        return f'<HotelReservation {self.hotel_name} - {self.patient.full_name}>'
