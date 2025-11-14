from app import db
from datetime import datetime

class AppSettings(db.Model):
    __tablename__ = 'app_settings'

    id = db.Column(db.Integer, primary_key=True)
    # Global feature toggles
    enable_hair = db.Column(db.Boolean, default=True)
    enable_teeth = db.Column(db.Boolean, default=True)
    enable_eye = db.Column(db.Boolean, default=True)
    enable_hotel = db.Column(db.Boolean, default=True)
    enable_leads = db.Column(db.Boolean, default=True)
    enable_aesthetic = db.Column(db.Boolean, default=True)
    enable_bariatric = db.Column(db.Boolean, default=True)
    enable_ivf = db.Column(db.Boolean, default=True)
    enable_checkup = db.Column(db.Boolean, default=True)

    # Logo path
    logo_path = db.Column(db.String(255), nullable=True)

    # Theming (optional future use)
    theme_color = db.Column(db.String(7), default='#7a001d')
    navbar_style = db.Column(db.String(20), default='glass')
    
    # Backup & technical infrastructure
    backup_enabled = db.Column(db.Boolean, default=True)
    backup_schedule = db.Column(db.String(50), default='daily')  # daily, weekly, monthly
    api_enabled = db.Column(db.Boolean, default=True)
    performance_mode = db.Column(db.String(20), default='standard')  # standard, optimized, minimal

    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def get(cls):
        inst = cls.query.first()
        if not inst:
            inst = cls()
            db.session.add(inst)
            db.session.commit()
        return inst
