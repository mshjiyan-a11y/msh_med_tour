from app import db
from datetime import datetime


class Notification(db.Model):
    __tablename__ = 'notifications'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), index=True, nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True, nullable=True)  # hedef kullanıcı (opsiyonel, None => tüm adminler)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=True)
    level = db.Column(db.String(20), default='info')  # info, success, warning, danger
    ntype = db.Column(db.String(50), default='general')  # general, lead, encounter, approval, system
    link_url = db.Column(db.String(500), nullable=True)

    channel = db.Column(db.String(20), default='in_app')  # in_app, email, both
    scheduled_for = db.Column(db.DateTime, nullable=True)
    sent_at = db.Column(db.DateTime, nullable=True)

    is_read = db.Column(db.Boolean, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    meta_json = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    def mark_read(self):
        if not self.is_read:
            self.is_read = True
            self.read_at = datetime.utcnow()
