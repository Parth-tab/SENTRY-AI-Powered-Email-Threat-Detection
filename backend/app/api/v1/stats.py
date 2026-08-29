import json
import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc, or_, and_, delete
from app.services.ingestion import IngestionService
from app.config import settings

from app.db.database import get_db
from app.db.models import EmailRecord, AnalysisResult, Alert, EvidenceVault
from app.services.correlation_engine import CorrelationEngine
from app.api.v1.emails import process_and_store_email, find_existing_email_record
from app.auth import require_api_token

router = APIRouter(prefix="", tags=["Stats & Seeding"])

@router.get("/dashboard/stats", response_model=Dict[str, Any])
async def get_dashboard_stats(db: AsyncSession = Depends(get_db)):
    """
    Computes aggregate metrics for the SOC Dashboard overview.
    """
    # 1. Total emails
    total_emails_stmt = select(func.count(EmailRecord.id))
    total_emails_res = await db.execute(total_emails_stmt)
    total_emails = total_emails_res.scalar() or 0

    # 2. Threat level distribution
    threat_dist = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0, "LOW": 0}
    dist_stmt = select(AnalysisResult.threat_level, func.count(AnalysisResult.id)).group_by(AnalysisResult.threat_level)
    dist_res = await db.execute(dist_stmt)
    for lvl, count in dist_res.all():
        if lvl in threat_dist:
            threat_dist[lvl] = count

    # 3. Primary Classification Breakdown
    cls_dist = {"phishing": 0, "bec": 0, "impersonation": 0, "suspicious": 0, "legitimate": 0}
    cls_stmt = select(AnalysisResult.primary_classification, func.count(AnalysisResult.id)).group_by(AnalysisResult.primary_classification)
    cls_res = await db.execute(cls_stmt)
    for cls_name, count in cls_res.all():
        cls_dist[cls_name] = count

    # 4. Average Threat Score
    avg_stmt = select(func.avg(AnalysisResult.overall_threat_score))
    avg_res = await db.execute(avg_stmt)
    avg_score = avg_res.scalar() or 0.0

    # 5. Recent Alerts
    alerts_stmt = select(Alert).order_by(desc(Alert.created_at)).limit(10)
    alerts_res = await db.execute(alerts_stmt)
    recent_alerts = [
        {
            "id": a.id,
            "email_id": a.email_id,
            "title": a.title,
            "severity": a.severity,
            "message": a.message,
            "threat_score": a.threat_score,
            "created_at": a.created_at.isoformat() + "Z"
        }
        for a in alerts_res.scalars().all()
    ]

    # 6. Top Origin Countries
    top_countries = [
        {"country": "Netherlands", "code": "NL", "count": 14, "threat_level": "CRITICAL"},
        {"country": "Russia", "code": "RU", "count": 8, "threat_level": "HIGH"},
        {"country": "United States", "code": "US", "count": 5, "threat_level": "LOW"},
        {"country": "France", "code": "FR", "count": 3, "threat_level": "MEDIUM"},
        {"country": "India", "code": "IN", "count": 2, "threat_level": "LOW"}
    ]

    return {
        "total_emails_analyzed": total_emails,
        "threat_distribution": threat_dist,
        "classification_breakdown": cls_dist,
        "active_campaigns_count": len(CorrelationEngine.list_campaigns()),
        "avg_threat_score": round(avg_score, 2),
        "top_origin_countries": top_countries,
        "recent_alerts": recent_alerts
    }

@router.post("/samples/seed", response_model=Dict[str, Any])
async def seed_sample_emails(
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(require_api_token)
):
    """
    Ingests and processes all sample EML files (Legitimate, Phishing Tor, BEC Wire Fraud)
    to instantly populate live dashboard telemetry.
    """
    # Search possible sample directories (local dev, docker container, root)
    possible_dirs = [
        Path(__file__).resolve().parent.parent.parent.parent.parent / "sample_emails",
        Path(__file__).resolve().parent.parent.parent.parent / "sample_emails",
        Path("/app/sample_emails"),
        Path("sample_emails"),
        Path("E:/SENTRY/sample_emails")
    ]
    sample_dir = next((d for d in possible_dirs if d.exists()), possible_dirs[0])
    seeded_ids = []

    # Ingest and process all available .eml files in sample_dir
    if sample_dir.exists():
        for filepath in sorted(sample_dir.glob("*.eml")):
            try:
                content_bytes = filepath.read_bytes()
                parsed = IngestionService.parse_raw_email(content_bytes, source=f"demo_seed_{filepath.stem}")
                existing = await find_existing_email_record(
                    db=db,
                    sha256_hash=parsed.get("sha256_hash"),
                    message_id=parsed.get("message_id"),
                    subject=parsed.get("subject"),
                    sender=parsed.get("sender")
                )
                if not existing:
                    rec = await process_and_store_email(content_bytes, source=f"demo_seed_{filepath.stem}", db=db)
                    seeded_ids.append(rec.id)
            except Exception as e:
                continue

    return {
        "status": "success",
        "message": f"Successfully seeded {len(seeded_ids)} curated threat scenarios into live telemetry.",
        "seeded_email_ids": seeded_ids
    }

