# Setup & Installation Guide

## 📋 Prerequisites

- **Python 3.8 or higher** - Download from https://www.python.org/downloads/
- **Git** - Download from https://git-scm.com/download
- **Facebook/Meta Account** - For Lead Ads integration
- **Modern Browser** - Chrome, Firefox, Safari, Edge (latest versions)

---

## 🔧 Installation Steps

### Step 1: Clone Repository

```bash
git clone https://github.com/mshjiyan-a11y/msh_med_tour.git
cd msh_med_tour
```

### Step 2: Create Virtual Environment

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**macOS/Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### Step 3: Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 4: Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Windows: notepad .env
# macOS/Linux: nano .env
```

**Essential .env variables:**
```
FLASK_ENV=development
SECRET_KEY=your-very-secret-key-generate-one
DATABASE_URL=sqlite:///app.db
```

### Step 5: Initialize Database

```bash
# Create database and run migrations
flask db upgrade

# Or if migrations don't exist:
flask db init
flask db migrate -m "Initial migration"
flask db upgrade
```

### Step 6: Create Superadmin User

```bash
python scripts/create_superadmin.py
```

**Follow the prompts:**
- Email: drbulentkose@example.com (or your choice)
- Password: Create strong password
- Name: Your name

### Step 7: Run Application

```bash
python run.py
```

**Output should show:**
```
* Running on http://127.0.0.1:5000
* Press CTRL+C to quit
```

### Step 8: Access Application

Open browser and go to: **http://localhost:5000**

Login with superadmin credentials created in Step 6.

---

## 📱 Facebook Lead Ads Setup

### Prerequisite: Get Meta Credentials

1. **Go to Meta for Developers:**
   - Visit https://developers.facebook.com
   - Create or select app

2. **Get Page ID:**
   - Go to Facebook Ads Manager
   - Select your business page
   - Find Page ID in page settings

3. **Get Lead Form ID:**
   - In Ads Manager, select Lead Form
   - Copy Form ID from form settings

4. **Generate Access Token:**
   - In Meta Developers > Settings > Tools
   - Generate "System User" token with:
     - `leads_retrieval` permission
     - `pages_read_engagement` permission
   - Token must be "long-lived" (60+ days valid)
   - **Never share this token!**

### Configure in Application

1. **Log in as Superadmin**
   - Go to http://localhost:5000/admin

2. **Select a Distributor**
   - Click on distributor name in list
   - Scroll to bottom of page

3. **Fill Meta Configuration**
   - **Page ID**: Paste your Facebook Page ID
   - **Form ID**: Paste your Lead Form ID
   - **Access Token**: Paste your generated token
   - **Sync Interval**: 5-1440 minutes (default: 5)
   - **Enable Checkbox**: Mark as active

4. **Test Connection**
   - Click "Bağlantı Testi" (Test Connection)
   - Should show "✓ Bağlantı başarılı!"

5. **Sync Leads**
   - Click "Şimdi Senkronize Et" (Sync Now)
   - Existing leads will be imported

---

## 🐛 Troubleshooting

### Issue: "Module not found" error
**Solution:**
```bash
pip install -r requirements.txt
# Verify installation
pip list | grep flask
```

### Issue: Database locked error
**Solution:**
```bash
# Delete old database and recreate
rm app.db
python run.py
```

### Issue: Port 5000 already in use
**Solution:**
```bash
# Use different port
export FLASK_PORT=5001
python run.py

# Or: Kill process using port 5000
# Windows: netstat -ano | findstr :5000
# macOS/Linux: lsof -i :5000
```

### Issue: Meta connection fails
**Solution:**
1. Verify access token is valid (hasn't expired)
2. Confirm Page ID and Form ID are correct
3. Check Meta API status: https://developers.facebook.com/status
4. Ensure token has correct permissions
5. Check firewall/proxy settings

### Issue: Login not working
**Solution:**
```bash
# Reset superadmin user
python scripts/create_superadmin.py

# Clear session/cookies in browser
# Ctrl+Shift+Delete (most browsers)
```

---

## 🚀 Running in Production

### Pre-Production Checklist

- [ ] Change `FLASK_ENV` to `production`
- [ ] Set strong `SECRET_KEY`
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Configure proper logging
- [ ] Set up email backend
- [ ] Enable rate limiting
- [ ] Configure CORS
- [ ] Set up backups
- [ ] Configure monitoring

### Deployment Options

**Option 1: Using Gunicorn**
```bash
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

**Option 2: Using Docker**
```bash
docker build -t msh_med_tour .
docker run -p 5000:5000 msh_med_tour
```

**Option 3: Using Heroku**
```bash
heroku create your-app-name
git push heroku main
heroku config:set FLASK_ENV=production
heroku config:set SECRET_KEY=your-secret
```

**Option 4: Using AWS/DigitalOcean/Linode**
- Deploy to Ubuntu/CentOS server
- Use Nginx as reverse proxy
- Use Supervisor for process management
- Configure SSL certificate

---

## 📦 Project Structure

```
msh_med_tour/
├── app/
│   ├── __init__.py           # Flask app initialization
│   ├── models/               # Database models
│   │   ├── user.py
│   │   ├── distributor.py
│   │   ├── patient.py
│   │   └── meta_lead.py      # Facebook Lead models
│   ├── routes/               # Flask blueprints
│   │   ├── admin.py
│   │   ├── auth.py
│   │   └── facebook_leads.py
│   ├── services/             # Business logic
│   │   ├── meta_lead_service.py
│   │   ├── lead_scoring.py
│   │   └── lead_analytics.py
│   ├── templates/            # Jinja2 templates
│   │   ├── base.html
│   │   └── admin/
│   ├── static/               # CSS, JS, images
│   └── utils/                # Helper functions
├── migrations/               # Database migrations
├── scripts/                  # Setup scripts
│   └── create_superadmin.py
├── config.py                 # Flask configuration
├── requirements.txt          # Python dependencies
├── run.py                    # Entry point
├── .env.example              # Environment template
├── .gitignore               # Git ignore rules
└── README.md                # Project documentation
```

---

## 🧪 Testing

### Run All Tests
```bash
python -m pytest
```

### Run Specific Test
```bash
python -m pytest tests/test_auth.py
```

### Test Meta Integration
```bash
python test_meta_integration.py
```

### Generate Coverage Report
```bash
python -m pytest --cov=app tests/
```

---

## 📚 Additional Resources

- **Flask Documentation:** https://flask.palletsprojects.com/
- **SQLAlchemy ORM:** https://docs.sqlalchemy.org/
- **Bootstrap CSS:** https://getbootstrap.com/docs/5.3/
- **Meta Graph API:** https://developers.facebook.com/docs/graph-api/
- **Python Best Practices:** https://pep8.org/

---

## 🆘 Getting Help

1. **Check documentation:** See README.md and other .md files
2. **Search issues:** https://github.com/mshjiyan-a11y/msh_med_tour/issues
3. **Create new issue:** Describe problem with steps to reproduce
4. **Email support:** mshjiyan@gmail.com

---

## ✅ Verification Checklist

After installation, verify:

- [ ] Application runs without errors
- [ ] Can log in with superadmin account
- [ ] Admin dashboard loads
- [ ] Can access distributor list
- [ ] Can see Facebook Lead Ads section
- [ ] Can test Meta connection
- [ ] Can see lead list page
- [ ] Database queries work
- [ ] No console errors

If all checks pass, you're ready to use MSH Med Tour! 🎉

---

**Last Updated:** November 14, 2025  
**Maintained by:** Jiyan
