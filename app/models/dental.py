from app import db
from datetime import datetime

class DentalProcedure(db.Model):
    __tablename__ = 'dental_procedures'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    tooth_no = db.Column(db.Integer, nullable=False)  # 1-32
    treatment_type = db.Column(db.String(50), nullable=False)
    note = db.Column(db.Text)
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')  # EUR, USD, TRY, GBP
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<DentalProcedure {self.id} - Tooth {self.tooth_no}>'

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'tooth_no': self.tooth_no,
            'treatment_type': self.treatment_type,
            'note': self.note,
            'price': self.price,
            'discount_enabled': self.discount_enabled,
            'discounted_price': self.discounted_price,
            'final_price': self.discounted_price if self.discount_enabled and self.discounted_price else self.price
        }