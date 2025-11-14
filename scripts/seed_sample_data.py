import os
import sys
from datetime import datetime

# Add project root to path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app, db
from app.models.distributor import Distributor
from app.models.user import User
from app.models.patient import Patient
from app.models.encounter import Encounter
from app.models.hair import HairAnnotation, HairPatternSelection
from app.models.dental import DentalProcedure
from app.models.eye import EyeRefraction, EyeTreatmentSelection

app = create_app()

def create_sample_distributor():
    distributor = Distributor(
        name="EstetikMed Clinic",
        contact_name="Dr. Ahmet Yılmaz",
        phone="+90 532 555 1234",
        email="info@estetikmed.com",
        address="Bağdat Caddesi No:123, Kadıköy, İstanbul",
        color_hex="#2c3e50",
        pdf_footer_text="EstetikMed Clinic - Your Beauty & Health Partner\nwww.estetikmed.com | +90 532 555 1234",
        enable_hair=True,
        enable_teeth=True,
        enable_eye=True
    )
    db.session.add(distributor)
    db.session.commit()
    
    # Create distributor admin
    admin = User(
        distributor_id=distributor.id,
        username="clinic_admin",
        email="admin@estetikmed.com",
        role="distributor",
        first_name="Ahmet",
        last_name="Yılmaz",
        phone="+90 532 555 1234"
    )
    admin.set_password("clinic123")
    db.session.add(admin)
    db.session.commit()
    
    return distributor

def create_sample_patients(distributor):
    patients = [
        {
            "full_name": "John Smith",
            "phone": "+44 7700 900123",
            "email": "john.smith@example.com",
            "dob": "1985-03-15",
            "gender": "M",
            "notes": "Interested in hair transplant and dental work",
            "nationality": "British",
            "passport_number": "GBR123456"
        },
        {
            "full_name": "Maria Schmidt",
            "phone": "+49 151 23456789",
            "email": "maria.schmidt@example.com",
            "dob": "1990-07-22",
            "gender": "F",
            "notes": "Looking for comprehensive dental treatment",
            "nationality": "German",
            "passport_number": "DEU987654"
        },
        {
            "full_name": "Ahmed Al-Sayed",
            "phone": "+971 50 123 4567",
            "email": "ahmed.alsayed@example.com",
            "dob": "1978-11-30",
            "gender": "M",
            "notes": "Interested in LASIK surgery",
            "nationality": "UAE",
            "passport_number": "UAE456789"
        }
    ]
    
    created_patients = []
    for p in patients:
        # Split full_name into first_name and last_name
        name_parts = p["full_name"].split(' ', 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""
        
        patient = Patient(
            distributor_id=distributor.id,
            first_name=first_name,
            last_name=last_name,
            phone=p["phone"],
            email=p["email"],
            dob=datetime.strptime(p["dob"], "%Y-%m-%d").date(),
            gender=p["gender"],
            notes=p["notes"],
            nationality=p["nationality"],
            passport_number=p["passport_number"]
        )
        db.session.add(patient)
        created_patients.append(patient)
    
    db.session.commit()
    return created_patients

def create_sample_encounters(patients):
    # Sample encounter for hair transplant
    hair_encounter = Encounter(
        distributor_id=patients[0].distributor_id,
        patient_id=patients[0].id,
        date=datetime.utcnow(),
        note="Initial consultation for hair transplant",
        status="draft"
    )
    db.session.add(hair_encounter)
    db.session.commit()
    
    # Add hair pattern
    pattern = HairPatternSelection(
        encounter_id=hair_encounter.id,
        pattern_key="norwood_04",
        note="Moderate crown thinning"
    )
    db.session.add(pattern)
    
    # Add hair annotations
    annotations = [
        ("crown", "Significant thinning", "Consider 1000-1200 grafts"),
        ("front", "Receding hairline", "Requires 800-1000 grafts")
    ]
    for region, label, note in annotations:
        anno = HairAnnotation(
            encounter_id=hair_encounter.id,
            region_id=region,
            label=label,
            note=note
        )
        db.session.add(anno)
    
    # Sample encounter for dental work
    dental_encounter = Encounter(
        distributor_id=patients[1].distributor_id,
        patient_id=patients[1].id,
        date=datetime.utcnow(),
        note="Full dental examination and treatment plan",
        status="draft"
    )
    db.session.add(dental_encounter)
    db.session.commit()
    
    # Add dental procedures
    procedures = [
        (14, "Crown", "Porcelain crown needed", 500),
        (16, "Implant", "Titanium implant recommended", 800),
        (24, "Filling", "Composite filling required", 150),
        (46, "Root Canal", "Root canal treatment needed", 400)
    ]
    for tooth_no, treatment, note, price in procedures:
        proc = DentalProcedure(
            encounter_id=dental_encounter.id,
            tooth_no=tooth_no,
            treatment_type=treatment,
            note=note,
            price=price
        )
        db.session.add(proc)
    
    # Sample encounter for eye examination
    eye_encounter = Encounter(
        distributor_id=patients[2].distributor_id,
        patient_id=patients[2].id,
        date=datetime.utcnow(),
        note="LASIK consultation and eye examination",
        status="draft"
    )
    db.session.add(eye_encounter)
    db.session.commit()
    
    # Add eye refraction
    refraction = EyeRefraction(
        encounter_id=eye_encounter.id,
        od_sph=-2.75,  # Right eye
        od_cyl=-0.50,
        od_ax=180,
        os_sph=-2.25,  # Left eye
        os_cyl=-0.75,
        os_ax=165,
        planned_procedure="LASIK"
    )
    db.session.add(refraction)
    
    # Add eye treatments
    treatments = [
        ("LASIK_STD", "Standard LASIK", "OU", 1200, "Bilateral standard LASIK procedure"),
        ("PREP_EXAM", "Pre-op Examination", "OU", 150, "Complete pre-operative assessment")
    ]
    for code, title, side, price, note in treatments:
        treatment = EyeTreatmentSelection(
            encounter_id=eye_encounter.id,
            code=code,
            title=title,
            side=side,
            price=price,
            note=note
        )
        db.session.add(treatment)
    
    db.session.commit()

if __name__ == "__main__":
    with app.app_context():
        print("Creating sample distributor...")
        distributor = create_sample_distributor()
        print(f"Created distributor: {distributor.name}")
        
        print("\nCreating sample patients...")
        patients = create_sample_patients(distributor)
        print(f"Created {len(patients)} patients")
        
        print("\nCreating sample encounters...")
        create_sample_encounters(patients)
        print("Created encounters with hair, dental, and eye examinations")
        
        print("\nDone! You can now log in as:")
        print("Superadmin: admin / password")
        print("Clinic Admin: clinic_admin / clinic123")