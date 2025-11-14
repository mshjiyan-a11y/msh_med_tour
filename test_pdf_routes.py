#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
import requests

# Flask app'i test mode'da çalıştır
app = create_app()

if __name__ == '__main__':
    print("🔍 PDF Preview Route Test")
    print("=" * 30)
    
    # Test URL'leri
    base_url = "http://127.0.0.1:5000"
    encounter_id = 19
    
    test_urls = [
        f"{base_url}/encounter/{encounter_id}/pdf",
        f"{base_url}/encounter/{encounter_id}/pdf/preview"
    ]
    
    print(f"Encounter ID: {encounter_id}")
    print(f"Base URL: {base_url}")
    print()
    
    for url in test_urls:
        print(f"Testing: {url}")
        try:
            response = requests.get(url, timeout=10)
            print(f"  Status: {response.status_code}")
            print(f"  Content-Type: {response.headers.get('Content-Type', 'N/A')}")
            print(f"  Content-Length: {len(response.content)} bytes")
            
            if response.status_code == 200:
                print("  ✅ SUCCESS")
            else:
                print(f"  ❌ ERROR: {response.status_code}")
                print(f"  Response: {response.text[:200]}...")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ CONNECTION ERROR: {e}")
        
        print()
    
    # Manuel URL test
    print("📋 Manuel Test Komutları:")
    print(f"1. Flask uygulaması çalıştır: python run.py")
    print(f"2. Browser'da test et:")
    for url in test_urls:
        print(f"   - {url}")
    print()
    
    print("🔍 Debug için kontrol edilecekler:")
    print("1. Flask uygulaması çalışıyor mu?")
    print("2. Login yapılmış mı? (PDF routes @login_required)")
    print("3. User'ın distributor_id'si encounter'la uyuyor mu?")
    print("4. Browser console'da JavaScript hatası var mı?")
    print("5. Network tab'da HTTP error var mı?")