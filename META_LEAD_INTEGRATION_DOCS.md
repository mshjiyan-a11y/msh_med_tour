# Meta/Facebook Lead Integration - Dokümantasyon

## Genel Bakış

MSH Med Tour'a Meta/Facebook Lead Ads entegrasyonu başarıyla eklendi. Bu özellik, dağıtıcıların Facebook reklamlarından aldıkları leadleri canlı olarak sisteme çekmelerine ve yönetmelerine olanak sağlar.

## Yeni Özellikler

### 1. Database Modelleri
- **MetaAPIConfig**: Her dağıtıcı için Meta API kimlik bilgilerini saklar
- **FacebookLead**: Facebook'tan çekilen leadleri saklar
- **LeadInteraction**: Lead'lerle yapılan işlemleri (çağrı, email, not, durum değişikliği) takip eder

### 2. Meta Lead Service
`app/services/meta_lead_service.py` - Meta API ile iletişim kuran servis

**Temel Fonksiyonlar:**
```python
# Bağlantı testi
success, message = service.test_connection()

# Lead çekme
leads_data, error = service.fetch_leads(limit=100)

# Lead verilerini parse etme
parsed = service.parse_lead_data(lead_dict)

# Lead depolama
stored_count, errors = service.store_leads(leads_data)

# Tam senkronizasyon
result = service.sync_leads(limit=100)
# Returns: {'success': bool, 'fetched': int, 'stored': int, 'errors': list, 'message': str}
```

### 3. Admin Routes
- `GET/POST /admin/distributor/<id>/meta-settings` - Meta konfigürasyonu
- `POST /admin/api/meta-test/<config_id>` - Bağlantı testi
- `POST /admin/api/meta-sync/<config_id>` - Manuel senkronizasyon

### 4. Facebook Leads Dashboard
- `GET /admin/facebook-leads/` - Lead listesi (filtreleme, pagination)
- `GET /admin/facebook-leads/<id>` - Lead detayı
- `POST /admin/facebook-leads/<id>/status` - Durum güncelleme
- `POST /admin/facebook-leads/<id>/assign` - Personele atama
- `POST /admin/facebook-leads/<id>/note` - Not ekleme
- `POST /admin/facebook-leads/<id>/delete` - Lead silme
- `GET /admin/facebook-leads/api/stats` - İstatistikler
- `GET /admin/facebook-leads/api/recent` - Son leadler

### 5. Otomatik Senkronizasyon
`app/utils/meta_scheduler.py` - APScheduler entegrasyonu (5 dakikalık aralıklarla)

## Kurulum & Setup

### 1. Gerekli Paketler
```bash
pip install requests  # Already installed
pip install apscheduler  # For automatic sync (optional but recommended)
```

### 2. Meta Developer Account Setup

#### Adım 1: Meta Business Account Oluştur
- https://business.facebook.com/ adresine gidin
- Yeni Business Account oluşturun veya mevcut olanı kullanın

#### Adım 2: App Oluştur
- https://developers.facebook.com/ adresine gidin
- "My Apps" → "Create App"
- App Type: "Business"
- Temel bilgileri doldurun

#### Adım 3: Lead Form Oluştur (Facebook)
1. Facebook Page'inizde Ad Manager'ı açın
2. Lead Form başlığı altında Form oluşturun
3. Form ID'sini kopyalayın

#### Adım 4: API Credentials Al
1. App Settings → Basic → App ID ve App Secret'ı kopyalayın
2. Tools → Graph API Explorer'ı açın
3. Page Token oluşturun (Long-lived, 60 gün geçerliliği)

### 3. Admin Panelinde Ayarla

