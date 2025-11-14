from app import db
from datetime import datetime

class IVFTreatment(db.Model):
    __tablename__ = 'ivf_treatments'
    
    id = db.Column(db.Integer, primary_key=True)
    encounter_id = db.Column(db.Integer, db.ForeignKey('encounters.id'), nullable=False)
    
    # Treatment type
    treatment_type = db.Column(db.String(50), nullable=False)  # ivf, icsi, iui, egg_freezing, donor_egg
    treatment_name = db.Column(db.String(100))  # Turkish name
    cycle_number = db.Column(db.Integer, default=1)  # 1st attempt, 2nd attempt, etc.
    
    # Patient information
    female_age = db.Column(db.Integer)
    male_partner = db.Column(db.String(100))  # Partner name
    
    # Medical history
    infertility_duration_years = db.Column(db.Integer)
    previous_pregnancies = db.Column(db.Integer, default=0)
    previous_miscarriages = db.Column(db.Integer, default=0)
    infertility_cause = db.Column(db.String(200))  # Male factor, female factor, unexplained, etc.
    
    # Hormone levels (female)
    fsh_level = db.Column(db.Float)  # Follicle Stimulating Hormone
    lh_level = db.Column(db.Float)  # Luteinizing Hormone
    amh_level = db.Column(db.Float)  # Anti-Müllerian Hormone
    estradiol_level = db.Column(db.Float)
    
    # Sperm analysis (male)
    sperm_count = db.Column(db.String(50))  # Million/ml
    sperm_motility = db.Column(db.String(50))  # Percentage
    sperm_morphology = db.Column(db.String(50))  # Normal forms percentage
    
    # Treatment protocol
    stimulation_protocol = db.Column(db.String(100))  # Long protocol, Short protocol, Antagonist
    medications = db.Column(db.Text)  # List of medications
    egg_retrieval_date = db.Column(db.Date)
    eggs_retrieved = db.Column(db.Integer)
    eggs_fertilized = db.Column(db.Integer)
    embryos_created = db.Column(db.Integer)
    
    # Embryo transfer
    transfer_date = db.Column(db.Date)
    embryos_transferred = db.Column(db.Integer)
    embryo_quality = db.Column(db.String(100))  # Grade A, Grade B, Blastocyst, etc.
    embryos_frozen = db.Column(db.Integer)
    
    # Results
    pregnancy_test_date = db.Column(db.Date)
    pregnancy_result = db.Column(db.String(20))  # positive, negative, pending
    hcg_level = db.Column(db.Float)  # Beta HCG level
    
    # Pricing
    price = db.Column(db.Float, default=0)
    currency = db.Column(db.String(3), default='EUR')
    package_includes = db.Column(db.Text)  # Medications, tests, embryo freezing, etc.
    discount_enabled = db.Column(db.Boolean, default=False)
    discounted_price = db.Column(db.Float)
    
    # Success rate info
    clinic_success_rate = db.Column(db.String(50))  # "55% for age <35"
    
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<IVFTreatment {self.treatment_type} Cycle:{self.cycle_number}>'
