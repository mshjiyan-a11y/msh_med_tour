# MSH Med Tour - Facebook Lead Integration (Advanced Features)
## Kapsamlı Kurulum & Kullanım Kılavuzu

**Sürüm:** 2.0.0 Advanced  
**Durum:** Üretim Hazır ✓  
**Tarih:** 2025-01-21

---

## 📋 İçindekiler

1. [Sistem Özeti](#sistem-özeti)
2. [Hızlı Kurulum](#hızlı-kurulum)
3. [Advanced Özellikler](#advanced-özellikler)
4. [API & WebSocket](#api--websocket)
5. [Yönetim Paneli](#yönetim-paneli)
6. [Troubleshooting](#troubleshooting)

---

## Sistem Özeti

### Mimari Bileşenler

```
Meta/Facebook Lead Ads
    ↓
MetaLeadService (API Integration)
    ↓
Database (Facebook_Leads, MetaAPIConfig, LeadInteraction)
    ↓
┌─────────────────────────────────────┐
│     Lead Management System          │
├─────────────────────────────────────┤
│ • Lead Scoring (100-point scale)    │
│ • Bulk Operations                   │
│ • Email Notifications               │
│ • Real-time WebSocket Updates       │
│ • Analytics & Reporting             │
│ • Auto-Scheduler (5-min sync)       │
└─────────────────────────────────────┘
    ↓
Admin Dashboard (Superadmin Only)
```

### Veritabanı Modelleri

```
Distributor (1) ──→ MetaAPIConfig (1)
     │                     │
     ├──→ FacebookLead (Many)
     │         │
     └─────────├──→ LeadInteraction (Many)
              │         ↓
              └─────→ User (Assigned_to)
```

---

## Hızlı Kurulum

### Step 1: Meta Developer Setup

1. **Meta Business Manager Oluştur**
   - https://business.facebook.com
   - "Create Account" → Business Manager

2. **App Oluştur**
   - Developers.facebook.com → My Apps → Create App
   - App Type: Business
   - Name: "MSH Lead Ads"

3. **Permissions Ekle**
   - App Roles → "Admin"
   - Products → Add "Marketing API"
   - Add Product → "Leads"

4. **Credentials Al**
   - Settings → Basic
   - App ID, App Secret kopyala
   - Generate Access Token → "Generate"
   - Long-lived token (60+ days) seç

5. **Page & Form Setup**
   - Facebook Page seç
   - Ad Manager → Leads → Create Lead Form
   - Form ID'sini kopyala

### Step 2: Admin Panel Kurulum

1. **Navbar: Admin → Facebook Leads → Settings**

2. **Form Doldur:**
   ```
   Page ID: 123456789012345
   Form ID: 987654321098765
   Access Token: EAAxxxxxxxxxxxxx...
   Sync Interval: 5 (dakika)
   Enable: ✓
   ```

3. **Bağlantı Testi**
   - "Connection Test" butonuna tıkla
   - Başarılı yanıt: "✓ Connection successful"

4. **İlk Senkronizasyon**
   - "Sync Now" butonuna tıkla
   - Dashboard → Facebook Leads'de leadler görünsün

---

## Advanced Özellikler

### 1. Lead Scoring System

**Scoring Algoritması (100 Puan Skalası):**

| Faktör | Puan | Hesaplama |
|--------|------|-----------|
| **Kişisel Bilgi** | 30 | Email + Telefon = 30, Bir tanesi = 15 |
| **Hızlı Yanıt** | 20 | Lead < 24h = 20 |
| **Hizmet İlgisi** | 25 | Form'da service seçili = 25 |
| **Katılım** | 15 | 3+ form alanı = 15, 1-2 = 7.5 |
| **Yaşlılık** | 10 | < 1h = 10, < 24h = 5 |
| **TOPLAM** | **100** | - |

**Skor Seviyeleri:**
- **80-100:** Çok İyi (Yeşil) - İşleme al
- **60-79:** İyi (Mavi)
- **40-59:** Orta (Sarı)
- **20-39:** Düşük (Turuncu)
- **0-19:** Çok Düşük (Kırmızı)

**Kullanım:**

```python
from app.services.lead_scoring import LeadScoringEngine

# Bir lead'in skoru hesapla
lead = FacebookLead.query.get(1)
score = LeadScoringEngine.calculate_score(lead)

# En iyi 10 lead'i al
top_leads = LeadScoringEngine.get_top_leads(limit=10)

# Yönetim önerileri al
recommendations = LeadScoringEngine.get_priority_recommendations()
```

**Dashboard Erişimi:**
```
Admin Panel → Facebook Leads → Scoring Dashboard
```

---

### 2. Bulk Operations

**Desteklenen İşlemler:**

1. **Toplu Durum Değişikliği**
   - Checkbox ile leadleri seç
   - "Bulk Action" → "Change Status"
   - Yeni durum seç → Uygula
   - Tüm leadlere interaction log kaydı

2. **Toplu Personel Ataması**
   - Checkbox ile leadleri seç
   - "Bulk Action" → "Assign"
   - Personel seç → Uygula
   - Status otomatik "assigned" olur

3. **Toplu Silme**
   - Checkbox ile leadleri seç
   - "Bulk Action" → "Delete"
   - Confirm → Leadler silinir
   - Interaction log kaydedilir

4. **Toplu Export**
   - Checkbox ile leadleri seç
   - "Bulk Action" → "Export"
   - Format seç (CSV/JSON)
   - İndir

**CSV Format Örneği:**
```csv
ID,Ad Soyad,Email,Telefon,Dağıtıcı,Durum,Atanan Kişi,Oluşturulma Tarihi
1,Ahmet Kaya,ahmet@example.com,+905551234567,MSH Med Tour,new,,21.01.2025 10:30
2,Fatma Çetin,fatma@example.com,+905559876543,MSH Med Tour,assigned,drbulentkose,21.01.2025 11:15
```

---

### 3. Email Notifications

**Otomatik Email Gönderimi:**

| Tetikleyici | Alıcı | İçerik |
|-------------|-------|--------|
| Yeni Lead (Score > 30) | Admin | Lead bilgileri + Skor |
| Status Değişikliği | Atanan Kişi | Eski/Yeni Durum |
| Günlük Özet | Distributor Admin | Günlük Stats |

**Email Setup (config):**

```python
# config.py
MAIL_SERVER = 'smtp.gmail.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
MAIL_USERNAME = 'your-email@gmail.com'
MAIL_PASSWORD = 'your-app-password'
MAIL_DEFAULT_SENDER = 'MSH Lead System'
```

**Async Gönderim:**
```python
from app.services.lead_notifications import LeadEmailNotifications

# Yeni lead - otomatik gönderilir
LeadEmailNotifications.notify_new_lead(lead)

# Status değişikliği - otomatik gönderilir
LeadEmailNotifications.notify_status_change(
    lead, old_status, new_status, current_user
)

# Günlük özet
LeadEmailNotifications.send_daily_summary(distributor_id)
```

---

### 4. Real-time WebSocket Updates

**SocketIO Namespace: `/facebook-leads`**

```javascript
// Client-side JavaScript

const socket = io('http://localhost:5000/facebook-leads');

// Lead room'a katıl
socket.emit('join_lead', {lead_id: 123});

// Lead güncellemesini dinle
socket.on('lead_updated', (data) => {
    console.log('Lead updated:', data);
    // Dashboard'ı güncelle
});

// Yeni lead bildirimi
socket.on('lead_created', (data) => {
    console.log('New lead:', data.name);
    // Toast notification göster
});

// İstatistik güncellemesi
socket.on('stats_updated', (stats) => {
    console.log('Stats:', stats);
    // Dashboard kartlarını güncelle
});
```

**Backend Broadcasting:**

```python
from app.events.lead_events import (
    broadcast_lead_update,
    broadcast_lead_created,
    broadcast_stats_update
)

# Lead güncellemesi yayınla
broadcast_lead_update(lead_id, 'status_changed', {
    'old_status': 'new',
    'new_status': 'contacted'
})

# Yeni lead yayınla
broadcast_lead_created(lead)

# İstatistikleri güncelle
broadcast_stats_update()
```

---

### 5. Analytics & Reporting

**Metriler:**

1. **Conversion Funnel**
   - Total → Assigned → Contacted → Converted
   - Dönüştürme oranları (%)

2. **Distributor Performance**
   - Dağıtıcı başına toplam lead
   - Dönüştürme oranları
   - Ranking

3. **Staff Performance**
   - Personel başına atanan lead
   - Kişisel dönüştürme oranı
   - Top performer identifikasyonu

4. **Response Time Analytics**
   - Ortalama ilk yanıt süresi
   - Min/Max yanıt süresi
   - SLA tracking

5. **Interaction Statistics**
   - İşlem türü başına sayı
   - Başarı oranı

**Report Türleri:**

```python
from app.services.lead_analytics import LeadAnalytics

# Günlük rapor
daily_report = LeadAnalytics.generate_report('daily')

# Haftalık rapor
weekly_report = LeadAnalytics.generate_report('weekly')

# Aylık rapor (default)
monthly_report = LeadAnalytics.generate_report('monthly')

# JSON export
json_report = LeadAnalytics.export_report_json('monthly')

# HTML export
html_report = LeadAnalytics.export_report_html('monthly')
```

**Dashboard Erişimi:**
```
Admin Panel → Facebook Leads → Analytics
```

**Report Download:**
- Günlük/Haftalık/Aylık Rapor butonu
- JSON formatında API

---

## API & WebSocket

### REST API Endpoints

```bash
# Lead İstatistikleri
GET /admin/facebook-leads/api/stats

# Son Leadler
GET /admin/facebook-leads/api/recent?limit=10

# Lead Skorları
GET /admin/facebook-leads/api/scoring

# Analytics Data
GET /admin/facebook-leads/analytics/report?type=monthly&format=json
```

### WebSocket Events

**Emit (Gönder):**
```javascript
socket.emit('join_lead', {lead_id: 123});
socket.emit('leave_lead', {lead_id: 123});
```

**On (Dinle):**
```javascript
socket.on('connected', (data) => {});
socket.on('lead_updated', (data) => {});
socket.on('lead_created', (data) => {});
socket.on('stats_updated', (data) => {});
```

---

## Yönetim Paneli

### Menu Yapısı

```
Admin Panel
├── Facebook Leads (Dropdown)
│   ├── Lead'ler
│   │   ├── Filtreleme (Dağıtıcı, Durum, Arama)
│   │   ├── Toplu İşlemler
│   │   ├── Lead Detay
│   │   └── Durum/Not Yönetimi
│   ├── Scoring Dashboard
│   │   ├── Skor Dağılımı
│   │   ├── Yönetim Önerileri
│   │   └── En İyi Lead'ler
│   └── Analytics
│       ├── Conversion Funnel
│       ├── Performans Grafikleri
│       └── Report Download
├── Distributor Settings
│   └── Meta API Configuration
└── System Settings
```

### Kullanıcı Rolleri

| Rol | Erişim |
|-----|--------|
| Superadmin | Tüm özellikler |
| Admin | Lead management, Analytics |
| Staff | Atanan leadler |
| Distributor | Kendi leadleri |

---

## Troubleshooting

### Common Issues

**1. "Bağlantı başarısız: Invalid token"**
- Access Token'ın süresi doldu
- Yeni long-lived token oluştur
- Form ID'sini kontrol et

**2. "Leadler çekilmiyor"**
- Meta config aktif mi? (is_active = true)
- APScheduler kurulu mu? `pip install apscheduler`
- Scheduler başlatıldı mı? Terminal'de kontrol et
- Manuel sync dene: "Sync Now" butonu

**3. "Emailler gönderilmiyor"**
- SMTP yapılandırması kontrol et
- Gmail kullanıyorsan: App Password kullan (2FA şifre değil)
- Firewall SMTP portunu bloke etmiyor mu?

**4. "WebSocket bağlantı hatası"**
- SocketIO kurulu mu? `pip install flask-socketio`
- Server çalışıyor mu?
- CORS ayarları kontrol et

**5. "Duplicate lead hatası"**
- Aynı lead iki kez işleniyor
- Last_fetch_time kontrolü yap
- Sync aralığını artır

### Debug Mode

```python
# app routes - logging ekle
import logging
logger = logging.getLogger(__name__)

logger.debug(f"Lead processing: {lead_id}")
logger.error(f"Error occurred: {error}")
```

### Log Dosyaları

```bash
# Flask logs
tail -f logs/flask.log

# Celery/Scheduler logs
tail -f logs/scheduler.log

# Database logs
tail -f logs/database.log
```

---

## Performance Tuning

### Optimization Tips

1. **Database Indexing**
   ```python
   # meta_lead.py modellerde indexes ekle
   __table_args__ = (
       Index('idx_distributor_status', 'distributor_id', 'status'),
       Index('idx_meta_lead_id', 'meta_lead_id'),
   )
   ```

2. **Caching**
   ```python
   from app import cache
   
   @cache.cached(timeout=300)
   def get_lead_stats():
       return LeadAnalytics.get_conversion_funnel()
   ```

3. **Batch Processing**
   ```python
   # 100'den fazla lead için batch process
   for i in range(0, len(leads), 100):
       batch = leads[i:i+100]
       process_batch(batch)
   ```

### Scheduler Tuning

```python
# app/utils/meta_scheduler.py

# Dakika = 60 / Lead sayısı
# 1000 lead = 60/10 = 6 dakika interval
scheduler.add_job(
    sync_all_meta_leads,
    IntervalTrigger(minutes=6),  # Ayarla
)
```

---

## Gelecek Roadmap

- [ ] Webhook support (real-time push)
- [ ] Lead-CRM integration
- [ ] Advanced filtering (custom fields)
- [ ] Lead pipeline builder
- [ ] Multi-form support
- [ ] AI lead ranking
- [ ] Slack integration
- [ ] Zapier integration

---

## Support & Help

**Dokümantasyon:**
- Meta Graph API: https://developers.facebook.com/docs/marketing-api
- Flask-SocketIO: https://flask-socketio.readthedocs.io
- SQLAlchemy: https://docs.sqlalchemy.org

**Issues:**
- Hata loglarını kontrol et
- Debug mode'u aç
- Test endpoint'lerini çalıştır

---

**Son Güncelleme:** 2025-01-21  
**Sürüm:** 2.0.0 Advanced  
**Durum:** Production Ready ✓