1. Admin Panel → Facebook Leads (Navbar'dan)
2. Dağıtıcı seç ve "Meta Ayarları" kısmına:
   - Page ID
   - Lead Form ID
   - Access Token
   - Senkronizasyon aralığı (örn: 5 dakika)
3. "Ayarları Kaydet"
4. "Bağlantı Testi" butonuyla test et
5. "Şimdi Senkronize Et" ile leadleri çek

## Lead Yönetimi

### Lead Statüleri
- **new** - Yeni lead, henüz işleme alınmadı
- **assigned** - Bir personele atanmış
- **contacted** - İletişim kurulmuş
- **converted** - Hastaya dönüştürülmüş
- **rejected** - Reddedilmiş

### Dashboard Kullanımı

#### Filtreleme & Arama
```
Dağıtıcı: Tüm dağıtıcılar veya belirli bir dağıtıcı seçin
Durum: Lead statüsüne göre filtrele
Ara: Ad, email veya telefona göre arama
```

#### Lead İşlemleri
1. **Durum Değiştir**: İkonlar ve detay sayfasında
2. **Personele Ata**: Durum değiştirme penceresinde
3. **Not Ekle**: Lead detayında
4. **Silme**: Lead detayında

### Interaction (İşlem) Takibi
Her lead için tüm işlemler loglanır:
- Status değişiklikleri
- Personel atamaları
- Eklenene notlar
- Çağrı/Email/SMS kayıtları

## API Entegrasyonu

### Bağlantı Testi
```bash
curl -X POST http://localhost:5000/admin/api/meta-test/1
```

Yanıt:
```json
{
    "success": true,
    "message": "Bağlantı başarılı"
}
```

### Manuel Senkronizasyon
```bash
curl -X POST http://localhost:5000/admin/api/meta-sync/1
```

Yanıt:
```json
{
    "success": true,
    "fetched": 10,
    "stored": 8,
    "message": "8/10 lead kaydedildi",
    "errors": []
}
```

### İstatistikler
```bash
curl http://localhost:5000/admin/facebook-leads/api/stats
```

Yanıt:
```json
{
    "total": 25,
    "new": 5,
    "assigned": 3,
    "contacted": 10,
    "converted": 5,
    "rejected": 2
}
```

## Teknik Detaylar

### Database İlişkileri
```
Distributor
├─ MetaAPIConfig (1:1)
│  └─ leads senkronizasyon ayarları
└─ FacebookLead (1:Many)
   ├─ assigned_to (User)
   └─ interactions (LeadInteraction)
       └─ user (User)
```

### Lead Veri Akışı
```
Facebook Lead Form
    ↓
Meta Graph API
    ↓
MetaLeadService.fetch_leads()
    ↓
MetaLeadService.parse_lead_data()
    ↓
FacebookLead (DB)
    ↓
Admin Dashboard
```

### Duplicate Kontrol
- Her lead için `meta_lead_id` unique constraint'i vardır
- Aynı Facebook lead ID iki kez kaydedilmez
- `last_fetch_time` ile senkronizasyon takip edilir

## Hata Ayıklama

### Common Errors

#### "Bağlantı başarısız: Invalid token"
- Access Token'ın süresi dolmuş olabilir
- Yeni long-lived token oluşturun

#### "Lead Form ID bulunamadı"
- Form ID'sini Facebook Ad Manager'dan kontrol edin
- Doğru formatını kullanıyor musunuz? (sadece rakam)

#### "Duplicate lead error"
- Aynı lead iki kez işleniyor olabilir
- `last_fetch_time` kontrol edin
- Senkronizasyon aralığını artırın

#### APScheduler Hatası
- APScheduler kurulu değilse otomatik sync çalışmaz
- Manuel sync'i kullanabilirsiniz
- `pip install apscheduler` ile kurun

### Debug Logging
Hata ayıklamak için log'ları kontrol edin:
```python
import logging
logger = logging.getLogger('app.services.meta_lead_service')
logger.setLevel(logging.DEBUG)
```

## Güvenlik

### Token Depolama
- Access Token'lar güvenli şekilde veritabanında depolanır
- Üretim ortamında encryption önerilir:
```python
from cryptography.fernet import Fernet

# Encrypt token before storing
encrypted = cipher.encrypt(access_token.encode())
```

### API Key Validation
- Tüm API isteklerinde CSRF protection aktif
- Superadmin kontrolü vardır
- Tüm işlemler auditlog'a kaydedilir

## Gelecek Geliştirmeler

1. **Webhook Support**: Real-time lead notifications
2. **Lead Scoring**: Otomatik lead değerlendirmesi
3. **CRM Integration**: Existing lead model'e bağlanma
4. **Bulk Actions**: Multiple lead işlemeleri
5. **Email Notifications**: Yeni lead bildirimleri
6. **Advanced Analytics**: Lead conversion funnels

## Test Etme

### Test Script Çalıştır
```bash
python test_meta_integration.py
```

Çıktısı:
```
============================================================
Meta/Facebook Lead Integration Test
============================================================

[1] Checking distributors...
   OK: Found distributor: MSH Med Tour (ID: 1)

[2] Checking Meta API Config...
   OK: Config exists (ID: 1)

[3] Creating test Facebook leads...
   OK: Created lead: Ahmet Kaya (ahmet@example.com)
   ...
```

## Dosya Yapısı

```
app/
├── models/
│   └── meta_lead.py              # Database models
├── services/
│   └── meta_lead_service.py       # Meta API service
├── routes/
│   ├── facebook_leads.py          # Lead management routes
│   └── admin.py                   # Admin integration
├── utils/
│   └── meta_scheduler.py          # Automatic sync scheduler
└── templates/admin/facebook_leads/
    ├── index.html                 # Leads dashboard
    └── view.html                  # Lead detail view

test_meta_integration.py            # Test script
```

## Yardım & Destek

### Meta Graph API Dokümantasyonu
- https://developers.facebook.com/docs/marketing-api/guides/lead-ads
- https://developers.facebook.com/docs/facebook-login/access-tokens

### Sık Sorulan Sorular (SSS)

**S: Lead'ler otomatik olarak çekiliyor mu?**
A: Evet, APScheduler kuruluysa 5 dakikada bir. Yoksa manuel "Senkronize Et" butonunu kullanın.

**S: Kaç lead çekebilirim?**
A: Meta'nın API limitine bağlı. Genelde 100-1000 lead/dakika.

**S: Lead'leri silebilir miyim?**
A: Evet, lead detay sayfasında "Leadi Sil" butonu vardır.

**S: Multiple lead form'u destekler miyor?**
A: Mevcut versiyonda 1 distributor = 1 form. Geliştirmede çoklu form desteği planlanıyor.

---

**Sürüm**: 1.0.0  
**Tarih**: 2025-01-21  
**Durum**: Üretim Hazır ✓
