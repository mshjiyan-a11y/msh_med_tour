#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection, Distributor, User

app = create_app()
with app.app_context():
    
    # clinic_admin kullanıcısını bul
    clinic_admin = User.query.filter_by(username='clinic_admin').first()
    if not clinic_admin:
        print("❌ clinic_admin kullanıcısı bulunamadı!")
        exit()
    
    print(f"✅ clinic_admin kullanıcısı bulundu - ID: {clinic_admin.id}")
    
    # clinic_admin tarafından oluşturulan son encounter'ları bul
    recent_encounters = Encounter.query.filter_by(created_by=clinic_admin.id).order_by(Encounter.date.desc()).limit(10).all()
    
    print(f"\n📊 clinic_admin tarafından oluşturulan son {len(recent_encounters)} encounter:")
    
    for encounter in recent_encounters:
        print(f"\n🔍 Encounter {encounter.id}:")
        print(f"  - Tarih: {encounter.date}")
        print(f"  - Hasta: {encounter.patient.full_name}")
        print(f"  - Durum: {encounter.status}")
        
        # Manuel göz verisi sorgusu
        eye_refraction = EyeRefraction.query.filter_by(encounter_id=encounter.id).first()
        eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=encounter.id).all()
        
        print(f"  - Göz Refraksiyonu: {'VAR' if eye_refraction else 'YOK'}")
        print(f"  - Göz Tedavileri: {len(eye_treatments)} adet")
        
        if eye_refraction:
            print(f"    OD: SPH={eye_refraction.od_sph}, CYL={eye_refraction.od_cyl}, AXIS={eye_refraction.od_ax}")
            print(f"    OS: SPH={eye_refraction.os_sph}, CYL={eye_refraction.os_cyl}, AXIS={eye_refraction.os_ax}")
        
        if eye_treatments:
            for i, treatment in enumerate(eye_treatments, 1):
                print(f"    Tedavi {i}: {treatment.title} - {treatment.side} - {treatment.price}€")
    
    # En son göz verisine sahip encounter'ı test et
    eye_encounter = None
    for enc in recent_encounters:
        eye_ref = EyeRefraction.query.filter_by(encounter_id=enc.id).first()
        eye_treat = EyeTreatmentSelection.query.filter_by(encounter_id=enc.id).all()
        if eye_ref or eye_treat:
            eye_encounter = enc
            print(f"\n🎯 PDF test için encounter {enc.id} seçildi (göz verisi var)")
            break
    
    if not eye_encounter:
        print("\n❌ clinic_admin tarafından oluşturulan hiçbir encounter'da göz verisi yok!")
        exit()
    
    # PDF test
    try:
        distributor = Distributor.query.first()
        if not distributor:
            print("❌ Distributor bulunamadı!")
            exit()
        
        from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
        generator = ProfessionalEncounterPDF(eye_encounter, distributor)
        pdf_buffer = generator.generate()
        
        print(f"✅ PDF başarıyla oluşturuldu! Boyut: {len(pdf_buffer.getvalue())} bytes")
        
        # Test dosyası kaydet
        filename = f"clinic_admin_eye_test_{eye_encounter.id}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        print(f"✅ Test PDF kaydedildi: {filename}")
        
    except Exception as e:
        import traceback
        print(f"❌ PDF oluşturma hatası: {e}")
        traceback.print_exc()