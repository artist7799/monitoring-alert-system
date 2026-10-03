# Real-Time Monitoring & Alert Management System

A full-stack, enterprise-grade **Real-Time Monitoring & Alert Management System** built with a **Flask REST API**, **MySQL database (SQLAlchemy ORM)**, **Server-Sent Events (SSE) real-time stream**, and a modern **React + Vite monitoring dashboard**.

---

## 🏗️ System Architecture

```text
                               Monitoring Device / Telemetry Engine
                                                │
                                                ↓
                                    POST /api/events (REST)
                                                │
                                                ↓
                                   Event Processing Service
                                                │
                                                ↓
                                      Alert Engine Rules
                                                │
                         ┌──────────────────────┴──────────────────────┐
                         ↓                                             ↓
                  MySQL Database                              SSE Real-Time Stream
             (Events, Alerts, Devices)                            (/api/stream)
                         │                                             │
                         └──────────────────────┬──────────────────────┘
                                                ↓
                                     React + Vite Dashboard
```

---

## 🚀 Key System Features

- **Authentication & RBAC**: Secure JWT-based authentication supporting three user roles:
  - `ADMIN`: Full CRUD management access across devices, events, alerts, and system settings.
  - `OPERATOR`: Operational telemetry submission, alert acknowledgment, and alert resolution.
  - `VIEWER`: Read-only system health and monitoring access.
- **Device Management**: Full lifecycle tracking of monitoring hardware (`ONLINE`, `WARNING`, `OFFLINE`) with soft-deletion data preservation.
- **Event Processing Service**: Ingests multi-metric telemetry events (`TEMPERATURE`, `HUMIDITY`, `CPU_USAGE`, `MEMORY_USAGE`, `SMOKE`, `SYSTEM_ERROR`, `STATUS_CHANGE`).
- **Alert Engine**: Evaluates configurable threshold rules upon event ingestion, automatically creating system alerts (`LOW`, `HIGH`, `CRITICAL`) with deduplication.
- **System Status & Monitoring APIs**: Overview stats (`total_devices`, `online_devices`, `warning_devices`, `offline_devices`, `open_alerts`, `critical_alerts`, `events_today`) and single-device health breakdowns.
- **Real-Time SSE Stream**: Low-latency Server-Sent Events stream at `/api/stream` pushing live system status updates, telemetry events, device status changes, and alert notifications to connected dashboards.
- **React + Vite Dashboard**: Dark-mode enterprise UI featuring:
  - System Overview Cards & Key Metrics
  - Live Telemetry Stream Feed
  - Recent Alert Feed & Toast Notifications
  - Device Inventory Table with Search, Filter & Pagination
  - Device Details Page with Telemetry Sparkline Charts & Metric Gauges
  - Telemetry Event Log with Date Range Filtering & Sorting
  - Alert Management Page with Acknowledge & Resolve Actions
  - SSE Connection Status Indicator (`Live` / `Reconnecting` / `Offline`)

---

## 🛠️ Technology Stack

| Layer | Technology |
|---|---|
| **Backend Framework** | Flask, Python 3.11 |
| **Database & ORM** | MySQL 8+, Flask-SQLAlchemy, PyMySQL |
| **Database Migrations** | Flask-Migrate (Alembic) |
| **Authentication & RBAC** | Flask-JWT-Extended, bcrypt |
| **API Documentation** | Flasgger (Swagger UI at `/apidocs/`) |
| **Validation & Schema** | Marshmallow |
| **Real-Time Communication** | Server-Sent Events (SSE) via `ReadableStream` |
| **Frontend Framework** | React 18, Vite 5, React Router 6 |
| **HTTP Client** | Axios (with JWT interceptors) |
| **Icons & Design** | Lucide React, Vanilla CSS Design System |
| **Testing Frameworks** | Pytest (Backend), Vitest & Testing Library (Frontend) |

---

## 📁 Project Structure

```text
monitoring-alert-system/
├── backend/
│   ├── app.py                  # Flask Application Factory & Server Entrypoint
│   ├── models/                 # SQLAlchemy Models (User, Device, Event, Alert, SystemStatus)
│   ├── routes/                 # REST Blueprints (Auth, Devices, Events, Alerts, Status, Stream)
│   ├── services/               # Business Logic Services (Auth, Device, Event, Alert, Monitoring, SSE)
│   ├── schemas/                # Marshmallow Request/Response Validation Schemas
│   ├── database/               # Database Connection & Seed Data Scripts
│   ├── middleware/             # RBAC Decorators & Error Handling Middleware
│   ├── tests/                  # Pytest Unit & Integration Test Suite (189 Tests)
│   └── venv/                   # Python Virtual Environment
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API Services (authApi, deviceApi, eventApi, alertApi, statusApi)
│   │   ├── components/         # Reusable UI Components (Layout, Sidebar, Header, Tables, Badges, Charts)
│   │   ├── context/            # AuthContext Provider
│   │   ├── hooks/              # Custom Hooks (useAuth, useSSE)
│   │   ├── pages/              # Router Pages (Login, Dashboard, Devices, DeviceDetails, Events, Alerts)
│   │   ├── test/               # Vitest Frontend Test Suite
│   │   ├── utils/              # Helper Utilities (storage, formatDate, status)
│   │   ├── index.css           # Global Dark Theme Design Tokens & CSS
│   │   ├── App.jsx             # React Router & Protection Guards
│   │   └── main.jsx            # React Entrypoint
│   ├── package.json            # Frontend Package Manifest
│   └── vite.config.js          # Vite Proxy & Vitest Config
├── README.md                   # System Documentation
└── .env.example                # Environment Variable Template
```

