# MSH Med Tour - Medical Tourism Management System

## 🏥 Overview

MSH Med Tour is a comprehensive medical tourism management system with integrated Facebook Lead Ads support. It enables healthcare providers and distributors to manage patient journeys, appointments, and lead generation through Meta's Lead Ads platform.

**Current Version:** 2.0.0 (Facebook Lead Ads Integration)

### ✨ Key Features

- **Facebook Lead Ads Integration** - Real-time lead capture from Meta Lead Ads
- **Lead Scoring & Analytics** - AI-powered lead quality assessment
- **Multi-Distributor Support** - Manage multiple healthcare distribution partners
- **Patient Journey Management** - End-to-end patient coordination
- **Medical Modules** - Dental, Eye, Hair, Bariatric, Aesthetic, IVF services
- **Appointment Scheduling** - Integrated calendar and appointment system
- **Document Management** - Patient document storage and retrieval
- **Communication Hub** - Tickets, messages, feedback management
- **Role-Based Access Control** - Granular permission management
- **Real-time Updates** - WebSocket support for live data
- **Multi-language Support** - Turkish and English interfaces

---

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- SQLite (included)
- Modern web browser

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/mshjiyan-a11y/msh_med_tour.git
cd msh_med_tour
```

2. **Create virtual environment:**
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure environment:**
```bash
cp .env.example .env
# Edit .env with your settings
```

5. **Run the application:**
```bash
python run.py
```

6. **Access the application:**
- Open browser: http://localhost:5000
- Default credentials will be shown in terminal

---

## 📱 Facebook Lead Ads Setup

### For Superadmin

1. Go to Admin Panel → Distributors
2. Select a distributor
3. Scroll to "Facebook Lead Ads Konfigürasyonu"
4. Enter your Meta credentials:
   - **Page ID**: Your Facebook Page ID
   - **Form ID**: Your Lead Form ID
   - **Access Token**: Long-lived access token (60+ days valid)
   - **Sync Interval**: How often to check for new leads (minutes)
5. Click "Kaydet" (Save)
6. Click "Bağlantı Testi" (Test Connection)
7. Click "Şimdi Senkronize Et" (Sync Now)

### Getting Meta Credentials

1. **Page ID & Form ID:**
   - Go to Facebook Ads Manager
   - Select your page and lead form
   - Copy Page ID and Form ID

2. **Access Token:**
   - Go to Meta for Developers: https://developers.facebook.com
   - Create an app or use existing one
   - Generate long-lived access token
   - **Keep it secure!**

---

## 📊 Facebook Leads Management

### Dashboard Overview
- Admin Panel shows real-time lead count
- Quick access to "Facebook Lead Ads" card
- One-click sync and configuration

### Lead Listing
- **URL:** http://localhost:5000/admin/facebook-leads
- **Features:**
  - View all captured leads
  - Filter by status, score, distributor
  - Search by name, email, phone
  - Quality score badges (High/Medium/Low)
  - Lead assignment tracking

### Lead Scoring
- **Automatic scoring** on lead creation
- **5-factor assessment:**
  - Data completeness (20 points)
  - Contact availability (20 points)
  - Form quality (20 points)
  - Timing relevance (20 points)
  - Historical performance (20 points)

**Total: 0-100 points**
- 🟢 70+: High quality
- 🟡 40-70: Medium quality  
- 🔴 0-40: Low quality

### Lead Status Flow
1. **new** - Freshly imported lead
2. **contacted** - Sales team reached out
3. **qualified** - Lead meets requirements
4. **unqualified** - Doesn't meet criteria
5. **converted** - Patient acquired

---

## 🏗️ System Architecture

### Core Components

**Database Models:**
- `User` - System users with roles
- `Distributor` - Healthcare partner organizations
- `Patient` - Patient records
- `FacebookLead` - Meta lead data
- `MetaAPIConfig` - Per-distributor Meta settings
- `LeadInteraction` - Audit trail

**Services:**
- `MetaLeadService` - Meta API integration
- `LeadScoringService` - AI quality assessment
- `BulkOperationsService` - Batch processing
- `LeadNotificationsService` - Email alerts
- `LeadAnalyticsService` - Reporting & insights

**Routes:**
- `/admin/*` - Admin panel
- `/admin/facebook-leads` - Lead management
- `/api/*` - REST API endpoints
- `/auth/*` - Authentication

---

## 🔧 Configuration

### .env File
```
FLASK_ENV=development
SECRET_KEY=your-secret-key-here
DATABASE_URL=sqlite:///app.db

# Facebook/Meta
META_API_VERSION=v18.0

# Email (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Features
ENABLE_HAIR=True
ENABLE_TEETH=True
ENABLE_EYE=True
```

---

## 📚 Documentation

- **[API Reference](API_REFERENCE.md)** - REST API endpoints
- **[Meta Integration Guide](META_LEAD_INTEGRATION_DOCS.md)** - Detailed setup
- **[Advanced Features](FACEBOOK_LEADS_ADVANCED_DOCS.md)** - Scoring, analytics
- **[Architecture](SYSTEM_ARCHITECTURE.md)** - System design
- **[Deployment Guide](DEPLOYMENT_CHECKLIST.md)** - Production setup

---

## 🧪 Testing

### Run tests:
```bash
python -m pytest tests/

# With coverage:
python -m pytest --cov=app tests/
```

### Test Meta Integration:
```bash
python test_meta_integration.py
```

---

## 📦 Project Structure

```
msh_med_tour/
├── app/
│   ├── models/              # Database models
│   ├── routes/              # Flask blueprints
│   ├── services/            # Business logic
│   ├── templates/           # HTML templates
│   ├── static/              # CSS, JS, uploads
│   └── utils/               # Helper functions
├── migrations/              # Database migrations
├── scripts/                 # Setup scripts
├── requirements.txt         # Python dependencies
├── config.py               # Configuration
├── run.py                  # Entry point
└── README.md               # This file
```

---

## 🔐 Security

- Role-Based Access Control (RBAC)
- Password hashing with Werkzeug
- CSRF protection
- SQL injection prevention (SQLAlchemy ORM)
- Secure token management
- API key encryption

### Production Checklist:
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS
- [ ] Set DEBUG=False
- [ ] Use PostgreSQL instead of SQLite
- [ ] Configure CORS properly
- [ ] Enable rate limiting
- [ ] Set up monitoring & logging

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📝 License

This project is licensed under the MIT License - see LICENSE file for details.

---

## 👥 Support

For issues and questions:
- 📧 Email: mshjiyan@gmail.com
- 🐛 Issues: https://github.com/mshjiyan-a11y/msh_med_tour/issues
- 📖 Documentation: See docs/ folder

---

## 🙏 Acknowledgments

- Flask framework
- SQLAlchemy ORM
- Bootstrap CSS framework
- Meta Graph API
- Community contributors

---

**Last Updated:** November 2025
**Maintained by:** Jiyan - Medical Tourism Management System

Comprehensive medical tourism management system with multi-module support (Hair Transplant, Dental, Eye Treatment).

## Features

### Core Features
- ✅ **Multi-Module Support**: Hair transplant, dental, and eye treatment modules
- ✅ **Interactive Visual Interfaces**: Click-to-fill on medical diagrams (32 teeth, hair zones, eye diagrams)
- ✅ **Patient Management**: Full CRUD operations with search and filtering
- ✅ **Encounter Tracking**: Sequential numbering (1. Muayene, 2. Muayene) with module-specific data
- ✅ **PDF Reports**: Generate detailed medical reports with ReportLab
- ✅ **Dashboard Analytics**: Chart.js graphs for module usage and monthly trends
- ✅ **Toast Notifications**: Real-time feedback for all operations
- ✅ **Multi-Language UI**: Turkish, English, Arabic (UI ready, translations pending)

### Lead Management (v2.0.0 Advanced)
- ✅ **Facebook Lead Ads Integration**: Real-time lead capture with automatic sync (5-min intervals)
- ✅ **AI Lead Scoring**: 5-factor scoring system (100-point scale) with priority recommendations
- ✅ **Bulk Operations**: Manage 100+ leads at once (status, assignment, export)
- ✅ **Real-time Updates**: WebSocket-powered real-time dashboard updates
- ✅ **Email Notifications**: Async notifications for new leads, status changes, daily summaries
- ✅ **Advanced Analytics**: Conversion funnel, performance tracking, daily/weekly/monthly reports
- ✅ **Lead Tracking**: Status management (new → assigned → contacted → converted)
- ✅ **Lead to Patient Conversion**: One-click conversion with data preservation

### Security & Multi-Tenancy
- ✅ **Role-Based Access Control**: Admin, Distributor, Doctor, Staff roles
- ✅ **Multi-Tenant Architecture**: Complete data isolation per distributor
- ✅ **API Key Management**: Per-distributor API keys with admin-only controls
- ✅ **Token-Based Authentication**: Secure API access with expiration and usage tracking

## Tech Stack

- **Backend**: Flask 2.3+, SQLAlchemy 2.0+, SQLite/PostgreSQL
- **Authentication**: Flask-Login with role-based access
- **Forms**: Flask-WTF, WTForms
- **PDF Generation**: ReportLab, Pillow
- **Email**: Flask-Mail with async sending
- **Real-time**: Flask-SocketIO for WebSocket updates
- **Scheduling**: APScheduler for background tasks (lead sync)
- **i18n**: Flask-Babel
- **Frontend**: Bootstrap 5.3.0, Font Awesome 6.0.0, jQuery 3.6.0, Chart.js 4.4.0

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup

1. **Clone the repository**
```bash
git clone <repository-url>
cd msh_med_tour
```

2. **Create virtual environment**
```bash
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
copy .env.example .env
# Edit .env with your settings
```

5. **Configure Email (SMTP)**

Edit `.env` file:

```ini
# Gmail Example (Recommended)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=true
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
```

**Gmail Setup:**
1. Go to [Google Account Settings](https://myaccount.google.com/)
2. Enable 2-Step Verification
3. Go to [App Passwords](https://myaccount.google.com/apppasswords)
4. Generate a new app password for "Mail"
5. Copy the 16-character password to `MAIL_PASSWORD`

**Other Providers:**
- **Outlook/Office365**: 
  - Server: `smtp.office365.com`, Port: `587`
- **Yahoo Mail**: 
  - Server: `smtp.mail.yahoo.com`, Port: `587`
- **Custom SMTP**: Use your provider's SMTP settings

6. **Initialize database**
```bash
flask db upgrade
```

7. **Create admin user**
```bash
python create_admin.py
# Follow prompts to create your admin account
```

8. **Run the application**
```bash
python run.py
```

Visit `http://127.0.0.1:5000`

## Usage Guide

### For Administrators

1. **Login** with admin credentials
2. **Create Distributor**: Go to Admin Panel → Add distributor
3. **Generate API Keys**: Admin Panel → API Keys → Create new key
4. **Configure Integrations**: Set Facebook and website API keys per distributor

### For Distributors/Doctors

1. **Add Patient**: Dashboard → "Yeni Hasta Ekle" button
   - Fill patient information (name, phone, email, nationality, passport)
   - Click "Kaydet"

2. **Create Encounter**: Patient Detail → "Yeni Muayene" button
   - Select module (Hair/Dental/Eye)
   - Select encounter date
   - Fill module-specific data using interactive diagrams

3. **Module-Specific Data Entry**:
   - **Hair**: Click on zones, enter graft counts
   - **Dental**: Click on teeth (1-32), select treatment type
   - **Eye**: Select eye (OD/OS), enter refraction values

4. **Generate PDF**: Encounter Detail → "PDF İndir" button

5. **Manage Leads**: Leads → View/Convert/Track status
   - Click lead to view details
   - Add notes and update status
   - Convert to patient when ready

### Facebook Lead Management (v2.0.0)

**Quick Setup (5 minutes):**

1. **Get Meta Credentials**: 
   - Go to business.facebook.com → Create Business Manager
   - Create App → Add Marketing API + Leads products
   - Generate long-lived access token
   - Create Lead Form → Copy Page ID & Form ID

2. **Configure in Admin Panel**:
   ```
   Admin → Distributor Settings → Meta API Configuration
   ├─ Page ID: [paste]
   ├─ Form ID: [paste]  
   ├─ Access Token: [paste]
   ├─ Sync Interval: 5 (minutes)
   └─ Enable: ✓
   ```

3. **Start Syncing**:
   - Click "Test Connection" → Should show ✓ success
   - Click "Sync Now" → Leads appear in dashboard

**Features:**

- **Lead Dashboard**: `Admin → Facebook Leads → Lead'ler`
  - View all leads with filtering (status, distributor, search)
  - Quick actions (assign, change status, add notes)
  - Pagination (25 items/page)

- **Lead Scoring**: `Admin → Facebook Leads → Skor & Öncelik`
  - AI scoring (5 factors, 100-point scale)
  - Score levels: Excellent (80-100), Good (60-79), Medium (40-59), Low (20-39), Very Low (0-19)
  - Top leads & management recommendations

- **Analytics**: `Admin → Facebook Leads → Analytics`
  - Conversion funnel (new → assigned → contacted → converted)
  - Performance by distributor and staff member
  - Response time statistics
  - Generate daily/weekly/monthly reports

- **Bulk Operations**:
  - Change status for 100+ leads at once
  - Assign batch to staff member
  - Delete multiple leads
  - Export as CSV/JSON

**Documentation:**
- **Quick Start** (5 min): [QUICK_START.md](QUICK_START.md)
- **Complete Guide**: [FACEBOOK_LEADS_ADVANCED_DOCS.md](FACEBOOK_LEADS_ADVANCED_DOCS.md)
- **API Reference**: [API_REFERENCE.md](API_REFERENCE.md)
- **Architecture**: [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md)
- **Deployment**: [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)

### API Integration

**Website Form Example:**

```javascript
fetch('https://your-domain.com/api/v1/leads', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key-here'
  },
  body: JSON.stringify({
    source: 'website',
    first_name: 'John',
    last_name: 'Doe',
    email: 'john@example.com',
    phone: '+905551234567',
    interested_service: 'hair_transplant',
    message: 'I want to get information about hair transplant'
  })
})
```

**Facebook Webhook Setup:**

1. Admin Panel → Distributor Integrations
2. Enter Facebook API credentials
3. Set webhook URL: `https://your-domain.com/api/v1/facebook/webhook`
4. Verify token: `msh_med_tour_2025_verify`

## Email Notifications

The system sends automatic email notifications for:

- **New Leads**: When a lead is created via API (sent to distributor)
- **Appointment Reminders**: When encounter has scheduled date (sent to patient)

**Email Configuration Checklist:**
- ✅ SMTP server settings in `.env`
- ✅ Valid email credentials
- ✅ App password (for Gmail) or account password
- ✅ TLS/SSL enabled

**Testing Email:**
```bash
python -c "from app import create_app; from app.utils.email import send_email; app = create_app(); app.app_context().push(); send_email('Test', ['test@example.com'], 'Test body', '<p>Test HTML</p>')"
```

## Database Schema

### Core Tables
- **users**: System users with role-based access
- **distributors**: Multi-tenant organizations
- **patients**: Patient records
- **encounters**: Medical encounters with module type
- **hair_annotations**: Hair transplant zone data
- **dental_procedures**: Dental treatment per tooth
- **eye_refractions**: Eye refraction measurements

### Lead Tables (v2.0.0)
- **metaapiconfig**: Meta/Facebook API credentials per distributor
- **facebooklead**: Lead data from Meta Lead Ads with status tracking
- **leadinteraction**: Audit trail (calls, emails, notes, status changes)

## File Structure

```
msh_med_tour/
├── app/
│   ├── models/          # SQLAlchemy models
│   │   └── meta_lead.py # NEW: MetaAPIConfig, FacebookLead, LeadInteraction
│   ├── routes/          # Flask blueprints
│   │   ├── auth.py      # Authentication routes
│   │   ├── main.py      # Patient & encounter routes
│   │   ├── admin.py     # Admin panel
│   │   ├── leads.py     # LEGACY: Lead management
│   │   ├── facebook_leads.py # NEW: Facebook lead management (20+ routes)
│   │   └── api.py       # API endpoints
│   ├── services/        # Business logic (NEW in v2.0.0)
│   │   ├── meta_lead_service.py         # Meta API integration
│   │   ├── lead_scoring.py              # AI scoring engine
│   │   ├── bulk_operations.py           # Bulk operations
│   │   ├── lead_notifications.py        # Email notifications
│   │   └── lead_analytics.py            # Analytics & reporting
│   ├── events/          # WebSocket events (NEW in v2.0.0)
│   │   └── lead_events.py               # SocketIO handlers
│   ├── templates/       # Jinja2 templates
│   │   ├── base.html    # Base template with navbar & toast
│   │   ├── main/        # Patient & encounter templates
│   │   ├── leads/       # LEGACY: Lead templates
│   │   ├── admin/facebook_leads/ # NEW: Facebook lead templates
│   │   │   ├── index.html               # Lead dashboard
│   │   │   ├── view.html                # Lead detail
│   │   │   ├── scoring_dashboard.html   # Scoring view
│   │   │   └── analytics.html           # Analytics view
│   │   └── admin/       # Admin templates
│   ├── static/          # CSS, JS, images
│   │   ├── css/         # Custom styles
│   │   ├── js/          # Interactive diagrams
│   │   └── uploads/     # User uploads
│   ├── utils/           # Utility modules
│   │   ├── email.py     # Email notifications
│   │   └── meta_scheduler.py # NEW: APScheduler integration
│   └── __init__.py      # App factory
├── migrations/          # Database migrations
├── config.py            # Configuration
├── requirements.txt     # Python dependencies
├── run.py              # Application entry point
├── check_system_health.py # NEW: System health check script
├── test_meta_integration.py # NEW: Facebook integration tests
├── .env                # Environment variables (not in git)
├── QUICK_START.md              # NEW: 5-minute setup guide
├── FACEBOOK_LEADS_ADVANCED_DOCS.md # NEW: Complete documentation
├── API_REFERENCE.md            # NEW: API documentation  
├── SYSTEM_ARCHITECTURE.md      # NEW: Technical architecture
└── DEPLOYMENT_CHECKLIST.md     # NEW: Production deployment guide
```

## Troubleshooting

### Email Not Sending

**Problem**: Emails not being sent to users

**Solutions**:
1. Check `.env` has valid SMTP credentials
2. For Gmail: Ensure App Password is used (not regular password)
3. Check firewall allows outbound port 587
4. Test with: `python -c "from app.utils.email import send_email; ..."`
5. Check terminal output for error messages

### Database Errors

**Problem**: Database locked or migration errors

**Solutions**:
```bash
# Reset database (WARNING: Deletes all data)
rm app.db
flask db upgrade
python create_admin.py
```

### Import Errors

**Problem**: Module import errors on startup

**Solutions**:
```bash
# Reinstall dependencies
pip install --upgrade -r requirements.txt

# Check Python version
python --version  # Should be 3.8+
```

## Development

### Running in Development Mode

```bash
# Enable debug mode
set FLASK_ENV=development  # Windows
export FLASK_ENV=development  # Linux/Mac

python run.py
```

### Creating Database Migrations

```bash
# After model changes
flask db migrate -m "Description of changes"
flask db upgrade
```

### Adding New Modules

1. Create model in `app/models/`
2. Add routes in `app/routes/main.py`
3. Create template in `app/templates/main/`
4. Add interactive diagram in `app/static/js/`
5. Run migration: `flask db migrate`

## Production Deployment

### Security Checklist
- [ ] Change `SECRET_KEY` in `.env`
- [ ] Use PostgreSQL/MySQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Set `FLASK_ENV=production`
- [ ] Use Gunicorn or uWSGI
- [ ] Set up nginx reverse proxy
- [ ] Enable database backups
- [ ] Configure firewall rules
- [ ] Use secure SMTP (port 465 with SSL)

### Deployment Example (Linux)

```bash
# Install Gunicorn
pip install gunicorn

# Run with Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 run:app

# Or with systemd service
sudo nano /etc/systemd/system/msh_med_tour.service
sudo systemctl start msh_med_tour
sudo systemctl enable msh_med_tour
```

**For Facebook Lead Integration deployment, see [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md)**

## License

Proprietary - All rights reserved

## Support

For issues or questions:
- Check troubleshooting section above
- Review help text in the application (every page has usage tips)
- Run health check: `python check_system_health.py`
- Contact system administrator

---

## Documentation

**v2.0.0 Facebook Lead Integration Documentation:**

| Document | Purpose | Audience |
|----------|---------|----------|
| [QUICK_START.md](QUICK_START.md) | 5-minute setup guide | Everyone |
| [FACEBOOK_LEADS_ADVANCED_DOCS.md](FACEBOOK_LEADS_ADVANCED_DOCS.md) | Complete features & usage | Admins |
| [API_REFERENCE.md](API_REFERENCE.md) | All API endpoints | Developers |
| [SYSTEM_ARCHITECTURE.md](SYSTEM_ARCHITECTURE.md) | Technical design | Developers |
| [DEPLOYMENT_CHECKLIST.md](DEPLOYMENT_CHECKLIST.md) | Production deployment | DevOps |

**System Health Check:**
```bash
python check_system_health.py
# Verifies all components, dependencies, database, templates
```

---

**Version**: 2.0.0 Advanced (Facebook Lead Integration)  
**Core Version**: 1.0.0 (Medical Tourism System)  
**Last Updated**: 2025-01-21  
**Status**: Production Ready ✓
