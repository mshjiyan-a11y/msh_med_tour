from app import db
from datetime import datetime

class BariatricSurgery(db.Model):
    __tablename__ = 'bariatric_surgeries'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    
    # Surgery type
    surgery_type = db.Column(db.String(50), nullable=False)  # gastric_bypass, sleeve, gastric_balloon, gastric_band
    surgery_name = db.Column(db.String(100))  # Turkish name
    
    # Patient measurements
    weight_kg = db.Column(db.Float)  # Current weight in kg
    height_cm = db.Column(db.Float)  # Height in cm
    bmi = db.Column(db.Float)  # Body Mass Index (calculated)
    target_weight_kg = db.Column(db.Float)  # Target weight
    
    # Medical history
    diabetes = db.Column(db.Boolean, default=False)
    hypertension = db.Column(db.Boolean, default=False)
    sleep_apnea = db.Column(db.Boolean, default=False)
    previous_surgeries = db.Column(db.Text)
    medications = db.Column(db.Text)
    
    # Surgery details
    technique = db.Column(db.String(100))  # Laparoscopic, Robotic, Open
    expected_weight_loss = db.Column(db.String(50))  # "30-40 kg in 12 months"
    hospital_stay_days = db.Column(db.Integer, default=3)
    
    # Pricing
    price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    package_includes = db.Column(db.Text)  # Hotel, transfers, tests, etc.
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    
    # Follow-up
    diet_plan_provided = db.Column(db.Boolean, default=False)
    follow_up_schedule = db.Column(db.Text)  # "1 week, 1 month, 3 months, 6 months"
    
    # Consent
    risks_explained = db.Column(db.Boolean, default=False)
    consent_signed = db.Column(db.Boolean, default=False)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def calculate_bmi(self):
        """Calculate BMI from weight and height"""
        if self.weight_kg and self.height_cm:
            height_m = self.height_cm / 100
            self.bmi = round(self.weight_kg / (height_m ** 2), 1)
        return self.bmi
    
    def __repr__(self):
        return f'<BariatricSurgery {self.surgery_type} BMI:{self.bmi}>'
