# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [2.0.0] - 2025-11-14

### ✨ Added
- **Facebook Lead Ads Integration** - Complete Meta/Facebook Lead Ads support
  - Real-time lead capture from Meta Lead Forms
  - Per-distributor Meta API configuration
  - Automatic lead syncing (configurable intervals)
  - Lead quality scoring with AI assessment
  - Lead status tracking and management

- **Lead Management Features**
  - Lead listing with filtering and search
  - Lead quality scoring (0-100 points)
  - Lead status workflow (new → qualified → converted)
  - Lead assignment to sales team members
  - Bulk operations support
  - Lead interaction audit trail

- **Admin Dashboard Enhancements**
  - Real-time Facebook lead count widget
  - Quick access to lead management
  - Distributor-specific Meta configuration
  - Connection testing interface
  - Manual sync triggers

- **Database Models**
  - `MetaAPIConfig` - Store per-distributor Meta credentials
  - `FacebookLead` - Lead records from Meta
  - `LeadInteraction` - Audit trail for lead activities

- **Services**
  - `MetaLeadService` - Meta API integration
  - `LeadScoringService` - Quality scoring engine
  - `BulkOperationsService` - Batch lead processing
  - `LeadNotificationsService` - Email alerts
  - `LeadAnalyticsService` - Reporting & insights

- **API Endpoints**
  - `POST /admin/distributor_settings/<id>` - Save Meta config
  - `POST /admin/test-meta-connection/<distributor_id>` - Test connection
  - `POST /admin/sync-meta-leads/<distributor_id>` - Manual sync
  - `GET /admin/facebook-leads` - List all leads

- **Templates**
  - `admin/distributor_detail.html` - Integrated Meta config form
  - `admin/facebook_leads/index.html` - Lead listing page
  - `admin/facebook_leads/scoring_dashboard.html` - Score visualization
  - `admin/facebook_leads/analytics.html` - Analytics dashboard

### 🔧 Changed
- Updated admin dashboard with lead statistics
- Enhanced distributor detail page with Meta configuration
- Improved template inheritance and base layout
- Optimized database queries for lead filtering

### 🐛 Fixed
- Fixed route aliasing for distributor settings page
- Corrected template inheritance issues
- Resolved form action routing
- Fixed nested form structure in templates

### 📚 Documentation
- Created comprehensive README.md with setup guide
- Added Facebook Lead Ads setup instructions
- Documented lead scoring algorithm
- Provided Meta credentials acquisition guide
- Added system architecture documentation

### 🔒 Security
- Secure access token storage
- Role-based access control for lead management
- CSRF protection on configuration forms
- Encrypted password fields for tokens

---

## [1.9.0] - 2025-10-30

### ✨ Added
- Patient journey coordination system
- Hotel reservation management
- Multi-language message support
- Enhanced audit logging

### 🔧 Changed
- Improved appointment scheduling UI
- Optimized patient search performance
- Better error handling in forms

### 🐛 Fixed
- Fixed eye module data associations
- Corrected distributor clinic relationships
- Resolved authentication edge cases

---

## [1.8.0] - 2025-10-15

### ✨ Added
- Role-Based Access Control (RBAC) system
- Notification management
- Document upload functionality
- Quote approval workflow

### 🔧 Changed
- Reorganized database schema for better scalability
- Improved form validation across modules

### 🐛 Fixed
- Fixed currency conversion calculations
- Resolved PDF generation issues

---

## [1.7.0] - 2025-09-20

### ✨ Added
- Communication hub with tickets and messages
- Feedback management system
- Currency support and pricing configuration
- Patient document portal

### 🔧 Changed
- Enhanced appointment calendar interface
- Improved patient dashboard

---

## [1.6.0] - 2025-08-10

### ✨ Added
- Hair treatment module
- Bariatric surgery module
- Aesthetic procedures module
- IVF treatment module
- Checkup module

### 🔧 Changed
- Extended encounter documentation
- Added medical specialization tracking

---

## [1.5.0] - 2025-07-05

### ✨ Added
- Eye care module with detailed tracking
- Dental service module
- Hotel reservation system

### 🐛 Fixed
- Improved database migration process

---

## [1.4.0] - 2025-06-01

### ✨ Added
- Patient journey management
- Journey step coordination
- Multi-step encounter tracking

---

## [1.3.0] - 2025-05-10

### ✨ Added
- Basic appointment system
- Appointment calendar view
- Clinic management

---

## [1.2.0] - 2025-04-15

### ✨ Added
- Enhanced patient profile
- Appointment scheduling
- Patient search functionality

---

## [1.1.0] - 2025-03-20

### ✨ Added
- User authentication system
- Role-based access
- Admin panel basics

---

## [1.0.0] - 2025-02-01

### ✨ Added
- Initial project setup
- Core database models
  - User and authentication
  - Distributor and organization
  - Patient records
  - Encounter documentation
- Basic Flask application structure
- Bootstrap responsive design
- Patient management dashboard

---

## Upcoming Features 🚀

- [ ] Advanced analytics dashboard
- [ ] Email notification system
- [ ] Lead scoring UI improvements
- [ ] Bulk lead operations interface
- [ ] CRM integration
- [ ] Mobile app support
- [ ] Advanced reporting
- [ ] Machine learning lead prediction
- [ ] WhatsApp integration
- [ ] Automated follow-up workflows

---

## How to Contribute

Please see [CONTRIBUTING.md](CONTRIBUTING.md) for details on how to contribute to this project.

---

**Maintainer:** Jiyan  
**Repository:** https://github.com/mshjiyan-a11y/msh_med_tour  
**Last Updated:** November 14, 2025
