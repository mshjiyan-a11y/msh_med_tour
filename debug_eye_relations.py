"""
Tüm göz kayıtlarını incele
"""
from app import create_app, db
from app.models import Encounter, EyeRefraction, EyeTreatmentSelection

app = create_app()

def check_all_eye_data():
    with app.app_context():
        print("=== TÜM GÖZ KAYITLARI ===\n")
        
        print("1. Refraksiyon Kayıtları:")
        refractions = EyeRefraction.query.all()
        for ref in refractions:
            encounter = Encounter.query.get(ref.encounter_id)
            patient_name = encounter.patient.full_name if encounter and encounter.patient else 'N/A'
            print(f"  ID: {ref.id}, Encounter: {ref.encounter_id}, Hasta: {patient_name}")
            print(f"     OD: SPH={ref.od_sph}, CYL={ref.od_cyl}, AX={ref.od_ax}")
            print(f"     OS: SPH={ref.os_sph}, CYL={ref.os_cyl}, AX={ref.os_ax}")
            print(f"     Prosedür: {ref.planned_procedure}")
            print()
        
        print("\n2. Tedavi Kayıtları:")
        treatments = EyeTreatmentSelection.query.all()
        for treatment in treatments:
            encounter = Encounter.query.get(treatment.encounter_id)
            patient_name = encounter.patient.full_name if encounter and encounter.patient else 'N/A'
            print(f"  ID: {treatment.id}, Encounter: {treatment.encounter_id}, Hasta: {patient_name}")
            print(f"     Tedavi: {treatment.title} ({treatment.side})")
            print(f"     Fiyat: {treatment.price} {treatment.currency}")
            print()
        
        print("\n3. En son encounter'ları kontrol et:")
        encounters = Encounter.query.order_by(Encounter.id.desc()).limit(3).all()
        for encounter in encounters:
            print(f"Encounter {encounter.id}: Hasta {encounter.patient.full_name if encounter.patient else 'N/A'}")
            # Manuel sorgu ile kontrol et
            ref_manual = EyeRefraction.query.filter_by(encounter_id=encounter.id).first()
            treatments_manual = EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).all()
            
            print(f"  Manuel refraksiyon sorgusu: {'Var' if ref_manual else 'Yok'}")
            print(f"  Manuel tedavi sorgusu: {len(treatments_manual)} adet")
            print(f"  Relationship refraksiyon: {'Var' if encounter.eye_refraction else 'Yok'}")
            print(f"  Relationship tedaviler: {len(encounter.eye_treatments)} adet")
            print()

if __name__ == '__main__':
    check_all_eye_data()