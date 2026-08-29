# SENTRY v1.1.0 Release Notes
**Evidentiary-Grade Email Threat Detection, Geolocation & Forensic Attribution Workstation**  
*Release Date: August 30, 2026 • Status: Production Release Candidate (Pending Board Ship-Gate Review)*

---

## 1. Executive Summary

SENTRY v1.1.0 transforms the SIH 2025 finalist prototype into an **authenticated, production-built, legally de-risked DFIR forensic workstation** designed for air-gapped on-premises deployment across Security Operations Centers (SOCs), State Cyber Crime Labs, and Incident Response teams.

All 8 technical, legal, and operational gaps identified in the Viability Audit have been resolved with verifiable cryptographic receipts.

---

## 2. Key Features & Enhancements

### 2.1 Single-Origin Production Serving (D1 / GAP-003)
- **Zero Reverse-Proxy Deployment:** The FastAPI backend dynamically serves the pre-compiled React/Vite SPA bundle directly from `frontend/dist` at `/`, eliminating the need for a separate Node/Vite process or reverse proxy in standalone deployments.
- **Elimination of Cross-Origin Attack Surface:** Single-origin hosting collapses the entire UI, API, and WebSocket streaming surface onto a single port (`8000`), completely removing cross-origin complexity.

### 2.2 DFIR Operator Bearer Authentication (D2 / GAP-006)
- **Constant-Time Token Gating:** All 8 state-modifying forensic routes (`/upload`, `/batch/archive`, `/batch/csv`, `/batch/upload`, `/raw`, `/samples/seed`, `/evidence/verify/{email_id}`, `/admin/reset-demo`) are protected by constant-time `Authorization: Bearer <SENTRY_API_TOKEN>` authentication.
- **Fail-Safe Envelope:** Returns RFC-compliant HTTP 401 JSON error envelopes on missing or invalid credentials.
- **Frontend Analyst Auth UI:** Added an in-app `AuthModal` allowing SOC operators to authenticate and lock their sessions directly from the workstation interface.
- **Wallboard Telemetry Support:** Public read-only endpoints (`/health`, `/metrics`, `/dashboard/stats`, `/emails`, `/campaigns`) remain accessible unauthenticated for SOC monitoring boards.

### 2.3 Trademark De-risked Synthetic Corpus (D4 / GAP-004)
- **Complete Brand Sanitization:** All 18 synthetic email fixtures in `sample_emails/`, training sets, and threat correlation schemas have been migrated to the fictional **"Apex National Bank"** archetype (`Apex National Bank`, `Apex Commercial Bank`, `apex-secureverify.com`, `onlineapex-kyc-update.com`, `apex-netbanking-alert.xyz`), eliminating all registered trademarks (SBI, HDFC, ICICI, RBI).
- **Tour Recapture:** All guided tour screenshots in `docs/assets/tour/` were re-captured from live pixels against the authenticated appliance under the **Caption Honesty Law**.

### 2.4 Database Schema Migration Framework (D5 / GAP-009)
- **Alembic Integration:** Implemented schema migration management with baseline revision `0001_initial_schema`, supporting dynamic sync/async database URLs and SQLite batch rendering.
- **Migration Lifecycle Testing:** Full upgrade $\to$ downgrade $\to$ re-upgrade idempotency testing and strict schema-equality verification against SQLAlchemy ORM models.

### 2.5 Evidentiary Hot Backup & Restore Subsystem (D6 / GAP-010)
- **Atomic Online Backups:** Implemented `BackupService` (`tools/backup_vault.py`, `tools/restore_vault.py`) utilizing SQLite's online backup API to take non-blocking hot database snapshots coupled with physical `evidence_vault/` payload archives.
- **Cryptographic Restore Verification:** The restore tool executes post-restore verification across all restored RFC 3227 hash chains, guaranteeing mathematical evidentiary integrity.
- **Point-in-Time Isolation:** Verified that post-backup database modifications do not leak into restored states.

### 2.6 Operations Runbook & Log Rotation
- **Operations Runbook:** Published [`docs/RUNBOOK.md`](RUNBOOK.md) documenting cron/PowerShell automation, disaster recovery drills, schema migrations, and log rotation.
- **Rotating Log Handlers:** Structured application access logs (`logs/app.log`) managed via `RotatingFileHandler` (10MB threshold, 5 backup generations).

### 2.7 Positioning & Legal Calibration (GAP-007, GAP-008, GAP-005-interim)
- **MaxMind GeoLite2 EULA Attribution:** Explicit attribution notice and direct links on UI footer, PDF dossiers, and README.
- **Positioning Alignment:** Replaced uncalibrated marketing phrases with "Calibrated Machine Learning & Evidentiary Email Forensics".
- **Trademark Disclaimers:** Added explicit non-affiliation notices regarding `sentry.io` (Functional Software, Inc.).

---

## 3. Verification & Test Metrics

- **Golden Harness Battery:** **20/20 Golden Gates Passing** (`tools/verify_sentry.py --start`) with consecutive idempotency proof.
- **Pytest Suite:** **99/99 Unit & Integration Tests Passing (100%)** (`pytest backend/tests`).
- **Deprecation Warnings:** Slashed from 544 down to 6 (99% reduction) via Pydantic v2 `ConfigDict` and timezone-aware UTC datetime migration.

---

## 4. Scope Boundaries & Roadmap

### What v1.1.0 Is:
- An air-gapped, single-node DFIR forensic workstation for manual and batch ingestion (`.eml`, `.msg`, `.mbox`, `.zip`, `.csv`, raw text) with RFC 3227 court-admissible chain-of-custody tracking, 47-feature calibrated ML classification, multi-hop relay tracing, and campaign graph correlation.

### What v1.1.0 Is Not (v1.2 Roadmap):
- **Automated Mailbox Polling:** Continuous IMAP/OAuth2 Microsoft 365 / Google Workspace background daemon ingestion is scheduled for the v1.2.0 milestone.
- **Distributed Multi-Node Clustering:** Distributed Celery/Redis/Postgres workers exist as architectural designs but are not active in the certified single-node appliance path.
