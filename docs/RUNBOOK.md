# SENTRY Enterprise Appliance Operations Runbook

> **Evidentiary Standard:** RFC 3227 • NIST SP 800-86 • ISO/IEC 27037  
> **Applicable Version:** v1.1.0+ • **Target:** SOC Tier 2/3 Operators & System Administrators

---

## 1. Overview & Operational Principles

SENTRY is a hardened, air-gapped forensic workstation and threat detection appliance. To maintain court-admissible evidentiary integrity under **RFC 3227**, operations must follow deterministic procedures:
1. **Never perform raw, un-checkpointed file copies** of active SQLite databases during ingestion.
2. **Always use verified snapshot tooling** (`tools/backup_vault.py` / `tools/restore_vault.py`) which cryptographically validates hash chains post-restore.
3. **Always track schema evolution via Alembic migrations** before deploying updated binaries.

---

## 2. Evidentiary Hot Backup Automation (GAP-010)

SENTRY includes atomic hot-backup tooling that leverages SQLite's online backup API alongside byte-exact verification of all sealed `.eml` payloads in `evidence_vault/`.

### 2.1 Manual Snapshot Creation
```bash
# From repository root
python tools/backup_vault.py --output backups/sentry_snapshot_manual.tar.gz
```
**Expected Output:**
```
[*] Initiating SENTRY evidentiary hot snapshot...

[+] SNAPSHOT GENERATED SUCCESSFULLY:
    Archive Path:     E:\SENTRY\backups\sentry_snapshot_manual.tar.gz
    Archive SHA-256:  3f8a...e901
    Database SHA-256: 7b2c...41a2
    Email Records:    18
    Evidence Chains:  18
    Vault Files:      18
    Timestamp (UTC):  2026-08-30T02:00:00Z
```

### 2.2 Scheduled Daily Automation
#### Linux (Cron):
```cron
# Daily backup at 02:00 UTC with 30-day retention
0 2 * * * cd /opt/sentry && /opt/sentry/.venv/bin/python tools/backup_vault.py >> /var/log/sentry/backup.log 2>&1
0 3 * * * find /opt/sentry/backups -name "sentry_snapshot_*.tar.gz" -mtime +30 -delete
```

#### Windows (PowerShell Scheduled Task):
```powershell
$Action = New-ScheduledTaskAction -Execute "E:\SENTRY\.venv\Scripts\python.exe" -Argument "tools\backup_vault.py" -WorkingDirectory "E:\SENTRY"
$Trigger = New-ScheduledTaskTrigger -Daily -At 2am
Register-ScheduledTask -TaskName "SENTRY_Hot_Backup" -Action $Action -Trigger $Trigger -Description "Daily SENTRY Evidentiary Hot Backup"
```

---

## 3. Disaster Recovery & Hot Restore Drill (GAP-010)

A backup is only valid if it restores a *mathematically verifiable cryptographic state*. The restore tool unpacks the database and vault, reconciles individual payload checksums, and executes full verification across all RFC 3227 chains of custody.

### 3.1 Execute Restore Drill
```bash
# 1. Stop active SENTRY backend service
# On Windows:
powershell -File tools/cleanup.ps1
# On Linux:
systemctl stop sentry

# 2. Execute Verified Restore
python tools/restore_vault.py --snapshot backups/sentry_snapshot_20260830T020000Z.tar.gz
```

### 3.2 Restore Receipt Verification
The restore command will output a formal cryptographic receipt:
```
[*] Initiating restore from snapshot: backups/sentry_snapshot_20260830T020000Z.tar.gz

[+] RESTORE VERIFICATION PASSED (PASS):
    Restored Database:       E:\SENTRY\backend\sentry.db
    Restored Evidence Vault: E:\SENTRY\evidence_vault
    Restored Vault Files:    18
    Verified Hash Chains:    18 (0 failures)
    Receipt:                 All restored RFC 3227 hash chains verified cryptographically intact with zero discrepancies.
```

### 3.3 Post-Restore Verification Checks
1. Boot backend: `python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000`
2. Run deep health check:
   ```bash
   curl -s http://127.0.0.1:8000/health/deep | jq .
   ```
   Confirm `"status": "healthy"` and `"database": {"status": "healthy"}`.

---

## 4. Database Migration & Schema Upgrade Drill (GAP-009 / D5)

SENTRY uses Alembic for zero-downtime, deterministic relational database migrations.

### 4.1 Check Current Schema Revision
```bash
cd backend
alembic current
```
Output: `0001_initial_schema (head)`

### 4.2 Apply Pending Migrations (Upgrade)
```bash
cd backend
alembic upgrade head
```

### 4.3 Stamping Existing Appliances
If upgrading an unmigrated v1.0.0 appliance whose database was initialized without Alembic version metadata:
```bash
cd backend
alembic stamp head
```

### 4.4 Rollback Procedure (Downgrade Drill)
To roll back the last applied migration:
```bash
cd backend
alembic downgrade -1
```

---

## 5. Log Rotation & Disk Quota Management

SENTRY incorporates `RotatingFileHandler` across application and audit logging.

| Log Stream | Path | Rotation Threshold | Retention | Purpose |
| :--- | :--- | :--- | :--- | :--- |
| **Application Log** | `logs/app.log` | 10 MB per file | 5 generations (`app.log.1` ... `app.log.5`) | Structured request tracing, correlation IDs, timing |
| **Reset Audit Trail** | `logs/reset_audit.log` | Append-only / tamper-evident | Permanent | Cryptographic hash receipt of demo resets |
| **Verification Logs** | `logs/verify_backend.log` | Recreated per harness run | Ephemeral | CI/Harness integration trace |

### Monitoring Disk Utilization:
```bash
# Check log volume size
du -sh logs/
# Tail live application log with correlation tracking
tail -f logs/app.log
```

---

## 6. Emergency Troubleshooting & Port Release

If the backend or frontend fails to bind to ports 8000 / 3000 due to stale orphaned processes:

### Windows:
```powershell
powershell -File tools/cleanup.ps1
```

### Linux:
```bash
fuser -k 8000/tcp 3000/tcp
```
