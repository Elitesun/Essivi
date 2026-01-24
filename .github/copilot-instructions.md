# ESSIVI Water Distribution System - Backend AI Coding Instructions

## 📋 **Project Overview**
**Business**: Water distribution company using tricycles to deliver water sachets to intermediate points  
**Goal**: Modernize reporting and delivery tracking with mobile apps + web admin platform  
**Your Focus**: Django REST API backend only  
**Tech Stack**: Django 6.0.1, DRF, PostgreSQL, JWT Auth, Poetry (Python >=3.13)

---

## 🏗️ **System Architecture**
```
Mobile Apps (Agents/Clients) ↔ Django REST API ↔ PostgreSQL Database
Web Admin (Next.js) ↔ Django REST API ↔ PostgreSQL Database
```

**API Requirements**:
- RESTful JSON API 
- JWT token authentication with refresh tokens
- HTTPS mandatory, bcrypt password hashing
- Role-based access control (RBAC) for all endpoints
- API rate limiting + CORS configuration

---

## 📁 **Backend Folder Structure**
```
essivivi_backend/
├── Essivi/                 # Main project config (settings, URLs, WSGI/ASGI)
├── accounts/               # User auth, email verification, profiles
├── agents/                 # Commercial agents (delivery personnel) models & views
├── clients/                # Clients/retail points models & views
├── deliveries/             # Delivery tracking with GPS validation
├── orders/                 # Client orders and scheduling
├── admin_platform/         # Admin-specific views & functionality
├── analytics/              # Statistics, reports, KPI calculations
├── notifications/          # Email notifications (NO SMS)
├── core/                   # Shared models, utilities, validators
├── manage.py               # Django CLI entry point
└── pyproject.toml          # Poetry dependencies (Django 6.0.1)
```

---

## 🔐 **Authentication & Authorization**

### **Critical Rules**
1. **Email Verification ONLY** - No SMS verification
2. **Phone numbers stored** but NOT used for authentication
3. **Three user types**: Agents, Clients, Admin Users
4. **Session persistence** with auto-logout (5 minutes configurable)
5. **2FA required** for agents and admin (email-based OTP)

### **JWT Implementation**
- Use `djangorestframework-simplejwt` for token management
- Token includes user type and permissions
- Refresh token rotation on each refresh
- Short expiry (15 min access, 24h refresh)

### **Reference Documentation**
📖 For detailed authentication library configuration (dj-rest-auth 5.0.1), see [docs/auth.json](docs/auth.json)  
📖 For accounts app implementation details, see [docs/accounts.md](docs/accounts.md)

---

## 📊 **Core Data Models & Business Logic**

### **Agent Model** (Delivery Personnel)
```python
- agent_id: CharField (auto-generated, unique)
- name, phone, email, address
- assigned_tricycle: ForeignKey to Tricycle
- profile_photo: ImageField
- hire_date, status (active/inactive/on_delivery)
- gps_tracking_enabled: BooleanField
- performance_metrics: (calculated from Deliveries)
```

### **Client Model** (Retail Points)
```python
- client_code: CharField (auto-generated, unique)
- business_name, manager_name, phone, email
- address_full, gps_coordinates (required for delivery)
- client_type: CHOICES (retailer, wholesaler, institution)
- business_photo: ImageField
- registration_date, status (active/inactive)
```

### **Delivery Model** (Core Business Logic - NEVER DELETE)
```python
- delivery_id: AutoField (unique)
- agent: ForeignKey(Agent)
- client: ForeignKey(Client)
- quantity: PositiveIntegerField (water sachets)
- amount: DecimalField (CFA francs)
- gps_coordinates: PointField (auto-captured)
- proximity_validated: BooleanField (2-meter check - optional)
- delivery_photo: ImageField (optional)
- client_signature: ImageField (optional)
- timestamp: DateTimeField (auto)
- status: pending, completed, failed
- offline_queued: BooleanField (for mobile sync)

CRITICAL: NO SOFT DELETE - use status changes only. Audit trail required.
```

### **Order Model** (Client Requests)
```python
- order_id: AutoField
- client: ForeignKey(Client)
- agent: ForeignKey(Agent, null=True)  # assigned after acceptance
- quantity_requested: PositiveIntegerField
- status: pending → accepted → in_delivery → delivered → cancelled
- preferred_delivery_datetime: DateTimeField
- special_instructions: TextField
- created_at, updated_at: DateTimeField
```

---

## ✅ **Delivery Validation Rules**

```python
# Business logic constraints
1. Agent must have status="on_delivery" to start tour
2. Delivery requires: agent, client, quantity > 0, amount > 0, gps_coords
3. GPS coordinates automatically captured from mobile app
4. 2-meter proximity validation (configurable on/off per agent)
5. Offline deliveries queued with retry mechanism
6. All financial records immutable - status changes only
7. Audit log for every delivery modification
```

---

## 📈 **Reporting & Analytics Requirements**

### **Real-time Admin Dashboard**
- Active agents count + map with live locations
- Today's delivery count + total amount collected (CFA)
- Orders pending acceptance

