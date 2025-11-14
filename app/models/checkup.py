from app import db
from datetime import datetime

class CheckUpPackage(db.Model):
    __tablename__ = 'checkup_packages'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    
    # Package type
    package_type = db.Column(db.String(50), nullable=False)  # basic, standard, premium, vip, custom
    package_name = db.Column(db.String(100))  # "Bronze Check-Up", "Executive Health Screening", etc.
    
    # Tests included (stored as JSON or comma-separated)
    tests_included = db.Column(db.Text)  # JSON list of tests
    
    # Common tests (individual flags for easy querying)
    blood_test = db.Column(db.Boolean, default=False)
    urine_test = db.Column(db.Boolean, default=False)
    chest_xray = db.Column(db.Boolean, default=False)
    ecg = db.Column(db.Boolean, default=False)
    ultrasound = db.Column(db.Boolean, default=False)
    mri = db.Column(db.Boolean, default=False)
    ct_scan = db.Column(db.Boolean, default=False)
    endoscopy = db.Column(db.Boolean, default=False)
    colonoscopy = db.Column(db.Boolean, default=False)
    mammography = db.Column(db.Boolean, default=False)
    pap_smear = db.Column(db.Boolean, default=False)
    bone_density = db.Column(db.Boolean, default=False)
    
    # Specialist consultations
    cardiology_consult = db.Column(db.Boolean, default=False)
    internal_medicine = db.Column(db.Boolean, default=False)
    gynecology = db.Column(db.Boolean, default=False)
    urology = db.Column(db.Boolean, default=False)
    ophthalmology = db.Column(db.Boolean, default=False)
    ent = db.Column(db.Boolean, default=False)
    dermatology = db.Column(db.Boolean, default=False)
    
    # Results
    checkup_date = db.Column(db.Date)
    results_ready = db.Column(db.Boolean, default=False)
    results_summary = db.Column(db.Text)  # Overall health summary
    abnormal_findings = db.Column(db.Text)  # Any concerns found
    recommendations = db.Column(db.Text)  # Doctor recommendations
    
    # Report files
    report_pdf_path = db.Column(db.String(255))
    
    # Pricing
    price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    
    # Follow-up
    follow_up_required = db.Column(db.Boolean, default=False)
    follow_up_notes = db.Column(db.Text)
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<CheckUpPackage {self.package_type}>'


class CheckUpTest(db.Model):
    """Individual test results within a check-up package"""
    __tablename__ = 'checkup_tests'
    
    id = db.Column(db.Integer, primary_key=True)
    checkup_id = db.Column(db.Integer, db.ForeignKey('checkup_packages.id'), nullable=False)
    
    test_name = db.Column(db.String(100), nullable=False)
    test_category = db.Column(db.String(50))  # Blood, Imaging, Cardiac, etc.
    result_value = db.Column(db.String(100))
    reference_range = db.Column(db.String(100))
    unit = db.Column(db.String(20))
    status = db.Column(db.String(20))  # normal, abnormal, critical
    
    result_date = db.Column(db.Date)
    result_file_path = db.Column(db.String(255))  # PDF/Image of result
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    checkup = db.relationship('CheckUpPackage', backref=db.backref('test_results', lazy=True))
    
    def __repr__(self):
        return f'<CheckUpTest {self.test_name}: {self.result_value}>'
