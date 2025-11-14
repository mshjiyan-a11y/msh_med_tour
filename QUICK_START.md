# Quick Start Guide - Facebook Lead Integration

## 🚀 5 Dakika Kurulum

### Prerequisites
- Python 3.8+
- Flask 2.3+
- sqlite3
- Meta Business Account

### Step 1: Meta API Credentials Hazırla (2 min)

```
1. business.facebook.com → Create Business Manager
2. Developers.facebook.com → Create App (Business type)
3. Add Marketing API + Leads product
4. Settings → Basic → Copy App ID & Secret
5. Generate Access Token (long-lived 60+ days)
6. Ad Manager → Create Lead Form → Copy Form ID
```

**Credentials Example:**
```
App ID: 123456789012345
Form ID: 987654321098765
Access Token: EAAxxxxxxxxxxxxx...
Page ID: 111222333444555
```

### Step 2: Admin Panel Setup (2 min)

```
1. Admin Panel açılır → Facebook Leads → Settings
2. Form Doldur:
   - Page ID: [paste]
   - Form ID: [paste]
   - Access Token: [paste]
   - Sync Interval: 5 (dakika)
   - Enable: ✓
3. "Test Connection" butonuna tıkla
4. "Sync Now" butonuna tıkla
```

### Step 3: Dashboard Kontrol (1 min)

```
Admin Panel → Facebook Leads → Lead'ler
Leadleri gör → Filterle → Yönet
```

---

## 📊 Key Features Quick Reference

| Özellik | Konum | Kullanım |
|---------|-------|---------|
| **Lead Dashboard** | Admin → Facebook Leads → Lead'ler | Leadleri listele, filtrele, yönet |
| **Lead Scoring** | Admin → Facebook Leads → Skor | En iyi leads, öneriler |
| **Analytics** | Admin → Facebook Leads → Analytics | Conversion funnels, performance |
| **Bulk Operations** | Dashboard → Checkbox + Action | 100+ leade aynı anda işlem |
| **Settings** | Admin → Distributor Settings → Meta API | Access token, form ID konfigürasyonu |

---

## 🔧 Common Operations

### Create Lead (Manual Test)
```python
from app.models.meta_lead import FacebookLead
from app import db

lead = FacebookLead(
    meta_lead_id='12345_test',
    first_name='Ahmet',
    last_name='Kaya',
    email='ahmet@example.com',
    phone='+905551234567',
    form_data='{"service": "eye_exam"}',
    distributor_id=1
)
db.session.add(lead)
db.session.commit()
```

### Change Lead Status
```python
from app.models.meta_lead import FacebookLead, LeadInteraction

lead = FacebookLead.query.get(1)
old_status = lead.status

lead.status = 'contacted'
lead.updated_at = datetime.utcnow()

interaction = LeadInteraction(
    lead_id=lead.id,
    user_id=1,
    interaction_type='status_changed',
    description=f'{old_status} → contacted',
    result='success'
)
db.session.add(interaction)
db.session.commit()
```

### Get Lead Score
```python
from app.services.lead_scoring import LeadScoringEngine

lead = FacebookLead.query.get(1)
score = LeadScoringEngine.calculate_score(lead)
level = LeadScoringEngine.get_score_level(score)
color = LeadScoringEngine.get_score_color(score)

print(f"Score: {score}/100 ({level}) - {color}")
```

### Export Leads
```python
from app.services.bulk_operations import BulkLeadOperations

lead_ids = [1, 2, 3, 4, 5]
result = BulkLeadOperations.export_leads(lead_ids, format='csv')

# CSV file saved to: exports/leads_{timestamp}.csv
```

### Send Email Notification
```python
from app.services.lead_notifications import LeadEmailNotifications

lead = FacebookLead.query.get(1)
LeadEmailNotifications.notify_new_lead(lead)
```

---

## 📈 Analytics Quick Access

### Via Dashboard
```
Admin → Facebook Leads → Analytics
- See conversion funnel
- View staff performance
- Download monthly report
```

### Via API
```bash
# Get stats JSON
curl http://localhost:5000/admin/facebook-leads/api/stats

# Download monthly report
curl http://localhost:5000/admin/facebook-leads/analytics/report?type=monthly&format=json > report.json
```

### Via Python
```python
from app.services.lead_analytics import LeadAnalytics

# Get conversion funnel
funnel = LeadAnalytics.get_conversion_funnel(days=30)

# Get staff performance
staff_perf = LeadAnalytics.get_assignment_analytics()

# Generate report
report = LeadAnalytics.generate_report('monthly')

# Export as JSON
json_data = LeadAnalytics.export_report_json('monthly')
```

---

## 🔐 User Permissions

| Role | Lead View | Lead Edit | Bulk Ops | Analytics | Settings |
|------|-----------|-----------|----------|-----------|----------|
| Superadmin | ✓ | ✓ | ✓ | ✓ | ✓ |
| Admin | ✓ | ✓ | ✓ | ✓ | - |
| Staff | Assigned | Assigned | - | Own stats | - |
| Distributor | Own | Own | Own | Own | - |

---

## ⚠️ Troubleshooting

**Leadler görünmüyor?**
1. Meta config aktif mi? (Enable ✓)
2. Access token geçerli mi?
3. "Sync Now" butonunu tıkla
4. Log'ları kontrol et: `tail -f logs/flask.log`

**Emailler gönderilmiyor?**
1. SMTP config kontrol et
2. Gmail ise: App Password kullan
3. Firewall SMTP portunu bloke etmiyor mu?

**WebSocket bağlantı hatası?**
1. SocketIO kurulu mu? `pip install flask-socketio`
2. Server çalışıyor mu?
3. Tarayıcı console'unda hata bak

**Yavaş performans?**
1. Scheduler aralığını artır (e.g., 10 min)
2. Database indexleri ekle
3. Cache kullan

---

## 📞 Support

**Issues:** Check logs in `logs/` directory  
**Docs:** See `FACEBOOK_LEADS_ADVANCED_DOCS.md`  
**API Ref:** https://developers.facebook.com/docs/marketing-api  

---

**Version:** 2.0.0  
**Status:** Production Ready ✓
