#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app, db
from app.models import Patient, Encounter, EyeRefraction, EyeTreatmentSelection

app = create_app()

# Test form data simulation
test_form_data = {
    'enable_eye': 'on',
    'eye_od_sph': '-2.5',
    'eye_od_cyl': '-0.75',
    'eye_od_axis': '180',
    'eye_od_visual_acuity': '20/20',
    'eye_os_sph': '-2.25',
    'eye_os_cyl': '-0.5',
    'eye_os_axis': '175',
    'eye_os_visual_acuity': '20/25',
    'eye_procedure': 'LASIK',
    'eye_treatments': ['Surgery', 'Post-operative Care']
}

with app.app_context():
    print("🧪 Eye Form Data Simulation Test")
    print("================================")
    
    # Test karışık hastayla encounter oluştur
    patient = Patient.query.first()
    if not patient:
        print("❌ Test için hasta bulunamadı!")
        exit()
    
    print(f"📋 Test Patient: {patient.full_name}")
    
    # Simulate form processing logic from main.py
    print("\n🔍 Form Data Processing:")
    
    enable_eye = test_form_data.get('enable_eye')
    print(f"  enable_eye: {enable_eye}")
    
    if enable_eye:
        # Refraction data test
        od_sph = test_form_data.get('eye_od_sph')
        os_sph = test_form_data.get('eye_os_sph')
        print(f"  od_sph: {od_sph}")
        print(f"  os_sph: {os_sph}")
        
        if od_sph or os_sph:
            print("  ✅ Refraction data would be created:")
            print(f"    OD: SPH={od_sph}, CYL={test_form_data.get('eye_od_cyl')}, AXIS={test_form_data.get('eye_od_axis')}")
            print(f"    OS: SPH={os_sph}, CYL={test_form_data.get('eye_os_cyl')}, AXIS={test_form_data.get('eye_os_axis')}")
            print(f"    Procedure: {test_form_data.get('eye_procedure')}")
        
        # Treatment data test
        if isinstance(test_form_data.get('eye_treatments'), list):
            treatments = test_form_data.get('eye_treatments')
        else:
            treatments = [test_form_data.get('eye_treatments')] if test_form_data.get('eye_treatments') else []
        
        print(f"  eye_treatments: {treatments}")
        print(f"  ✅ {len(treatments)} treatment(s) would be created")
        
        for i, treatment in enumerate(treatments, 1):
            if treatment:
                print(f"    {i}. {treatment}")
    
    print(f"\n📝 Expected JavaScript Form Fields:")
    print(f"  - name='eye_od_sph' value='-2.5'")
    print(f"  - name='eye_od_cyl' value='-0.75'")
    print(f"  - name='eye_od_axis' value='180'")
    print(f"  - name='eye_os_sph' value='-2.25'")
    print(f"  - name='eye_os_cyl' value='-0.5'")
    print(f"  - name='eye_os_axis' value='175'")
    print(f"  - name='eye_treatments' value='Surgery'")
    print(f"  - name='eye_treatments' value='Post-operative Care'")
    
    print(f"\n🎯 Problem: If form fields don't match server expectations, data won't save!")