from app import db
from datetime import datetime

class AuditLog(db.Model):
    __tablename__ = 'audit_logs'

    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    action = db.Column(db.String(20), nullable=False)  # create, update, delete
    entity_type = db.Column(db.String(50), nullable=False)  # encounter, dental_procedure, etc.
    entity_id = db.Column(db.String(64))  # could store id or uuid
    field = db.Column(db.String(100))  # which field changed (optional for create/delete)
    old_value = db.Column(db.Text)
    new_value = db.Column(db.Text)
    note = db.Column(db.Text)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id])
    # encounter, distributor backrefs are optional; access via queries

    def to_dict(self):
        return {
            'id': self.id,
            'encounter_id': self.encounter_id,
            'distributor_id': self.distributor_id,
            'user_id': self.user_id,
            'action': self.action,
            'entity_type': self.entity_type,
            'entity_id': self.entity_id,
            'field': self.field,
            'old_value': self.old_value,
            'new_value': self.new_value,
            'note': self.note,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M:%S')
        }

    def __repr__(self):
        return f'<AuditLog {self.id} {self.action} {self.entity_type}:{self.entity_id}>'