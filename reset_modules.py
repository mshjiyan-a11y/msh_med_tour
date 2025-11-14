"""
Mevcut distribütörlerin modül ayarlarını sıfırla
"""
from app import create_app, db
from app.models import Distributor

app = create_app()

def reset_distributor_modules():
    with app.app_context():
        print("Mevcut distribütör modül ayarları sıfırlanıyor...")
        
        # Tüm distribütörleri getir
        distributors = Distributor.query.all()
        
        for dist in distributors:
            print(f"Distribütör: {dist.name}")
            print(f"  Önceki modüller: Saç={dist.enable_hair}, Diş={dist.enable_teeth}, Göz={dist.enable_eye}")
            
            # Tüm modülleri False yap (admin manuel olarak etkinleştirecek)
            dist.enable_hair = False
            dist.enable_teeth = False
            dist.enable_eye = False
            dist.enable_aesthetic = False
            dist.enable_bariatric = False
            dist.enable_ivf = False
            dist.enable_checkup = False
            
            print(f"  Yeni modüller: Tümü False")
            print()
        
        db.session.commit()
        print(f"✅ {len(distributors)} distribütörün modül ayarları sıfırlandı.")
        print("⚠️  Artık her distribütör için istenen modülleri manuel olarak etkinleştirin.")

if __name__ == '__main__':
    reset_distributor_modules()