from app import db
from datetime import datetime

class MetaAPIConfig(db.Model):
    """Meta/Facebook API configuration for distributors"""
    __tablename__ = 'meta_api_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, unique=True)
    
    # Meta API credentials
    page_id = db.Column(db.String(255))  # Facebook Page ID
    form_id = db.Column(db.String(255))  # Lead Form ID
    access_token = db.Column(db.String(500))  # Meta access token (should be encrypted in production)
    api_version = db.Column(db.String(20), default='v18.0')  # Meta API version
    
    # Configuration
    is_active = db.Column(db.Boolean, default=False)
    fetch_interval_minutes = db.Column(db.Integer, default=5)  # Fetch leads every N minutes
    last_fetch_time = db.Column(db.DateTime)
    last_error = db.Column(db.Text)
    
    # Tracking
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship
    distributor = db.relationship('Distributor', backref='meta_api_config')
    
    def __repr__(self):
        return f'<MetaAPIConfig {self.id} - Distributor {self.distributor_id}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'distributor_id': self.distributor_id,
            'page_id': self.page_id,
            'form_id': self.form_id,
            'is_active': self.is_active,
            'fetch_interval_minutes': self.fetch_interval_minutes,
            'last_fetch_time': self.last_fetch_time.isoformat() if self.last_fetch_time else None,
            'last_error': self.last_error,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class FacebookLead(db.Model):
    """Facebook leads fetched from Meta"""
    __tablename__ = 'facebook_leads'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    meta_lead_id = db.Column(db.String(255), unique=True)  # Facebook lead ID
    
    # Lead information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    
    # Form data (JSON)
    form_data = db.Column(db.JSON)  # Custom form fields
    
    # Status tracking
    status = db.Column(db.String(50), default='new')  # new, assigned, contacted, converted, rejected
    notes = db.Column(db.Text)
    assigned_to_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Assigned staff
    
    # Timestamps
    lead_created_at = db.Column(db.DateTime)  # When lead was created on Facebook
    created_at = db.Column(db.DateTime, default=datetime.utcnow)  # When we fetched it
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    distributor = db.relationship('Distributor', backref='facebook_leads')
    assigned_to = db.relationship('User', foreign_keys=[assigned_to_id], backref='facebook_lead_assignments')
    
    def __repr__(self):
        return f'<FacebookLead {self.id} - {self.first_name} {self.last_name}>'
    
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()
    
    def to_dict(self):
        return {
            'id': self.id,
            'meta_lead_id': self.meta_lead_id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'email': self.email,
            'phone': self.phone,
            'full_name': self.full_name(),
            'form_data': self.form_data,
            'status': self.status,
            'notes': self.notes,
            'assigned_to': self.assigned_to.username if self.assigned_to else None,
            'lead_created_at': self.lead_created_at.isoformat() if self.lead_created_at else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }


class LeadInteraction(db.Model):
    """Track interactions with leads"""
    __tablename__ = 'lead_interactions'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('facebook_leads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Interaction type
    interaction_type = db.Column(db.String(50))  # called, emailed, sms, note, status_changed
    description = db.Column(db.Text)
    
    # Result
    result = db.Column(db.String(100))  # success, failed, no_answer, etc.
    
    # Timestamp
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    lead = db.relationship('FacebookLead', backref='interactions')
    user = db.relationship('User', backref='lead_interactions')
    
    def __repr__(self):
        return f'<LeadInteraction {self.id} - Lead {self.lead_id} - {self.interaction_type}>'
