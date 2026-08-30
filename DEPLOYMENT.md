# SENTRY On-Premises & Enterprise Deployment Guide

Evidentiary-Grade Email Threat Detection, Geolocation & Forensic Intelligence Platform  
*Document Version: 1.1.0 • Target: On-Premises Appliance / DFIR Workstation*

---

## 1. System Architecture & Topology

SENTRY is engineered as an **air-gapped single-node forensic appliance** designed for deployment within Security Operations Centers (SOCs), State Cyber Crime Units, and DFIR laboratories.

```
┌────────────────────────────────────────────────────────────────────────┐
│               SENTRY Standalone Production Appliance                   │
│                                                                        │
│   ┌────────────────────────────────────────────────────────────────┐   │
│   │               FastAPI Single-Origin Server (:8000)             │   │
│   │                                                                │   │
│   │  [ / ]             Mounted Static SPA (frontend/dist)          │   │
│   │  [ /api/v1/... ]   Forensic Ingestion, ML & Analytics API      │   │
│   │  [ /metrics ]      Prometheus RED Telemetry Pipeline           │   │
│   │  [ /health/deep ]  Subsystem Verification Diagnostics          │   │
│   └──────────────┬─────────────────────────┬───────────────────────┘   │
│                  │                         │                           │
│   ┌──────────────▼──────────────┐   ┌──────▼───────────────────────┐   │
│   │   Asynchronous Relational   │   │     Local Evidence Vault     │   │
│   │    SQLite (aiosqlite)       │   │   (evidence_vault/*.eml)     │   │
│   │   (backend/sentry.db)       │   │   RFC 3227 Sealed Payloads   │   │
│   └─────────────────────────────┘   └──────────────────────────────┘   │
└────────────────────────────────────────────────────────────────────────┘
```

### Key Deployment Characteristics:
* **Single-Origin Simplicity (D1):** When built and served in production mode, FastAPI directly serves the pre-compiled React/Vite SPA from `frontend/dist` on port **8000**. No second server process, zero reverse-proxy requirement for standalone use, and zero CORS surface.
* **Deterministic Air-Gapped Operation:** All Machine Learning feature extraction (47 dimensions), gradient boosting classification, IP geolocation (MaxMind GeoLite2), and NetworkX campaign link analysis execute entirely in-process without outbound Internet access.

---

## 2. Prerequisites & Build Steps

### Hardware & OS Requirements
* **OS:** Linux (Ubuntu 22.04 LTS+, RHEL 9+, Debian 12+) or Windows Server 2022+ / Windows 11.
* **CPU:** 4 physical cores recommended (2 cores minimum).
* **RAM:** 4 GB minimum (8 GB recommended for large batch ingestion).
* **Storage:** 20 GB SSD storage minimum (vault scales with ingested raw email volume).
* **Software:** Python 3.11+ and Node.js 20+ LTS.

### 2.1 Clone & Setup Environment
```bash
git clone https://github.com/Parth-tab/SENTRY-AI-Powered-Email-Threat-Detection.git sentry
cd sentry

# Python Environment
python -m venv .venv
# On Linux/macOS:
source .venv/bin/activate
# On Windows (PowerShell):
.venv\Scripts\Activate.ps1

pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 2.2 Compile Production SPA Assets
```bash
cd frontend
npm install
npm run build
cd ..
```
*Verification:* Ensure that `frontend/dist/index.html` and `frontend/dist/assets/` exist.

---

## 3. Environment Configuration & Variables

SENTRY utilizes Pydantic-based configuration with automatic `.env` file loading and environment variable overrides.

Create a `.env` file in the repository root or set the variables in your process supervisor (e.g. systemd, Docker, supervisord):

| Environment Variable | Type | Default (Demo) | Production Requirement | Description |
| :--- | :---: | :--- | :--- | :--- |
| `ENVIRONMENT` | `string` | `demo` | `production` | Set to `production` for air-gapped on-premise deployment. Enforces strict entropy checks. |
| `BUILD_MODE` | `string` | `demo` | `production` | Enables single-origin SPA static mount. |
| `SERVE_STATIC` | `bool` | `false` | `true` | When `true`, FastAPI mounts `frontend/dist` directly at `/`. |
| `FRONTEND_DIST_DIR` | `string` | `../frontend/dist` | Absolute path | Path to built frontend static bundle. |
| `SECRET_KEY` | `string` | *(demo default)* | **Required High-Entropy** | Cryptographic key used for session signing and internal cryptographic checks. |
| `ADMIN_TOKEN` | `string` | *(demo default)* | **Required High-Entropy** | Token required for administrative endpoints (`X-Sentry-Admin` header). |
| `SENTRY_API_TOKEN` | `string` | *(demo default)* | **Required** | Bearer authentication token for DFIR analysts on writable ingest routes. |
| `DATABASE_URL` | `string` | `sqlite+aiosqlite:///...` | SQLite URL | Asynchronous SQLAlchemy database connection URI. |
| `SYNC_DATABASE_URL` | `string` | `sqlite:///...` | SQLite URL | Synchronous connection URI for schema migrations and utilities. |
| `EVIDENCE_VAULT_DIR` | `string` | `./evidence_vault` | Path | Filesystem path storing raw immutable RFC 3227 sealed email payloads. |
| `LOGS_DIR` | `string` | `./logs` | Path | Directory for telemetry, audit logs, and diagnostic traces. |
| `CORS_ORIGINS` | `string` | `""` | `""` or custom | Comma-separated list of additional allowed HTTP origins if reverse-proxying. |

