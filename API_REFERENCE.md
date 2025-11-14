# API Reference - Facebook Lead Integration

**Version:** 2.0.0 Advanced  
**Base URL:** `http://localhost:5000/admin/facebook-leads`  
**Authentication:** Superadmin only

---

## Table of Contents

1. [Dashboard Routes](#dashboard-routes)
2. [Management Routes](#management-routes)
3. [Bulk Operations](#bulk-operations)
4. [Analytics Routes](#analytics-routes)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Events](#websocket-events)
7. [Error Handling](#error-handling)

---

## Dashboard Routes

### GET / - Lead Dashboard
**Description:** Display all leads with filtering and pagination

**URL:** `GET /admin/facebook-leads/`

**Query Parameters:**
```
page=1              # Page number (default: 1)
status=new          # Filter by status (new|assigned|contacted|converted|rejected)
distributor_id=1    # Filter by distributor
search=John         # Search in name/email/phone
per_page=25         # Items per page (default: 25)
```

**Response:** HTML page with lead table and statistics

**Example:**
```bash
curl "http://localhost:5000/admin/facebook-leads/?status=new&page=1"
```

---

### GET /<id> - Lead Detail View
**Description:** View single lead with all details and interactions

**URL:** `GET /admin/facebook-leads/<id>`

**Parameters:**
```
id (integer)  # Lead ID
```

**Response:** HTML page with lead details, interactions, and management forms

**Example:**
```bash
curl http://localhost:5000/admin/facebook-leads/1
```

---

## Management Routes

### POST /<id>/status - Update Lead Status
**Description:** Change lead status

**URL:** `POST /admin/facebook-leads/<id>/status`

**Request Body:**
```json
{
  "status": "contacted"
}
```

**Status Options:**
- `new` - New lead
- `assigned` - Assigned to staff
- `contacted` - Staff has contacted
- `converted` - Became patient/customer
- `rejected` - Not interested

**Response:**
```json
{
  "success": true,
  "message": "Status updated successfully",
  "lead": {
    "id": 1,
    "status": "contacted",
    "updated_at": "2025-01-21T10:30:00"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/admin/facebook-leads/1/status \
  -H "Content-Type: application/json" \
  -d '{"status": "contacted"}'
```

---

### POST /<id>/assign - Assign Lead to Staff
**Description:** Assign lead to specific staff member

**URL:** `POST /admin/facebook-leads/<id>/assign`

**Request Body:**
```json
{
  "user_id": 5
}
```

**Response:**
```json
{
  "success": true,
  "message": "Lead assigned successfully",
  "lead": {
    "id": 1,
    "assigned_to": "drbulentkose",
    "status": "assigned"
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:5000/admin/facebook-leads/1/assign \
  -H "Content-Type: application/json" \
  -d '{"user_id": 5}'
```

---

### POST /<id>/note - Add Interaction Note
**Description:** Add note/comment to lead interaction history

**URL:** `POST /admin/facebook-leads/<id>/note`

**Request Body:**
```json
{
  "note": "Customer called, interested in eye surgery",
  "interaction_type": "called"
}
```

**Interaction Types:**
- `called` - Phone call
- `emailed` - Email sent
- `sms` - SMS sent
- `note` - General note
- `status_changed` - Status changed

**Response:**
```json
{
  "success": true,
  "message": "Note added successfully",
  "interaction": {
    "id": 42,
    "lead_id": 1,
    "interaction_type": "called",
    "description": "Customer called, interested in eye surgery",
    "created_at": "2025-01-21T10:35:00"
  }
}
```

---

### POST /<id>/delete - Delete Lead
**Description:** Soft delete a lead

**URL:** `POST /admin/facebook-leads/<id>/delete`

**Response:**
```json
{
  "success": true,
  "message": "Lead deleted successfully"
}
```

---

## Bulk Operations

### POST /bulk/status - Bulk Status Change
**Description:** Change status for multiple leads

**URL:** `POST /admin/facebook-leads/bulk/status`

**Request Body:**
```json
{
  "lead_ids": [1, 2, 3, 4, 5],
  "new_status": "contacted"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Status updated for 5 leads",
  "updated": 5,
  "errors": []
}
```

---

### POST /bulk/assign - Bulk Assignment
**Description:** Assign multiple leads to a staff member

**URL:** `POST /admin/facebook-leads/bulk/assign`

**Request Body:**
```json
{
  "lead_ids": [1, 2, 3, 4, 5],
  "assign_to_user_id": 7
}
```

**Response:**
```json
{
  "success": true,
  "message": "Assigned 5 leads to drbulentkose",
  "updated": 5,
  "errors": []
}
```

---

### POST /bulk/delete - Bulk Delete
**Description:** Delete multiple leads

**URL:** `POST /admin/facebook-leads/bulk/delete`

**Request Body:**
```json
{
  "lead_ids": [1, 2, 3]
}
```

**Response:**
```json
{
  "success": true,
  "message": "Deleted 3 leads",
  "updated": 3,
  "errors": []
}
```

---

### POST /bulk/export - Export Leads
**Description:** Export leads in CSV or JSON format

**URL:** `POST /admin/facebook-leads/bulk/export`

**Request Body:**
```json
{
  "lead_ids": [1, 2, 3, 4, 5],
  "format": "csv"
}
```

**Format Options:** `csv` or `json`

**Response:** File download
- CSV: `leads_2025-01-21_103500.csv`
- JSON: `leads_2025-01-21_103500.json`

---

## Analytics Routes

### GET /analytics - Analytics Dashboard
**Description:** Display comprehensive analytics dashboard

**URL:** `GET /admin/facebook-leads/analytics`

**Response:** HTML page with:
- Conversion funnel (new → assigned → contacted → converted)
- Performance by distributor
- Performance by staff member
- Response time statistics
- Interaction type breakdown

---

### GET /analytics/report - Generate Report
**Description:** Generate and download analytics report

**URL:** `GET /admin/facebook-leads/analytics/report?type=monthly&format=json`

**Query Parameters:**
```
type=monthly      # Report type: daily|weekly|monthly (default: monthly)
format=json       # Format: json|html (default: json)
```

**JSON Response:**
```json
{
  "generated_at": "2025-01-21T10:40:00",
  "period": "monthly",
  "funnel": {
    "statuses": {
      "new": 150,
      "assigned": 120,
      "contacted": 95,
      "converted": 28,
      "rejected": 67
    },
    "conversion_rates": {
      "to_assigned": "80.0%",
      "to_contacted": "79.2%",
      "to_converted": "29.5%"
    }
  },
  "daily_stats": [
    {
      "date": "2025-01-21",
      "total": 42,
      "conversion_rate": "28.5%"
    }
  ],
  "by_distributor": [
    {
      "name": "MSH Med Tour",
      "total": 150,
      "converted": 28,
      "conversion_rate": "18.7%"
    }
  ],
  "by_user": [
    {
      "username": "drbulentkose",
      "assigned_count": 85,
      "contacted_count": 68,
      "conversion_rate": "32.9%"
    }
  ],
  "interactions": {
    "called": {"count": 245, "success": 210, "failed": 35},
    "emailed": {"count": 128, "success": 128, "failed": 0}
  },
  "response_time": {
    "average_hours": 4.5,
    "min_hours": 0.1,
    "max_hours": 72.0
  }
}
```

---

### GET /scoring-dashboard - Scoring Dashboard
**Description:** Display lead scoring dashboard

**URL:** `GET /admin/facebook-leads/scoring-dashboard`

**Response:** HTML page with:
- Score distribution (5 levels)
- Top 20 leads by score
- AI recommendations
- Scoring methodology

---

## API Endpoints

### GET /api/stats - Lead Statistics
**Description:** Get JSON statistics of all leads

**URL:** `GET /admin/facebook-leads/api/stats`

**Response:**
```json
{
  "total": 150,
  "new": 30,
  "assigned": 95,
  "contacted": 68,
  "converted": 28,
  "rejected": 22,
  "conversion_rate": "18.7%"
}
```

---

### GET /api/recent - Recent Leads
**Description:** Get most recent leads

**URL:** `GET /admin/facebook-leads/api/recent?limit=10`

**Query Parameters:**
```
limit=10  # Number of leads to return (default: 10)
```

**Response:**
```json
{
  "leads": [
    {
      "id": 150,
      "first_name": "Fatma",
      "last_name": "Çetin",
      "email": "fatma@example.com",
      "phone": "+905559876543",
      "status": "new",
      "created_at": "2025-01-21T10:45:00",
      "score": 85
    }
  ]
}
```

---

### GET /api/scoring - Lead Scores
**Description:** Get scoring data for all leads

**URL:** `GET /admin/facebook-leads/api/scoring`

**Response:**
```json
{
  "leads": [
    {
      "id": 1,
      "first_name": "Ahmet",
      "last_name": "Kaya",
      "score": 92,
      "level": "excellent",
      "color": "green",
      "factors": {
        "contact_info": 30,
        "freshness": 20,
        "service_indicated": 25,
        "engagement": 15,
        "lead_age": 2
      }
    }
  ],
  "statistics": {
    "average_score": 65.3,
    "high_quality_count": 42,
    "excellent_count": 8
  }
}
```

---

### POST /config/<id>/test - Test Meta API Connection
**Description:** Test connection to Meta/Facebook API

**URL:** `POST /admin/facebook-leads/config/<id>/test`

**Response:**
```json
{
  "success": true,
  "message": "Connection successful",
  "details": {
    "page_name": "MSH Medical Center",
    "form_name": "Lead Form",
    "leads_available": 25
  }
}
```

---

### POST /config/<id>/sync - Manual Lead Sync
**Description:** Manually trigger lead synchronization

**URL:** `POST /admin/facebook-leads/config/<id>/sync`

**Response:**
```json
{
  "success": true,
  "message": "Sync successful",
  "details": {
    "total_fetched": 12,
    "new_leads": 8,
    "updated_leads": 4,
    "duplicates_skipped": 0
  }
}
```

---

## WebSocket Events

**Namespace:** `/facebook-leads`

### Emit Events (Client → Server)

#### connect
```javascript
// Automatically emitted on connection
socket.on('connect', () => {
  console.log('Connected to WebSocket');
});
```

#### join_lead
```javascript
// Subscribe to specific lead updates
socket.emit('join_lead', {lead_id: 123}, (response) => {
  console.log('Joined lead room:', response);
});
```

#### leave_lead
```javascript
// Unsubscribe from specific lead
socket.emit('leave_lead', {lead_id: 123});
```

### Receive Events (Server → Client)

#### connected
```javascript
socket.on('connected', (data) => {
  console.log('Authentication confirmed:', data);
  // {username: 'drbulentkose', timestamp: '2025-01-21T10:50:00'}
});
```

#### lead_updated
```javascript
socket.on('lead_updated', (data) => {
  console.log('Lead updated:', data);
  // {
  //   lead_id: 1,
  //   event_type: 'status_changed',
  //   data: {old_status: 'new', new_status: 'contacted'},
  //   timestamp: '2025-01-21T10:50:30'
  // }
});
```

#### lead_created
```javascript
socket.on('lead_created', (data) => {
  console.log('New lead:', data);
  // {
  //   id: 1,
  //   first_name: 'Ahmet',
  //   email: 'ahmet@example.com',
  //   score: 85
  // }
});
```

#### stats_updated
```javascript
socket.on('stats_updated', (data) => {
  console.log('Stats updated:', data);
  // {
  //   total: 150,
  //   new: 25,
  //   assigned: 95,
  //   contacted: 68,
  //   converted: 28
  // }
});
```

---

## Error Handling

### HTTP Error Responses

**400 Bad Request**
```json
{
  "error": "Invalid request",
  "message": "Lead ID is required"
}
```

**401 Unauthorized**
```json
{
  "error": "Unauthorized",
  "message": "Superadmin access required"
}
```

**404 Not Found**
```json
{
  "error": "Not found",
  "message": "Lead with ID 999 not found"
}
```

**500 Internal Server Error**
```json
{
  "error": "Server error",
  "message": "An unexpected error occurred"
}
```

### Common Error Scenarios

**Scenario:** Duplicate lead detection
```json
{
  "success": false,
  "message": "Lead already exists (meta_lead_id: 123456789)"
}
```

**Scenario:** Invalid Meta API configuration
```json
{
  "success": false,
  "message": "Invalid API credentials",
  "details": "Access token expired"
}
```

**Scenario:** Lead not assigned
```json
{
  "success": false,
  "message": "Cannot update status - lead not assigned"
}
```

---

## Rate Limiting

**Limits per IP:**
- API Calls: 1000 requests/hour
- Bulk Operations: 100 operations/hour
- Dashboard: Unlimited

**Headers Returned:**
```
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 950
X-RateLimit-Reset: 1705849200
```

---

## Authentication

**Type:** Session-based (Superadmin only)

**Headers Required:**
```
Cookie: session=xxxxxxxxxxxxx
X-Requested-With: XMLHttpRequest (for AJAX)
```

---

## Pagination

**Default:** 25 items per page

**Query Parameters:**
```
page=1          # Page number (1-indexed)
per_page=50     # Items per page
sort=created_at # Sort field
order=desc      # Sort order (asc|desc)
```

---

## Filtering

**Supported Filters:**
```
status=new              # By status
distributor_id=1        # By distributor
assigned_to_id=5        # By assignee
score_min=60            # Score range
score_max=100
created_after=2025-01-01     # Date range
created_before=2025-01-31
search=John             # Full-text search
```

---

## Date/Time Format

**Format:** ISO 8601 UTC
```
2025-01-21T10:30:00Z
```

---

**Version:** 2.0.0 Advanced  
**Last Updated:** 2025-01-21  
**Status:** Complete ✓