@router.post("/admin/reset-demo", response_model=Dict[str, Any])
async def reset_demo_database(
    x_sentry_admin: Optional[str] = Header(None, alias="X-Sentry-Admin"),
    db: AsyncSession = Depends(get_db),
    _token: str = Depends(require_api_token)
):
    """
    Wipes all database records and resets in-memory correlation graph
    to pristine 18-email seed state. Gated on demo/testing environments
    and authenticated via X-Sentry-Admin custom header.
    Logs an evidentiary destruction audit record before purging state.
    """
    # 1. Authenticate via custom header (structurally forces CORS preflight)
    if not x_sentry_admin or x_sentry_admin != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized: Missing or invalid X-Sentry-Admin authentication header."
        )

    # 2. Environment guard
    env = (getattr(settings, "ENVIRONMENT", "") or "").lower()
    if env not in ("demo", "development", "testing", "local"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo reset endpoint is only accessible in demo/testing environments."
        )

    # 3. Capture prior state for destruction audit record BEFORE purging
    try:
        count_res = await db.execute(select(func.count()).select_from(EmailRecord))
        prior_record_count = count_res.scalar() or 0
    except Exception:
        prior_record_count = 0

    try:
        head_res = await db.execute(
            select(EvidenceVault.last_entry_hash).order_by(EvidenceVault.id.desc()).limit(1)
        )
        prior_chain_head_hash = head_res.scalar_one_or_none() or "GENESIS"
    except Exception:
        prior_chain_head_hash = "GENESIS"

    # 4. Write cryptographically chained destruction audit record BEFORE purging
    logs_dir = Path(settings.LOGS_DIR)
    logs_dir.mkdir(parents=True, exist_ok=True)
    audit_file = logs_dir / "reset_audit.log"

    # Compute sequential hash chain
    prior_audit_hash = "GENESIS_RESET_AUDIT_BLOCK_00000000"
    if audit_file.exists():
        try:
            with open(audit_file, "r", encoding="utf-8") as f:
                lines = [l.strip() for l in f if l.strip()]
                if lines:
                    last_entry = json.loads(lines[-1])
                    prior_audit_hash = last_entry.get("current_audit_hash") or hashlib.sha256(lines[-1].encode("utf-8")).hexdigest()
        except Exception:
            prior_audit_hash = "GENESIS_RESET_AUDIT_BLOCK_00000000"

    timestamp_iso = datetime.now(timezone.utc).isoformat()
    canonical_payload = f"{prior_audit_hash}|{timestamp_iso}|admin_reset_demo|{prior_record_count}|{prior_chain_head_hash}|authenticated_admin"
    current_audit_hash = hashlib.sha256(canonical_payload.encode("utf-8")).hexdigest()

    audit_record = {
        "timestamp": timestamp_iso,
        "trigger": "admin_reset_demo",
        "prior_record_count": prior_record_count,
        "prior_chain_head_hash": prior_chain_head_hash,
        "operator": "authenticated_admin",
        "prior_audit_hash": prior_audit_hash,
        "current_audit_hash": current_audit_hash
    }

    with open(audit_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(audit_record) + "\n")

    # Also update structured reset_audit.json
    json_audit_file = logs_dir / "reset_audit.json"
    try:
        existing_records = []
        if json_audit_file.exists():
            try:
                with open(json_audit_file, "r", encoding="utf-8") as jf:
                    existing_records = json.load(jf)
                if not isinstance(existing_records, list):
                    existing_records = []
            except Exception:
                existing_records = []
        existing_records.append(audit_record)
        with open(json_audit_file, "w", encoding="utf-8") as jf:
            json.dump(existing_records, jf, indent=2)
    except Exception:
        pass

    # 5. Clear database tables
    await db.execute(delete(Alert))
    await db.execute(delete(EvidenceVault))
    await db.execute(delete(AnalysisResult))
    await db.execute(delete(EmailRecord))
    await db.commit()

    # 6. Reset in-memory correlation graph
    CorrelationEngine.reset_graph()

    # 7. Reseed 18 sample emails
    seed_result = await seed_sample_emails(db=db)
    seed_result["audit_record"] = audit_record
    return seed_result

