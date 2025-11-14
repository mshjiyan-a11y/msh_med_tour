"""Approval model for quote approval flow"""
from app import db
from datetime import datetime

class QuoteApproval(db.Model):
    __tablename__ = 'quote_approvals'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False, unique=True)
    token = db.Column(db.String(64), unique=True, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected
    approved_at = db.Column(db.DateTime)
    approved_by_name = db.Column(db.String(100))
    approved_by_email = db.Column(db.String(120))
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    encounter = db.relationship('Encounter', backref='approval', uselist=False)
    
    def __repr__(self):
        return f'<QuoteApproval {self.id} for Encounter {self.encounter_id} - {self.status}>'
