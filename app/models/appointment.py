from app import db
from datetime import datetime


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True, index=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    appointment_type = db.Column(db.String(50), default='consultation')  # consultation, surgery, checkup, followup
    
    start_time = db.Column(db.DateTime, nullable=False, index=True)
    end_time = db.Column(db.DateTime, nullable=False, index=True)
    
    status = db.Column(db.String(20), default='scheduled', index=True)  # scheduled, confirmed, completed, cancelled, no_show
    
    # Optional: provider/resource
    doctor_name = db.Column(db.String(100), nullable=True)
    room_number = db.Column(db.String(50), nullable=True)
    
    # Reminder tracking
    reminder_sent_at = db.Column(db.DateTime, nullable=True)
    reminder_method = db.Column(db.String(20), nullable=True)  # email, sms, whatsapp, in_app
    
    notes = db.Column(db.Text, nullable=True)
    cancellation_reason = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    distributor = db.relationship('Distributor', backref='appointments')
    patient = db.relationship('Patient', backref='appointments')
    encounter = db.relationship('Encounter', backref='appointments')
    creator = db.relationship('User', foreign_keys=[created_by])

    def duration_minutes(self):
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return int(delta.total_seconds() / 60)
        return 0

    def is_past(self):
        return self.start_time < datetime.utcnow()

    def __repr__(self):
        return f'<Appointment {self.id}: {self.title} at {self.start_time}>'