### **Agent Performance Metrics**
- Deliveries count, total quantity, total amount
- Punctuality rate, avg delivery time
- Response time to order assignments

### **Client Analytics**
- Purchase frequency, average basket size
- Total spent, last delivery date
- Geographic zones

### **Financial Reports** (Excel/PDF)
- Daily/weekly/monthly revenue
- Agent commission calculations
- Client payment status
- Email scheduled exports

### **Geographic Heatmaps**
- Delivery density by zone
- Agent coverage areas
- Pending orders by location

---

## 👥 **Admin Access**

### **Super Admin Features** (Full system access)
- Interactive map: Real-time agent tracking (Leaflet/Google Maps)
- Bulk import/export: Agents, clients, deliveries (CSV/Excel)
- Audit logs: All actions timestamped with user info
- 2FA for admin login (email OTP)

---

## 🚀 **Development Workflow**

### **Command Reference**
```bash
# Start dev server
poetry run py manage.py runserver

# Create migrations after model changes
poetry run py manage.py makemigrations

# Apply migrations
poetry run py manage.py migrate

# Create superuser
poetry run py manage.py createsuperuser

# Create new app
poetry run py manage.py startapp <app_name>

# Django shell
poetry run py manage.py shell

# Add dependency
poetry add <package-name>
```

### **App Registration**
Add all new apps to `INSTALLED_APPS` in [Essivi/settings.py](Essivi/settings.py):
```python
INSTALLED_APPS = [
    # Django defaults...
    'rest_framework',
    'rest_framework_simplejwt',
    'corsheaders',
    'django_filters',
    
    # Custom apps
    'accounts',
    'agents',
    'clients',
    'deliveries',
    'orders',
    'admin_platform',
    'analytics',
    'notifications',
    'core',
]
```

---

## 🔒 **Data Integrity & Security**

### **Critical Constraints**
1. **No deletion** of deliveries/orders/financial records (use status changes)
2. **Audit trail** for all modifications (who, what, when)
3. **Unique constraints**: agent_id, client_code, delivery_id
4. **Referential integrity** via Django ORM
5. **Password hashing**: bcrypt with Django's default
6. **API rate limiting**: Prevent abuse
7. **CORS configuration**: Mobile and Next.js domains only

---

## 📦 **API Response Format**

```python
# Success response
{
    "status": "success",
    "data": {...},
    "message": "Operation completed"
}

# Error response
{
    "status": "error",
    "message": "Descriptive error message",
    "errors": {...}  # field-level errors
}

# List response (paginated)
{
    "status": "success",
    "data": [...]
    "pagination": {
        "count": 100,
        "next": "/api/v1/deliveries/?page=2",
        "previous": null,
        "page_size": 20
    }
}
```

### **Standard Endpoints Pattern**
- `GET /api/<resource>/` - List (paginated, filtered, searchable)
- `POST /api/<resource>/` - Create
- `GET /api/<resource>/<id>/` - Retrieve
- `PUT /api/<resource>/<id>/` - Update
- `DELETE /api/<resource>/<id>/` - Delete (or return 204/405)
- `PATCH /api/<resource>/<id>/` - Partial update

---

## 🎯 **Priority Implementation Order**

1. **Phase 1**: Core models (Agent, Client, User) + Authentication + Email verification read 
2. **Phase 2**: Delivery system + GPS validation + Offline sync + Proximity checks
3. **Phase 3**: Order management + Assignment logic + Status workflow
4. **Phase 4**: Admin features + Reporting endpoints + Real-time tracking (Django Channels)
5. **Phase 5**: Advanced analytics + Email notifications + Audit system

---

## ⚡ **Special AI Agent Notes**

- **Documentation strategy**: Read `/docs` files ONLY when necessary (e.g., when implementing auth, check `accounts.md` + `auth.json`). Don't preload all docs—load on-demand to avoid token bloat.
- **Data validation is critical**: Water amounts in CFA francs, GPS coordinates, agent status
- **Offline-first mobile**: Implement conflict resolution for queued deliveries
- **GPS precision**: Consider PostGIS for complex geospatial queries (distance calculations, zone analysis)
- **Email templates**: Build notification system for order updates, agent assignments, reports
- **Aggregated endpoints**: Analytics endpoints must be optimized for dashboard loading (N+1 prevention)
- **No SMS**: Email only for all notifications and 2FA
- **Financial immutability**: Treat delivery records like accounting ledgers
- **Performance**: Index on (agent, client, status, timestamp) for common queries


## 📝 **Maintenance Note**

**IMPORTANT**: This instruction file must be kept up-to-date as the project evolves. When implementing new features, refactoring code, or changing architecture decisions:
1. Update relevant sections immediately after changes
2. Document new patterns, conventions, or constraints
3. Remove outdated information to prevent AI from using obsolete approaches
4. Keep examples synchronized with actual implementation
5. Version control this file alongside code changes
6. Update the postman collection and API docs accordingly

**A stale instruction file leads to inconsistent code and technical debt.**
