from app import db
from datetime import datetime

class HairAnnotation(db.Model):
    __tablename__ = 'hair_annotations'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    region_id = db.Column(db.String(20), nullable=False)  # e.g., "front", "crown", "vertex"
    label = db.Column(db.String(100))
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'region_id': self.region_id,
            'label': self.label,
            'note': self.note
        }

class HairPatternSelection(db.Model):
    __tablename__ = 'hair_pattern_selections'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    pattern_key = db.Column(db.String(20), nullable=False)  # e.g., "norwood_01" to "norwood_16"
    note = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'pattern_key': self.pattern_key,
            'note': self.note
        }