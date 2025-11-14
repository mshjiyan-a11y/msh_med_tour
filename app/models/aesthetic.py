from app import db
from datetime import datetime

class AestheticProcedure(db.Model):
    __tablename__ = 'aesthetic_procedures'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    
    # Procedure type
    procedure_type = db.Column(db.String(50), nullable=False)  # rhinoplasty, breast_augmentation, liposuction, face_lift, etc.
    procedure_name = db.Column(db.String(100))  # Turkish name
    
    # Body measurements (optional, depends on procedure)
    body_area = db.Column(db.String(50))  # nose, breast, abdomen, face, etc.
    measurements = db.Column(db.Text)  # JSON: {"width": "5cm", "height": "3cm", etc.}
    
    # Procedure details
    technique = db.Column(db.String(100))  # Open/Closed rhinoplasty, Silicone/Saline implant, etc.
    implant_size = db.Column(db.String(50))  # For breast: 300cc, 350cc, etc.
    anesthesia_type = db.Column(db.String(50))  # Local, General, Sedation
    
    # Pricing
    price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')  # EUR, USD, TRY
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    
    # Photos
    before_photo_path = db.Column(db.String(255))
    after_photo_path = db.Column(db.String(255))
    
    # Additional notes
    notes = db.Column(db.Text)
    risks_explained = db.Column(db.Boolean, default=False)
    consent_signed = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<AestheticProcedure {self.procedure_type}>'
