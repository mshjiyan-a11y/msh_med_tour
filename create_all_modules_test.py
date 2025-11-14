#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import (
    Patient, Encounter, Distributor,
    HairAnnotation, HairPatternSelection,
    DentalProcedure,
    EyeRefraction, EyeTreatmentSelection,
    AestheticProcedure,
    BariatricSurgery,
    IVFTreatment,
    CheckUpPackage
)

app = create_app()
with app.app_context():
    
    print("🧪 Tüm Modüller için Test Verisi Oluşturuluyor")
    print("=" * 50)
    
    # Test encounter'ı al (19 numaralı)
    encounter = Encounter.query.get(19)
    if not encounter:
        print("❌ Encounter 19 bulunamadı!")
        exit()
    
    print(f"📋 Test Encounter: {encounter.id} - {encounter.patient.full_name}")
    
    # Mevcut tüm verileri temizle
    print("\n🗑️ Mevcut verileri temizleniyor...")
    
    # Mevcut verileri sil
    existing_modules = [
        HairAnnotation.query.filter_by(encounter_id=19).all(),
        HairPatternSelection.query.filter_by(encounter_id=19).all(),
        DentalProcedure.query.filter_by(encounter_id=19).all(),
        EyeRefraction.query.filter_by(encounter_id=19).all(),
        EyeTreatmentSelection.query.filter_by(encounter_id=19).all(),
        AestheticProcedure.query.filter_by(encounter_id=19).all(),
        BariatricSurgery.query.filter_by(encounter_id=19).all(),
        IVFTreatment.query.filter_by(encounter_id=19).all(),
        CheckUpPackage.query.filter_by(encounter_id=19).all()
    ]
    
    for module_list in existing_modules:
        for item in module_list:
            db.session.delete(item)
    
    db.session.commit()
    print("✅ Mevcut veriler temizlendi")
    
    # 1. HAIR MODULE
    print("\n💇 Saç Ekimi Test Verisi...")
    hair_annotation = HairAnnotation(
        encounter_id=19,
        region_id='frontal',
        label='Frontal Bölge - 1200 Greft',
        note='Yoğun saç ekimi gerekli'
    )
    db.session.add(hair_annotation)
    
    hair_pattern = HairPatternSelection(
        encounter_id=19,
        pattern_key='norwood_4',
        note='Norwood 4 - Orta seviye saç kaybı'
    )
    db.session.add(hair_pattern)
    
    # 2. DENTAL MODULE  
    print("🦷 Diş Tedavisi Test Verisi...")
    dental_proc = DentalProcedure(
        encounter_id=19,
        tooth_no=14,
        treatment_type='İmplant',
        price=800.0,
        currency='EUR',
        note='Üst sol premolar implant'
    )
    db.session.add(dental_proc)
    
    # 3. EYE MODULE (zaten mevcut ama yenile)
    print("👁️ Göz Ameliyatı Test Verisi...")
    eye_refraction = EyeRefraction(
        encounter_id=19,
        od_sph=-1.5,
        od_cyl=-0.25,
        od_ax=90,
        os_sph=-1.75,
        os_cyl=-0.5,
        os_ax=85,
        planned_procedure='LASIK'
    )
    db.session.add(eye_refraction)
    
    eye_treatment = EyeTreatmentSelection(
        encounter_id=19,
        code='LASIK',
        title='LASIK Eye Surgery',
        side='OU',
        price=2800.0,
        currency='EUR',
        note='Both eyes LASIK procedure'
    )
    db.session.add(eye_treatment)
    
    # 4. AESTHETIC MODULE
    print("✨ Estetik Cerrahi Test Verisi...")
    aesthetic_proc = AestheticProcedure(
        encounter_id=19,
        procedure_type='rhinoplasty',
        procedure_name='Burun Estetiği',
        body_area='nose',
        technique='Açık Rinoplasti',
        anesthesia_type='Genel Anestezi'
    )
    db.session.add(aesthetic_proc)
    
    # 5. BARIATRIC MODULE
    print("⚖️ Bariatrik Cerrahi Test Verisi...")
    bariatric_surgery = BariatricSurgery(
        encounter_id=19,
        surgery_type='sleeve',
        surgery_name='Sleeve Gastrektomi',
        weight_kg=95.0,
        height_cm=170,
        bmi=32.9,
        target_weight_kg=70.0,
        diabetes=False
    )
    db.session.add(bariatric_surgery)
    
    # 6. IVF MODULE
    print("👶 IVF Tedavisi Test Verisi...")
    ivf_treatment = IVFTreatment(
        encounter_id=19,
        treatment_type='ivf',
        treatment_name='IVF Tedavisi',
        cycle_number=1,
        female_age=32,
        male_partner='Test Partner',
        infertility_duration_years=2,
        previous_pregnancies=0
    )
    db.session.add(ivf_treatment)
    
    # 7. CHECKUP MODULE
    print("❤️ Check-Up Paketi Test Verisi...")
    checkup_package = CheckUpPackage(
        encounter_id=19,
        package_type='premium',
        package_name='Gold Check-Up Paketi',
        tests_included='Kan testi, EKG, Röntgen, Ultrason',
        blood_test=True,
        urine_test=True,
        chest_xray=True,
        ecg=True
    )
    db.session.add(checkup_package)
    
    # Tüm verileri kaydet
    db.session.commit()
    print("\n✅ Tüm modül test verileri kaydedildi!")
    
    # Doğrulama
    print(f"\n🔍 Doğrulama:")
    modules_check = [
        ('Saç', len(HairAnnotation.query.filter_by(encounter_id=19).all())),
        ('Diş', len(DentalProcedure.query.filter_by(encounter_id=19).all())),
        ('Göz', len(EyeRefraction.query.filter_by(encounter_id=19).all())),
        ('Estetik', len(AestheticProcedure.query.filter_by(encounter_id=19).all())),
        ('Bariatrik', len(BariatricSurgery.query.filter_by(encounter_id=19).all())),
        ('IVF', len(IVFTreatment.query.filter_by(encounter_id=19).all())),
        ('Check-up', len(CheckUpPackage.query.filter_by(encounter_id=19).all()))
    ]
    
    for module_name, count in modules_check:
        print(f"  {module_name}: {count} kayıt {'✅' if count > 0 else '❌'}")
    
    # PDF Test
    print(f"\n📄 Tüm Modüller ile PDF Test...")
    try:
        distributor = Distributor.query.filter_by(id=encounter.distributor_id).first()
        
        from app.utils.professional_pdf_generator import ProfessionalEncounterPDF
        generator = ProfessionalEncounterPDF(encounter, distributor)
        pdf_buffer = generator.generate()
        
        filename = f"all_modules_test_encounter_19.pdf"
        with open(filename, 'wb') as f:
            f.write(pdf_buffer.getvalue())
        
        print(f"✅ Tüm modüller ile PDF oluşturuldu: {filename}")
        print(f"📊 PDF Boyutu: {len(pdf_buffer.getvalue())} bytes")
        print(f"\n🎯 Artık PDF'te şu bölümler görünmeli:")
        print(f"  - 💇 Saç Ekimi (1200 greft)")
        print(f"  - 🦷 Diş Tedavisi (14 numaralı diş implant)")  
        print(f"  - 👁️ Göz Ameliyatı (LASIK)")
        print(f"  - ✨ Estetik Cerrahi (Rinoplasti)")
        print(f"  - ⚖️ Bariatrik Cerrahi (Sleeve)")
        print(f"  - 👶 IVF Tedavisi (1. döngü)")
        print(f"  - ❤️ Check-up Paketi (Gold)")
        
    except Exception as e:
        print(f"❌ PDF oluşturma hatası: {e}")
        import traceback
        traceback.print_exc()