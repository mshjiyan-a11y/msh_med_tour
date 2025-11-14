from app import db
from datetime import datetime

class Lead(db.Model):
    """Lead/Form submissions from Facebook Ads or Website"""
    __tablename__ = 'leads'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    # Lead Source
    source = db.Column(db.String(50), nullable=False)  # 'facebook', 'website', 'instagram', 'manual'
    source_id = db.Column(db.String(255))  # Facebook Lead ID or form identifier
    campaign_name = db.Column(db.String(255))  # Facebook campaign/ad name
    
    # Contact Information
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    
    # Additional Info
    country = db.Column(db.String(100))
    city = db.Column(db.String(100))
    age = db.Column(db.Integer)
    
    # Interest (which service)
    interested_service = db.Column(db.String(50))  # 'hair', 'dental', 'eye', 'other'
    message = db.Column(db.Text)
    
    # Lead Status
    status = db.Column(db.String(20), default='new')  # 'new', 'contacted', 'qualified', 'converted', 'rejected'
    priority = db.Column(db.String(20), default='medium')  # 'low', 'medium', 'high', 'urgent'
    
    # Conversion
    converted_to_patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True)
    converted_at = db.Column(db.DateTime)
    
    # Assignment
    assigned_to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Metadata
    raw_data = db.Column(db.Text)  # Store original JSON from Facebook/form
    ip_address = db.Column(db.String(50))
    user_agent = db.Column(db.String(255))
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    distributor = db.relationship('Distributor', backref='leads')
    converted_patient = db.relationship('Patient', backref='source_lead', foreign_keys=[converted_to_patient_id])
    assigned_user = db.relationship('User', backref='assigned_leads', foreign_keys=[assigned_to_user_id])
    notes = db.relationship('LeadNote', backref='lead', lazy='dynamic', cascade='all, delete-orphan')
    
    @property
    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}".strip()
        return self.first_name or self.last_name or 'İsimsiz Lead'
    
    @property
    def is_converted(self):
        return self.status == 'converted' and self.converted_to_patient_id is not None
    
    def __repr__(self):
        return f'<Lead {self.id} - {self.full_name} from {self.source}>'


class LeadNote(db.Model):
    """Notes/comments on leads"""
    __tablename__ = 'lead_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    lead_id = db.Column(db.Integer, db.ForeignKey('leads.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    note = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    user = db.relationship('User', backref='lead_notes')
    
    def __repr__(self):
        return f'<LeadNote {self.id} for Lead {self.lead_id}>'


class APIKey(db.Model):
    """API Keys for each distributor"""
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False)
    
    key_name = db.Column(db.String(100), nullable=False)  # 'Website Form', 'Facebook Integration', etc.
    api_key = db.Column(db.String(64), unique=True, nullable=False)  # Generated token
    
    # Permissions
    can_create_leads = db.Column(db.Boolean, default=True)
    can_read_leads = db.Column(db.Boolean, default=False)
    allowed_sources = db.Column(db.String(255))  # Comma-separated: 'facebook,website,instagram'
    
    # Usage tracking
    last_used_at = db.Column(db.DateTime)
    usage_count = db.Column(db.Integer, default=0)
    
    # Status
    is_active = db.Column(db.Boolean, default=True)
    expires_at = db.Column(db.DateTime)  # Optional expiration
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Relationships
    distributor = db.relationship('Distributor', backref='api_keys')
    creator = db.relationship('User', backref='created_api_keys', foreign_keys=[created_by])
    
    def __repr__(self):
        return f'<APIKey {self.key_name} for {self.distributor.name}>'
