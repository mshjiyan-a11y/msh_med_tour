from app import db
from datetime import datetime

class EyeRefraction(db.Model):
    __tablename__ = 'eye_refractions'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    
    # Right eye (OD)
    od_sph = db.Column(db.Float)
    od_cyl = db.Column(db.Float)
    od_ax = db.Column(db.Float)
    
    # Left eye (OS)
    os_sph = db.Column(db.Float)
    os_cyl = db.Column(db.Float)
    os_ax = db.Column(db.Float)
    
    planned_procedure = db.Column(db.String(100))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'od_sph': self.od_sph,
            'od_cyl': self.od_cyl,
            'od_ax': self.od_ax,
            'os_sph': self.os_sph,
            'os_cyl': self.os_cyl,
            'os_ax': self.os_ax,
            'planned_procedure': self.planned_procedure,
            'note': self.note
        }

class EyeTreatmentSelection(db.Model):
    __tablename__ = 'eye_treatment_selections'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    side = db.Column(db.String(2))  # OD, OS, OU
    price = db.Column(db.Float)
    currency = db.Column(db.String(3), default='EUR')  # EUR, USD, TRY, GBP
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'code': self.code,
            'title': self.title,
            'side': self.side,
            'price': self.price,
            'note': self.note
        }