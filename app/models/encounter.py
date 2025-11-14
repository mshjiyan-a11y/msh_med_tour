from app import db
from datetime import datetime
import uuid

class Encounter(db.Model):
    __tablename__ = 'encounters'

    id = db.Column(db.Integer, primary_key=True)
    uuid = db.Column(db.String(36), unique=True, default=lambda: str(uuid.uuid4()))
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    date = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    appointment_time = db.Column(db.String(5))  # Format: HH:MM (09:00, 14:30, etc.)
    note = db.Column(db.Text)
    
    # PDF related fields
    pdf_path = db.Column(db.String(255))
    pdf_generated_at = db.Column(db.DateTime)
    pdf_language = db.Column(db.String(2), default='tr')  # tr or en
    
    # Status and tracking
    status = db.Column(db.String(20), default='draft')  # draft, final, approved
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Pricing validity, payment, exchange rate, personalized greeting
    valid_until = db.Column(db.Date)  # Quote/price validity date
    payment_plan = db.Column(db.String(100))  # e.g., "50% deposit, 50% on arrival"
    exchange_rate = db.Column(db.String(50))  # e.g., "1 EUR = 32.50 TRY"
    greeting_message = db.Column(db.Text)  # Custom greeting for this encounter PDF
    
    # Relationships
    hair_annotations = db.relationship('HairAnnotation', backref='encounter', lazy=True)
    hair_patterns = db.relationship('HairPatternSelection', backref='encounter', lazy=True)
    dental_procedures = db.relationship('DentalProcedure', backref='encounter', lazy=True)
    eye_refraction = db.relationship('EyeRefraction', backref='encounter', lazy=True, uselist=False)
    eye_treatments = db.relationship('EyeTreatmentSelection', backref='encounter', lazy=True)
    aesthetic_procedure = db.relationship('AestheticProcedure', backref='encounter', lazy=True, uselist=False)
    bariatric_surgery = db.relationship('BariatricSurgery', backref='encounter', lazy=True, uselist=False)
    ivf_treatment = db.relationship('IVFTreatment', backref='encounter', lazy=True, uselist=False)
    checkup_package = db.relationship('CheckUpPackage', backref='encounter', lazy=True, uselist=False)
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_encounters')

    def __repr__(self):
        return f'<Encounter {self.id} - Patient {self.patient_id}>'

    def to_dict(self):
        return {
            'id': self.id,
            'uuid': self.uuid,
            'distributor_id': self.distributor_id,
            'patient_id': self.patient_id,
            'date': self.date.strftime('%Y-%m-%d %H:%M:%S'),
            'note': self.note,
            'status': self.status,
            'pdf_path': self.pdf_path,
            'pdf_generated_at': self.pdf_generated_at.strftime('%Y-%m-%d %H:%M:%S') if self.pdf_generated_at else None,
            'pdf_language': self.pdf_language,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }