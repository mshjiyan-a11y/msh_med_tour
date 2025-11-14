"""
Göz muayenesi verilerini kontrol et
"""
from app import create_app, db
from app.models import Encounter, EyeRefraction, EyeTreatmentSelection

app = create_app()

def check_eye_data():
    with app.app_context():
        print("=== Göz Muayenesi Veri Kontrolü ===\n")
        
        # Son 5 encounter'ı al
        encounters = Encounter.query.order_by(Encounter.id.desc()).limit(5).all()
        
        for encounter in encounters:
            print(f"Encounter ID: {encounter.id}")
            print(f"Hasta: {encounter.patient.full_name if encounter.patient else 'N/A'}")
            print(f"Tarih: {encounter.date}")
            
            # Göz refraksiyon verisi
            eye_refraction = encounter.eye_refraction
            if eye_refraction:
                print(f"  ✅ Göz Refraksiyon bulundu (ID: {eye_refraction.id})")
                print(f"     OD SPH: {eye_refraction.od_sph}, CYL: {eye_refraction.od_cyl}, AX: {eye_refraction.od_ax}")
                print(f"     OS SPH: {eye_refraction.os_sph}, CYL: {eye_refraction.os_cyl}, AX: {eye_refraction.os_ax}")
                print(f"     Prosedür: {eye_refraction.planned_procedure}")
            else:
                print(f"  ❌ Göz Refraksiyon bulunamadı")
            
            # Göz tedavi seçimleri
            eye_treatments = encounter.eye_treatments
            if eye_treatments:
                print(f"  ✅ Göz Tedavileri bulundu ({len(eye_treatments)} adet)")
                for treatment in eye_treatments:
                    print(f"     - {treatment.title} (Göz: {treatment.side})")
            else:
                print(f"  ❌ Göz Tedavisi bulunamadı")
            
            print()
        
        # Toplam göz verilerini say
        total_refractions = EyeRefraction.query.count()
        total_treatments = EyeTreatmentSelection.query.count()
        
        print(f"Toplam Refraksiyon Kayıtları: {total_refractions}")
        print(f"Toplam Tedavi Kayıtları: {total_treatments}")

if __name__ == '__main__':
    check_eye_data()