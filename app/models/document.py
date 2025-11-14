from app import db
from datetime import datetime
import os


class Document(db.Model):
    __tablename__ = 'documents'

    id = db.Column(db.Integer, primary_key=True)
    distributor_id = db.Column(db.Integer, db.ForeignKey('distributors.id'), nullable=False, index=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=True, index=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=True, index=True)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=True)
    
    # File info
    filename = db.Column(db.String(255), nullable=False)  # original filename
    stored_filename = db.Column(db.String(255), nullable=False)  # unique stored name
    file_path = db.Column(db.String(500), nullable=False)  # relative path
    file_size = db.Column(db.Integer, nullable=True)  # bytes
    mime_type = db.Column(db.String(100), nullable=True)
    
    # Classification
    document_type = db.Column(db.String(50), default='other', index=True)  # medical_report, lab_result, consent_form, image, other
    tags = db.Column(db.String(500), nullable=True)  # comma-separated
    
    # Access control
    is_public = db.Column(db.Boolean, default=False)  # visible to patient
    is_archived = db.Column(db.Boolean, default=False, index=True)
    
    # Metadata
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    archived_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    distributor = db.relationship('Distributor', backref='documents')
    # Use unique backref names to avoid collision with existing patient document relationship
    patient = db.relationship('Patient', backref='uploaded_documents')
    encounter = db.relationship('Encounter', backref='encounter_documents')
    uploader = db.relationship('User', foreign_keys=[uploaded_by])

    def get_extension(self):
        return os.path.splitext(self.filename)[1].lower()

    def is_image(self):
        return self.get_extension() in ['.jpg', '.jpeg', '.png', '.gif', '.bmp']

    def is_pdf(self):
        return self.get_extension() == '.pdf'

    def size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0

    def __repr__(self):
        return f'<Document {self.id}: {self.title}>'
