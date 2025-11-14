#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection

app = create_app()
with app.app_context():
    
    # En son göz verisi olan encounter'ı bul
    encounters_with_eye = Encounter.query.join(EyeRefraction).all()
    print(f"Göz refraksiyonu olan encounter'lar: {len(encounters_with_eye)}")
    
    for enc in encounters_with_eye:
        print(f"- Encounter {enc.id}: {enc.date} (Patient: {enc.patient.full_name})")
        
        # Manuel sorgu ile verileri çek
        from app.models import EyeRefraction, EyeTreatmentSelection
        refraction = EyeRefraction.query.filter_by(encounter_id=enc.id).first()
        treatments = EyeTreatmentSelection.query.filter_by(encounter_id=enc.id).all()
        
        print(f"  Manuel Refraksiyon sorgusu: {refraction}")
        print(f"  Manuel Tedavi sorgusu: {len(treatments)} adet")
        
        # İlişkiler ile
        print(f"  İlişki ile refraksiyon: {enc.eye_refraction}")
        print(f"  İlişki ile tedavi: {len(enc.eye_treatments)} adet")
        
        # PDF generator ile test
        try:
            from app.utils.pdf_generator import EncounterPDFGenerator
            generator = EncounterPDFGenerator(enc)
            
            # Eye module kontrolü
            eye_refraction = EyeRefraction.query.filter_by(encounter_id=enc.id).first()
            eye_treatments = EyeTreatmentSelection.query.filter_by(encounter_id=enc.id).all()
            
            print(f"  PDF Generator - Eye refraction: {'Var' if eye_refraction else 'Yok'}")
            print(f"  PDF Generator - Eye treatments: {len(eye_treatments)} adet")
            
            if eye_refraction or eye_treatments:
                print(f"  ✅ PDF'de göz bölümü gösterilecek!")
            else:
                print(f"  ❌ PDF'de göz bölümü görünmeyecek")
                
        except Exception as e:
            print(f"  PDF test hatası: {e}")
        
        print()
        
    if not encounters_with_eye:
        print("❌ Hiç göz verisi bulunamadı!")
    else:
        print(f"✅ {len(encounters_with_eye)} encounter'da göz verisi bulundu")