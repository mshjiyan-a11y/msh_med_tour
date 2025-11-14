#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection, Distributor

app = create_app()
with app.app_context():
    
    # Encounter 19'u kontrol et
    encounter = Encounter.query.get(19)
    
    if not encounter:
        print("❌ Encounter 19 bulunamadı!")
        # Son encounter'ları listele
        recent = Encounter.query.order_by(Encounter.date.desc()).limit(5).all()
        print("📋 Son encounter'lar:")
        for enc in recent:
            print(f"  - {enc.id}: {enc.patient.full_name} ({enc.date})")
        exit()
    
    print(f"📋 Encounter 19 Detayları:")
    print(f"  - ID: {encounter.id}")
    print(f"  - Hasta: {encounter.patient.full_name}")
    print(f"  - Tarih: {encounter.date}")
    print(f"  - Durum: {encounter.status}")
    print(f"  - Oluşturan: {encounter.created_by}")
    
    # Göz verilerini kontrol et
    eye_ref = EyeRefraction.query.filter_by(encounter_id=19).first()
    eye_treats = EyeTreatmentSelection.query.filter_by(encounter_id=19).all()
    
    print(f"\n👁️ Göz Verileri:")
    print(f"  - Refraksiyon: {'VAR' if eye_ref else 'YOK'}")
    print(f"  - Tedaviler: {len(eye_treats)} adet")
    
    if eye_ref:
        print(f"    OD: SPH={eye_ref.od_sph}, CYL={eye_ref.od_cyl}, AXIS={eye_ref.od_ax}")
        print(f"    OS: SPH={eye_ref.os_sph}, CYL={eye_ref.os_cyl}, AXIS={eye_ref.os_ax}")
        print(f"    Prosedür: {eye_ref.planned_procedure}")
    
    if eye_treats:
        for i, treat in enumerate(eye_treats, 1):
            print(f"    Tedavi {i}: {treat.title} - {treat.side} - {treat.price}€")
    
    # PDF oluşturmayı test et
    print(f"\n📄 PDF Test:")
    try:
        distributor = Distributor.query.filter_by(id=encounter.distributor_id).first()
        if not distributor:
            print("❌ Distributor bulunamadı!")
            exit()
        
        print(f"  Distributor: {distributor.name}")
        
        from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
        generator = ProfessionalEncounterPDF(encounter, distributor)
        pdf_buffer = generator.generate()
        
        print(f"✅ PDF başarıyla oluşturuldu!")
        print(f"  Boyut: {len(pdf_buffer.getvalue())} bytes")
        
        # PDF dosyasını kaydet
        filename = f"debug_encounter_19.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"  Dosya kaydedildi: {filename}")
        
    except Exception as e:
        import traceback
        print(f"❌ PDF oluşturma hatası: {e}")
        traceback.print_exc()
    
    # Eğer göz verisi yoksa test verisi ekle
    if not eye_ref and not eye_treats:
        print(f"\n🧪 Test göz verisi ekleniyor...")
        
        test_ref = EyeRefraction(
            encounter_id=19,
            od_sph=-1.5,
            od_cyl=-0.25,
            od_ax=90,
            os_sph=-1.75,
            os_cyl=-0.5,
            os_ax=85,
            planned_procedure='LASIK'
        )
        db.session.add(test_ref)
        
        test_treat = EyeTreatmentSelection(
            encounter_id=19,
            code='LASIK',
            title='LASIK Eye Surgery',
            side='OU',
            price=2800.0,
            currency='EUR',
            note='Test treatment for encounter 19'
        )
        db.session.add(test_treat)
        
        db.session.commit()
        print("✅ Test göz verisi eklendi!")
        
        # PDF'yi tekrar oluştur
        print(f"\n📄 Göz verisi ile PDF Test:")
        try:
            generator = ProfessionalEncounterPDF(encounter, distributor)
            pdf_buffer = generator.generate()
            
            filename = f"encounter_19_with_eye_data.pdf"
            with open(filename, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"✅ Göz verisi ile PDF oluşturuldu: {filename}")
            print(f"  Boyut: {len(pdf_buffer.getvalue())} bytes")
            
        except Exception as e:
            print(f"❌ Göz verisi ile PDF hatası: {e}")
            import traceback
            traceback.print_exc()