---

## ⚡ Quick Start Guide

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- MySQL Server 8.0+ running on `localhost:3006` (or configured database)

---

### Step 1: Backend Setup

1. **Navigate to the backend directory**:
   ```powershell
   cd monitoring-alert-system/backend
   ```

2. **Activate the Virtual Environment**:
   ```powershell
   .\venv\Scripts\Activate.ps1
   ```

3. **Configure Environment Variables**:
   Ensure `.env` contains:
   ```env
   FLASK_ENV=development
   SECRET_KEY=super-secret-key-change-in-production-32bytes!
   JWT_SECRET_KEY=jwt-secret-key-super-secret-32bytes-long!
   DB_HOST=localhost
   DB_PORT=3306
   DB_NAME=monitoring_alert_system
   DB_USER=root
   DB_PASSWORD=your_mysql_password
   ```

4. **Initialize Database & Seed Initial Data**:
   ```powershell
   python app.py seed
   ```

5. **Run Backend Server**:
   ```powershell
   python app.py
   ```
   The REST API will start at `http://localhost:5000`. Swagger API docs are available at `http://localhost:5000/apidocs/`.

---

### Step 2: Frontend Setup

1. **Open a new terminal and navigate to the frontend directory**:
   ```powershell
   cd monitoring-alert-system/frontend
   ```

2. **Install Dependencies**:
   ```powershell
   npm install
   ```

3. **Start Vite Development Server**:
   ```powershell
   npm run dev
   ```
   The dashboard will be available at `http://localhost:3000`.

---

## 🔐 Default Seed Credentials

| Role | Email | Password | Permissions |
|---|---|---|---|
| **ADMIN** | `admin@example.com` | `admin123` | Full CRUD Access, Device Management, Alert Actions |
| **OPERATOR** | `operator@example.com` | `operator123` | Post Telemetry Events, Acknowledge & Resolve Alerts |
| **VIEWER** | `viewer@example.com` | `viewer123` | Read-Only Monitoring Access |

---

## 🧪 Running Test Suites

### Backend Unit & Integration Tests (Pytest)
Run all 189 backend tests covering models, auth, RBAC, CRUD APIs, alert generation engine, system status overview, and SSE real-time streaming:
```powershell
cd monitoring-alert-system/backend
.\venv\Scripts\pytest
```
*Expected Result*: `189 passed in ~2m 45s`

### Frontend Unit & Integration Tests (Vitest)
Run the React frontend test suite:
```powershell
cd monitoring-alert-system/frontend
npx vitest run
```
*Expected Result*: `10 passed in ~3s`

### Frontend Production Build Test
Verify that the React app compiles cleanly without bundling errors:
```powershell
cd monitoring-alert-system/frontend
npm run build
```

---

## 📡 API Endpoint Summary

| Category | Endpoint | Method | RBAC | Description |
|---|---|---|---|---|
| **Auth** | `/api/auth/register` | `POST` | Public | Register new user account |
| **Auth** | `/api/auth/login` | `POST` | Public | Authenticate user & issue JWT |
| **Auth** | `/api/auth/me` | `GET` | All | Fetch current profile |
| **Devices** | `/api/devices` | `GET` | All | List devices with search/pagination |
| **Devices** | `/api/devices` | `POST` | ADMIN | Register new device |
| **Devices** | `/api/devices/<id>` | `GET` | All | Fetch single device details |
| **Devices** | `/api/devices/<id>` | `PUT` | ADMIN | Update device configuration |
| **Devices** | `/api/devices/<id>` | `DELETE` | ADMIN | Soft-delete device |
| **Events** | `/api/events` | `POST` | ADMIN, OPERATOR | Ingest telemetry event & trigger Alert Engine |
| **Events** | `/api/events` | `GET` | All | List event history with search, date & metric filters |
| **Alerts** | `/api/alerts` | `GET` | All | List system alerts |
| **Alerts** | `/api/alerts/<id>/acknowledge` | `POST` | ADMIN, OPERATOR | Acknowledge open alert |
| **Alerts** | `/api/alerts/<id>/resolve` | `POST` | ADMIN, OPERATOR | Resolve alert |
| **Status** | `/api/status/overview` | `GET` | All | Real-time system overview counters |
| **Status** | `/api/status/devices` | `GET` | All | Detailed health status for all devices |
| **Status** | `/api/status/recent-events` | `GET` | All | Fetch recent events stream |
| **Status** | `/api/status/recent-alerts` | `GET` | All | Fetch recent alerts stream |
| **Stream** | `/api/stream` | `GET` | All | SSE real-time stream endpoint |

---

## 🎯 Completed Phase Matrix

- ✅ **Phase 1**: Project Structure & Architecture
- ✅ **Phase 2**: Database Models & Schema Design
- ✅ **Phase 3**: MySQL + Migrations + Database Seeding
- ✅ **Phase 4**: Authentication, JWT & RBAC Middleware
- ✅ **Phase 5**: Device Management REST APIs
- ✅ **Phase 6**: Event Processing Service
- ✅ **Phase 7**: Alert Generation & Management Engine
- ✅ **Phase 8**: System Status & Monitoring APIs
- ✅ **Phase 9**: Real-Time Server-Sent Events (SSE) Stream
- ✅ **Phase 10**: React Real-Time Monitoring Dashboard
- ✅ **Phase 11**: Production Dashboard Polish, Metric Charts & Comprehensive Frontend Integration