### Production `.env` Example
```ini
ENVIRONMENT=production
BUILD_MODE=production
SERVE_STATIC=true
SECRET_KEY=e8f7a93c41b80e5d26f1c79a0b3e4d5f6a7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d
ADMIN_TOKEN=a1b2c3d4e5f67890abcdef1234567890fedcba0987654321
SENTRY_API_TOKEN=sentry_soc_analyst_bearer_sec_2026
DATABASE_URL=sqlite+aiosqlite:///data/sentry.db
SYNC_DATABASE_URL=sqlite:///data/sentry.db
EVIDENCE_VAULT_DIR=/data/evidence_vault
LOGS_DIR=/var/log/sentry
```

---

## 4. Run Modes & Port Bindings

### Mode A: Production Single-Origin Appliance (Recommended)
FastAPI serves the entire application (API + UI + WebSockets) on a single port:

```bash
# Start on port 8000 bound to local or private network interface
python -m uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000 --workers 4
```
* **Access UI:** `http://<server-ip>:8000/`
* **API Documentation:** `http://<server-ip>:8000/docs`
* **Health Check:** `http://<server-ip>:8000/health/deep`
* **Prometheus Metrics:** `http://<server-ip>:8000/metrics`

### Mode B: Dual-Process Development Mode
For developers extending the platform:
```bash
# Terminal 1: Backend with auto-reload
python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

# Terminal 2: Frontend Vite Dev Server
cd frontend && npm run dev -- --port 3000
```
* **Access UI:** `http://127.0.0.1:3000/` (proxies WebSocket and API calls to `:8000`)

---

---

## 5. Database Migrations & Schema Upgrades (GAP-009 / D5)

SENTRY manages database schema evolution via Alembic.

### Applying Migrations
Before starting the backend on an existing database, run:
```bash
cd backend
alembic upgrade head
```

### Stamping Legacy Installations
For v1.0.0 installations initialized prior to migration tracking:
```bash
cd backend
alembic stamp head
```

---

## 6. Persistent Data Locations & Backup Operations (GAP-010 / D6)

| Data Asset | Filesystem Location | Description |
| :--- | :--- | :--- |
| **Relational Database** | `backend/sentry.db` (or configured path) | SQLite database containing parsed emails, threat scores, campaign links, and hop chronologies. |
| **Evidence Vault** | `evidence_vault/` | Write-once SHA-256 addressed `.eml` raw files with RFC 3227 genesis hash blocks. |
| **Application & Access Logs** | `logs/app.log` | Rotating structured logs (10MB limit, 5 backup generations). |
| **Admin Audit Trail** | `logs/reset_audit.log` | Cryptographically signed administrative action and reset audit records. |

> [!IMPORTANT]
> **Atomic Backup Notice (GAP-010):**  
> Because SENTRY links database records to physical disk digests via cryptographic hash chains, restoring a database snapshot without the matching `evidence_vault/` filesystem snapshot (or vice-versa) invalidates RFC 3227 verification.  
> Always use the coordinated evidentiary hot backup and restore tooling:
>
> **Create Hot Snapshot:**
> ```bash
> python tools/backup_vault.py --output backups/sentry_snapshot_$(date +%Y%m%d_%H%M%S).tar.gz
> ```
>
> **Execute Verified Restore:**
> ```bash
> python tools/restore_vault.py --snapshot backups/sentry_snapshot_<timestamp>.tar.gz
> ```
>
> For full disaster recovery procedures, automated cron schedules, and rollback drills, consult [`docs/RUNBOOK.md`](docs/RUNBOOK.md).
