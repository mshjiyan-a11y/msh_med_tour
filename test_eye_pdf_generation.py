#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection, Distributor

app = create_app()
with app.app_context():
    
    # Find a distributor
    distributor = Distributor.query.first()
    if not distributor:
        print("❌ Hiç distributor bulunamadı!")
        exit()
    
    # Find encounters with eye data
    encounters_with_eye = Encounter.query.join(EyeRefraction).all()
    
    if not encounters_with_eye:
        print("❌ Göz verili encounter bulunamadı!")
        exit()
    
    encounter = encounters_with_eye[0]
    print(f"Test için encounter {encounter.id} kullanılıyor - {encounter.patient.full_name}")
    
    try:
        from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
        generator = ProfessionalEncounterPDF(encounter, distributor)
        
        # Manuel sorgu ile test
        from app.models import EyeRefraction, EyeTreatmentSelection
        eye_refraction = EyeRefraction.query.filter_by(encounter_id=encounter.id).first()
        eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).all()
        
        print(f"Manuel sorgu - Refraksiyon: {'Var' if eye_refraction else 'Yok'}")
        print(f"Manuel sorgu - Tedaviler: {len(eye_treatments)} adet")
        
        if eye_refraction:
            print(f"  OD: SPH={eye_refraction.od_sph}, CYL={eye_refraction.od_cyl}, AXIS={eye_refraction.od_ax}")
            print(f"  OS: SPH={eye_refraction.os_sph}, CYL={eye_refraction.os_cyl}, AXIS={eye_refraction.os_ax}")
        
        if eye_treatments:
            for i, t in enumerate(eye_treatments, 1):
                print(f"  Tedavi {i}: {t.title} ({t.side}) - {t.price}€")
        
        # PDF oluştur
        pdf_buffer = generator.generate()
        print(f"✅ PDF başarıyla oluşturuldu! Boyut: {len(pdf_buffer.getvalue())} bytes")
        
        # Test dosya olarak kaydet
        with open('test_eye_pdf_output.pdf', 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print("✅ Test PDF dosyası kaydedildi: test_eye_pdf_output.pdf")
        
    except Exception as e:
        import traceback
        print(f"❌ PDF oluşturma hatası: {e}")
        traceback.print_exc()