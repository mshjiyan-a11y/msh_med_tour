from app import db
from datetime import datetime

class Distributor(db.Model):
    __tablename__ = 'distributors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    contact_name = db.Column(db.String(100))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120), unique=True, nullable=False)
    address = db.Column(db.Text)
    logo_path = db.Column(db.String(255))
    color_hex = db.Column(db.String(7), default='#7a001d')
    pdf_footer_text = db.Column(db.Text)
    
    # Contact and Social Media
    website = db.Column(db.String(255))
    facebook = db.Column(db.String(255))
    instagram = db.Column(db.String(255))
    twitter = db.Column(db.String(255))
    linkedin = db.Column(db.String(255))
    whatsapp = db.Column(db.String(20))
    
    # Additional PDF Info
    hospital_license = db.Column(db.String(100))
    tax_number = db.Column(db.String(50))
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    
    # Lead Integration Settings (Only Admin can edit)
    facebook_page_id = db.Column(db.String(100))  # Facebook Page ID for Lead Ads
    facebook_access_token = db.Column(db.String(500))  # Long-lived Page Access Token
    website_api_key = db.Column(db.String(64))  # API key for website forms
    webhook_secret = db.Column(db.String(100))  # Secret for webhook verification
    
    # Module enablement flags
    enable_hair = db.Column(db.Boolean, default=False)
    enable_teeth = db.Column(db.Boolean, default=False)
    enable_eye = db.Column(db.Boolean, default=False)
    enable_aesthetic = db.Column(db.Boolean, default=False)
    enable_bariatric = db.Column(db.Boolean, default=False)
    enable_ivf = db.Column(db.Boolean, default=False)
    enable_checkup = db.Column(db.Boolean, default=False)
    
    # Pricing Configuration
    price_per_graft = db.Column(db.Float, default=0)  # Hair transplant price per graft
    currency = db.Column(db.String(10), default='EUR')  # EUR, USD, TRY, GBP, etc.
    default_currency = db.Column(db.String(3), default='EUR')  # Default currency for all prices
    
    # Multi-language and personalization
    greeting_message = db.Column(db.Text)  # Custom greeting for PDFs
    brand_font = db.Column(db.String(50))  # Custom font for PDFs (e.g., 'Arial', 'DejaVu')
    pdf_language = db.Column(db.String(2), default='tr')  # tr, en, de
    currency_format_locale = db.Column(db.String(10), default='tr_TR')  # e.g., 'tr_TR', 'en_US', 'de_DE'
    
    # Additional fields
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    # Relationships
    users = db.relationship('User', backref='distributor', lazy=True)
    patients = db.relationship('Patient', backref='distributor', lazy=True)
    encounters = db.relationship('Encounter', backref='distributor', lazy=True)

    def __repr__(self):
        return f'<Distributor {self.name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'contact_name': self.contact_name,
            'phone': self.phone,
            'email': self.email,
            'address': self.address,
            'logo_path': self.logo_path,
            'color_hex': self.color_hex,
            'enable_hair': self.enable_hair,
            'enable_teeth': self.enable_teeth,
            'enable_eye': self.enable_eye,
            'enable_aesthetic': self.enable_aesthetic,
            'enable_bariatric': self.enable_bariatric,
            'enable_ivf': self.enable_ivf,
            'enable_checkup': self.enable_checkup,
            'is_active': self.is_active
        }