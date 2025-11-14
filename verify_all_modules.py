#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import (
    Encounter, HairAnnotation, HairPatternSelection, DentalProcedure,
    EyeRefraction, EyeTreatmentSelection, AestheticProcedure,
    BariatricSurgery, IVFTreatment, CheckUpPackage, Distributor
)

app = create_app()
with app.app_context():
    
    print("🔍 Encounter 19 - Tüm Modül Verileri Kontrolü")
    print("=" * 45)
    
    encounter = Encounter.query.get(19)
    print(f"📋 Encounter: {encounter.id} - {encounter.patient.full_name}")
    
    # Her modülün verilerini kontrol et
    modules = [
        ("💇 Saç Ekimi", HairAnnotation.query.filter_by(encounter_id=19).all()),
        ("🦷 Diş Tedavisi", DentalProcedure.query.filter_by(encounter_id=19).all()),
        ("👁️ Göz Ameliyatı", EyeRefraction.query.filter_by(encounter_id=19).all()),
        ("✨ Estetik Cerrahi", AestheticProcedure.query.filter_by(encounter_id=19).all()),
        ("⚖️ Bariatrik Cerrahi", BariatricSurgery.query.filter_by(encounter_id=19).all()),
        ("👶 IVF Tedavisi", IVFTreatment.query.filter_by(encounter_id=19).all()),
        ("❤️ Check-up", CheckUpPackage.query.filter_by(encounter_id=19).all())
    ]
    
    print(f"\n📊 Modül Veri Durumu:")
    all_ready = True
    for module_name, data in modules:
        count = len(data)
        status = "✅" if count > 0 else "❌"
        print(f"  {module_name}: {count} kayıt {status}")
        if count == 0:
            all_ready = False
            
        # İlk kayıtların detayını göster
        if count > 0:
            first_item = data[0]
            if hasattr(first_item, 'label'):
                print(f"    └─ {first_item.label}")
            elif hasattr(first_item, 'treatment_type'):
                print(f"    └─ {first_item.treatment_type}")
            elif hasattr(first_item, 'procedure_type'):
                print(f"    └─ {first_item.procedure_type}")
            elif hasattr(first_item, 'surgery_type'):
                print(f"    └─ {first_item.surgery_type}")
            elif hasattr(first_item, 'package_type'):
                print(f"    └─ {first_item.package_type}")
            elif hasattr(first_item, 'planned_procedure'):
                print(f"    └─ {first_item.planned_procedure}")
    
    if all_ready:
        print(f"\n🎉 Tüm modüller hazır! PDF test ediliyor...")
        
        # PDF oluştur
        try:
            distributor = Distributor.query.filter_by(id=encounter.distributor_id).first()
            
            from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
            generator = ProfessionalEncounterPDF(encounter, distributor)
            pdf_buffer = generator.generate()
            
            filename = f"complete_modules_test.pdf"
            with open(filename, 'wb') as f:
                f.write(pdf_buffer.getvalue())
            
            print(f"✅ PDF oluşturuldu: {filename}")
            print(f"📏 Boyut: {len(pdf_buffer.getvalue())} bytes")
            
            # Dosya boyutundan PDF'in zengin olup olmadığını tahmin et
            size_kb = len(pdf_buffer.getvalue()) / 1024
            if size_kb > 100:
                print(f"🎯 PDF zengin içerikli görünüyor ({size_kb:.1f} KB)")
            else:
                print(f"⚠️ PDF basit görünüyor ({size_kb:.1f} KB)")
                
        except Exception as e:
            print(f"❌ PDF hatası: {e}")
            import traceback
            traceback.print_exc()
    else:
        print(f"\n⚠️ Bazı modüllerde veri yok. Önce test verilerini oluşturun.")
        
    print(f"\n📋 Sonuç: Kullanıcı artık encounter 19'da tüm modül verilerini görmeli!")
    print(f"🌐 URL: http://127.0.0.1:5000/encounter/19/pdf/preview")