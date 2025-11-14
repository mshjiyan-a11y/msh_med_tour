from app import db
from datetime import datetime

class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    dob = db.Column(db.Date)
    gender = db.Column(db.String(1))  # 'M' or 'F'
    notes = db.Column(db.Text)
    
    # Passport or ID information
    id_number = db.Column(db.String(20))
    nationality = db.Column(db.String(50))
    passport_number = db.Column(db.String(20))
    
    # Additional fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    encounters = db.relationship('Encounter', backref='patient', lazy=True)

    @property
    def full_name(self):
        """Backward compatibility property"""
        return f"{self.first_name} {self.last_name}".strip()

    def __repr__(self):
        return f'<Patient {self.full_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'full_name': self.full_name,
            'phone': self.phone,
            'email': self.email,
            'dob': self.dob.strftime('%Y-%m-%d') if self.dob else None,
            'gender': self.gender,
            'notes': self.notes,
            'id_number': self.id_number,
            'nationality': self.nationality,
            'passport_number': self.passport_number,
            'is_active': self.is_active
        }