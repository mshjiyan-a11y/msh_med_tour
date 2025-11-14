#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection

app = create_app()
with app.app_context():
    
    # clinic_admin'in son encounter'ını bul
    clinic_admin_encounters = Encounter.query.filter_by(created_by=2).order_by(Encounter.date.desc()).all()
    
    if not clinic_admin_encounters:
        print("❌ clinic_admin'in encounter'ı yok!")
        exit()
    
    latest_encounter = clinic_admin_encounters[0]
    print(f"📋 En son encounter: {latest_encounter.id} - {latest_encounter.patient.full_name}")
    print(f"   Tarih: {latest_encounter.date}")
    
    # Mevcut göz verisini kontrol et
    existing_ref = EyeRefraction.query.filter_by(encounter_id=latest_encounter.id).first()
    existing_treat = EyeTreatmentSelection.query.filter_by(encounter_id=latest_encounter.id).all()
    
    print(f"   Mevcut refraksiyon: {'VAR' if existing_ref else 'YOK'}")
    print(f"   Mevcut tedaviler: {len(existing_treat)} adet")
    
    # Test göz verisi ekle
    print(f"\n🧪 Test göz verisi ekleniyor...")
    
    # Önce mevcut verileri sil
    if existing_ref:
        db.session.delete(existing_ref)
        print("   Eski refraksiyon silindi")
    
    for treat in existing_treat:
        db.session.delete(treat)
    if existing_treat:
        print(f"   {len(existing_treat)} eski tedavi silindi")
    
    # Yeni test verileri ekle
    test_refraction = EyeRefraction(
        encounter_id=latest_encounter.id,
        od_sph=-2.5,
        od_cyl=-0.75,
        od_ax=180,
        os_sph=-2.25,
        os_cyl=-0.5,
        os_ax=175,
        planned_procedure='LASIK'
    )
    db.session.add(test_refraction)
    
    test_treatment = EyeTreatmentSelection(
        encounter_id=latest_encounter.id,
        code='LASIK',
        title='LASIK Surgery',
        side='OU',
        price=2500.0,
        currency='EUR',
        note='Test treatment for both eyes'
    )
    db.session.add(test_treatment)
    
    db.session.commit()
    print("✅ Test göz verisi eklendi!")
    
    # Doğrula
    new_ref = EyeRefraction.query.filter_by(encounter_id=latest_encounter.id).first()
    new_treat = EyeTreatmentSelection.query.filter_by(encounter_id=latest_encounter.id).all()
    
    print(f"\n✅ Doğrulama:")
    print(f"   Refraksiyon: {'VAR' if new_ref else 'YOK'}")
    print(f"   Tedaviler: {len(new_treat)} adet")
    
    if new_ref:
        print(f"   OD: SPH={new_ref.od_sph}, CYL={new_ref.od_cyl}, AXIS={new_ref.od_ax}")
        print(f"   OS: SPH={new_ref.os_sph}, CYL={new_ref.os_cyl}, AXIS={new_ref.os_ax}")
    
    # PDF test
    print(f"\n📄 PDF test...")
    try:
        from app.models import Distributor
        distributor = Distributor.query.first()
        
        from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
        generator = ProfessionalEncounterPDF(latest_encounter, distributor)
        pdf_buffer = generator.generate()
        
        filename = f"test_clinic_admin_eye_{latest_encounter.id}.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ PDF oluşturuldu: {filename}")
        print(f"   Boyut: {len(pdf_buffer.getvalue())} bytes")
        
    except Exception as e:
        print(f"❌ PDF hatası: {e}")
        import traceback
        traceback.print_exc()