#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection, Distributor, User

app = create_app()
with app.app_context():
    
    # Tüm encounter'ları kontrol et - en son 10 tane
    print("🔍 Son 10 encounter:")
    all_recent = Encounter.query.order_by(Encounter.date.desc()).limit(10).all()
    
    for enc in all_recent:
        print(f"\n📋 Encounter {enc.id}:")
        print(f"  - Tarih: {enc.date}")
        print(f"  - Hasta: {enc.patient.full_name}")
        print(f"  - Oluşturan: {enc.created_by}")
        print(f"  - Durum: {enc.status}")
        
        # Göz verisi kontrolü
        eye_ref = EyeRefraction.query.filter_by(encounter_id=enc.id).first()
        eye_treat = EyeTreatmentSelection.query.filter_by(encounter_id=enc.id).all()
        
        print(f"  - Göz Refraksiyonu: {'VAR ✅' if eye_ref else 'YOK ❌'}")
        print(f"  - Göz Tedavileri: {len(eye_treat)} adet")
        
        if eye_ref:
            print(f"    📊 Refraksiyon:")
            print(f"      OD: SPH={eye_ref.od_sph}, CYL={eye_ref.od_cyl}, AXIS={eye_ref.od_ax}")
            print(f"      OS: SPH={eye_ref.os_sph}, CYL={eye_ref.os_cyl}, AXIS={eye_ref.os_ax}")
        
        if eye_treat:
            print(f"    🏥 Tedaviler:")
            for i, treatment in enumerate(eye_treat, 1):
                print(f"      {i}. {treatment.title} - {treatment.side} - {treatment.price}€")
    
    print(f"\n📊 Özet:")
    print(f"Toplam encounter: {len(all_recent)}")
    
    # clinic_admin kullanıcısını kontrol et
    clinic_admin = User.query.filter_by(username='clinic_admin').first()
    if clinic_admin:
        print(f"clinic_admin ID: {clinic_admin.id}")
        admin_encounters = [e for e in all_recent if e.created_by == clinic_admin.id]
        print(f"clinic_admin tarafından oluşturulan: {len(admin_encounters)} encounter")
    else:
        print("❌ clinic_admin kullanıcısı bulunamadı!")
    
    # Göz verili encounter sayısı
    eye_encounters = [e for e in all_recent if 
                     EyeRefraction.query.filter_by(encounter_id=e.id).first() or 
                     EyeTreatmentSelection.query.filter_by(encounter_id=e.id).all()]
    print(f"Göz verisi olan encounter: {len(eye_encounters)} adet")