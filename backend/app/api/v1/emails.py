import io
import json
from typing import List, Optional, Dict, Any
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Body, Response, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc

from app.db.database import get_db
from app.db.models import EmailRecord, AnalysisResult, EvidenceVault, Alert, Campaign
from app.schemas.email import EmailResponse, EmailDetailResponse
from app.schemas.analysis import AnalysisResultResponse
from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.services.threat_intel import ThreatIntelService
from app.services.correlation_engine import CorrelationEngine
from app.services.reporting import ReportingService
from app.services.alerting import alert_manager
from app.services.utils import json_serializable
from app.ml.classifier import ThreatClassifier

def model_to_dict(obj):
    if obj is None:
        return None
    return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

router = APIRouter(prefix="/emails", tags=["Emails"])

async def process_and_store_email(raw_bytes: bytes, source: str, db: AsyncSession) -> EmailRecord:
    # 1. Ingestion & Raw Extraction
    email_data = IngestionService.parse_raw_email(raw_bytes, source=source)
    
    # 2. Header Forensics
    hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(email_data["received_headers"])
    auth_results = HeaderForensicsService.evaluate_authentication(email_data["headers"])
    detected_anomalies = HeaderForensicsService.detect_anomalies(email_data, earliest_hop)
    all_anomalies = list(set(hop_anomalies + detected_anomalies))
    
    header_res = {
        "relay_hops_count": len(hops),
        "relay_path": hops,
        "earliest_reliable_hop": earliest_hop,
        "authentication": auth_results,
        "header_anomalies": all_anomalies
    }

    # 3. Content Analysis
    content_res = ContentAnalysisService.analyze_content(email_data)

    # 4. Domain Intelligence
    domain_res = DomainIntelService.analyze_domain(
        email_data.get("sender_domain", ""),
        sender_ip=earliest_hop.get("from_ip") if earliest_hop else None
    )

    # 5. Geolocation & Origin Assessment
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))

    # 6. External Threat Intelligence Corroboration
    threat_intel_res = await ThreatIntelService.evaluate_threat_intelligence(
        ip=origin_res.get("probable_origin_ip", ""),
        domain=domain_res.get("domain", ""),
        urls=content_res.get("urls_found", [])
    )

    # 7. Correlation & Attribution
    attribution_res = CorrelationEngine.correlate(email_data, origin_res, domain_res, content_res)

    # 8. ML Multi-signal Classification
    classification_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res,
        threat_intel_res=threat_intel_res
    )

    # 9. Evidence Vault & RFC 3227 Chain of Custody
    coc_id, chain_entries, last_hash = ReportingService.initialize_chain_of_custody(
        email_id=email_data["email_id"],
        sha256_hash=email_data["sha256_hash"],
        source=source
    )
    # Log analysis completion into hash chain
    chain_entries, last_hash = ReportingService.append_chain_entry(
        entries=chain_entries,
        action="AUTOMATED_FORENSIC_ANALYSIS",
        actor="SENTRY_CORRELATION_ENGINE",
        details=f"Extracted {len(hops)} relay hops, verified SPF/DKIM/DMARC, classified as {classification_res['threat_level']} ({classification_res['overall_threat_score']:.2f})"
    )

    # 10. Persist to Database
    email_record = EmailRecord(
        id=email_data["email_id"],
        message_id=email_data["message_id"],
        subject=email_data["subject"],
        sender=email_data["sender"],
        sender_domain=email_data["sender_domain"],
        recipient=email_data["recipient"],
        date=email_data["date"],
        raw_content=email_data["body_plain"],
        raw_content_path=email_data["vault_path"],
        raw_headers=json_serializable(email_data["headers"]),
        sha256_hash=email_data["sha256_hash"],
        source=source,
        ingested_at=email_data["ingested_at"],
        status="processed"
    )
    db.add(email_record)

    analysis_record = AnalysisResult(
        email_id=email_record.id,
        overall_threat_score=float(classification_res["overall_threat_score"]),
        threat_level=classification_res["threat_level"],
        primary_classification=classification_res["primary_classification"],
        classification_confidence=float(classification_res["classification_confidence"]),
        model_contributions=json_serializable(classification_res["model_contributions"]),
        auth_spf=json_serializable(auth_results.get("spf")),
        auth_dkim=json_serializable(auth_results.get("dkim")),
        auth_dmarc=json_serializable(auth_results.get("dmarc")),
        header_anomalies=json_serializable(all_anomalies),
        relay_hops_count=len(hops),
        relay_path=json_serializable(hops),
        earliest_reliable_hop=json_serializable(earliest_hop),
        content_analysis=json_serializable(content_res),
        domain_intel=json_serializable(domain_res),
        origin_assessment=json_serializable(origin_res),
        attribution_assessment=json_serializable(attribution_res),
        threat_intel_matches=json_serializable(threat_intel_res),
        recommendations=json_serializable(classification_res["recommendations"]),
        created_at=datetime.utcnow()
    )
    db.add(analysis_record)

    evidence_record = EvidenceVault(
        email_id=email_record.id,
        sha256_hash=email_data["sha256_hash"],
        stored_path=email_data["vault_path"],
        chain_of_custody_id=coc_id,
        chain_entries=json_serializable(chain_entries),
        last_entry_hash=last_hash,
        is_sealed=True,
        created_at=datetime.utcnow()
    )
    db.add(evidence_record)

    # Create real-time Alert if high/critical threat
    alert_record = None
    if classification_res["overall_threat_score"] >= 0.70:
        alert_record = Alert(
            email_id=email_record.id,
            title=f"{classification_res['threat_level']} Threat: {email_data['subject'][:40]}",
            severity=classification_res["threat_level"],
            message=f"Detected {classification_res['primary_classification'].upper()} from {email_data['sender']} (Score: {classification_res['overall_threat_score']:.2f})",
            threat_score=float(classification_res["overall_threat_score"]),
            is_acknowledged=False,
            created_at=datetime.utcnow()
        )
        db.add(alert_record)

    await db.commit()
    await db.refresh(email_record)

    # Update in-memory correlation graph
    CorrelationEngine.add_email_to_graph(
        email_id=email_record.id,
        email_data=email_data,
        analysis_data={
            "overall_threat_score": classification_res["overall_threat_score"],
            "threat_level": classification_res["threat_level"],
            "domain_intel": domain_res,
            "origin_assessment": origin_res,
            "attribution_assessment": attribution_res
        }
    )

    # Broadcast real-time updates via WebSocket
    analysis_dict = {
        "overall_threat_score": classification_res["overall_threat_score"],
        "threat_level": classification_res["threat_level"],
        "primary_classification": classification_res["primary_classification"]
    }
    await alert_manager.broadcast_email_analyzed(
        email_data={"id": email_record.id, "subject": email_record.subject, "sender": email_record.sender},
        analysis_data=analysis_dict
    )
    if alert_record:
        await alert_manager.broadcast_alert({
            "id": alert_record.id,
            "email_id": email_record.id,
            "title": alert_record.title,
            "severity": alert_record.severity,
            "message": alert_record.message,
            "threat_score": alert_record.threat_score,
            "created_at": alert_record.created_at.isoformat()
        })

    return email_record

@router.post("/upload", response_model=EmailDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_eml_file(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """
    Accepts .eml, .msg, or .mbox email file uploads, runs complete forensic pipeline,
    and returns full analysis.
    """
    content_bytes = await file.read()
    if not content_bytes:
        raise HTTPException(status_code=400, detail="Uploaded file is empty.")
    
    email_record = await process_and_store_email(content_bytes, source="eml_upload", db=db)
    
    stmt = select(EmailRecord).where(EmailRecord.id == email_record.id)
    res = await db.execute(stmt)
    full_email = res.scalar_one_or_none()
    
    stmt_analysis = select(AnalysisResult).where(AnalysisResult.email_id == email_record.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalar_one_or_none()
    
    stmt_evidence = select(EvidenceVault).where(EvidenceVault.email_id == email_record.id)
    res_evidence = await db.execute(stmt_evidence)
    evidence = res_evidence.scalar_one_or_none()

    return {
        "id": full_email.id,
        "message_id": full_email.message_id,
        "subject": full_email.subject,
        "sender": full_email.sender,
        "sender_domain": full_email.sender_domain,
        "recipient": full_email.recipient,
        "date": full_email.date,
        "source": full_email.source,
        "sha256_hash": full_email.sha256_hash,
        "ingested_at": full_email.ingested_at,
        "status": full_email.status,
        "raw_headers": full_email.raw_headers,
        "raw_content": full_email.raw_content,
        "analysis": model_to_dict(analysis),
        "evidence": model_to_dict(evidence)
    }

@router.post("/raw", response_model=EmailDetailResponse, status_code=status.HTTP_201_CREATED)
async def upload_raw_email(
    raw_content: str = Body(..., media_type="text/plain"),
    db: AsyncSession = Depends(get_db)
):
    """Submits raw RFC 5322 text string for instant forensic triage."""
    content_bytes = raw_content.encode("utf-8")
    email_record = await process_and_store_email(content_bytes, source="api_raw", db=db)
    
    stmt_analysis = select(AnalysisResult).where(AnalysisResult.email_id == email_record.id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalar_one_or_none()
    
    stmt_evidence = select(EvidenceVault).where(EvidenceVault.email_id == email_record.id)
    res_evidence = await db.execute(stmt_evidence)
    evidence = res_evidence.scalar_one_or_none()

    return {
        "id": email_record.id,
        "message_id": email_record.message_id,
        "subject": email_record.subject,
        "sender": email_record.sender,
        "sender_domain": email_record.sender_domain,
        "recipient": email_record.recipient,
        "date": email_record.date,
        "source": email_record.source,
        "sha256_hash": email_record.sha256_hash,
        "ingested_at": email_record.ingested_at,
        "status": email_record.status,
        "raw_headers": email_record.raw_headers,
        "raw_content": email_record.raw_content,
        "analysis": model_to_dict(analysis),
        "evidence": model_to_dict(evidence)
    }

@router.get("", response_model=List[Dict[str, Any]])
async def list_emails(
    limit: int = 50,
    offset: int = 0,
    threat_level: Optional[str] = None,
    sender: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
):
    """Lists and searches ingested emails with threat scores."""
    stmt = (
        select(EmailRecord, AnalysisResult)
        .outerjoin(AnalysisResult, EmailRecord.id == AnalysisResult.email_id)
        .order_by(desc(EmailRecord.ingested_at))
        .limit(limit)
        .offset(offset)
    )
    if sender:
        stmt = stmt.where(EmailRecord.sender.ilike(f"%{sender}%"))
    if threat_level:
        stmt = stmt.where(AnalysisResult.threat_level == threat_level.upper())

    results = await db.execute(stmt)
    rows = results.all()

    output = []
    for email_rec, analysis_rec in rows:
        output.append({
            "id": email_rec.id,
            "message_id": email_rec.message_id,
            "subject": email_rec.subject,
            "sender": email_rec.sender,
            "sender_domain": email_rec.sender_domain,
            "recipient": email_rec.recipient,
            "date": email_rec.date,
            "source": email_rec.source,
            "sha256_hash": email_rec.sha256_hash,
            "ingested_at": email_rec.ingested_at,
            "status": email_rec.status,
            "threat_score": analysis_rec.overall_threat_score if analysis_rec else 0.0,
            "threat_level": analysis_rec.threat_level if analysis_rec else "LOW",
            "primary_classification": analysis_rec.primary_classification if analysis_rec else "legitimate",
            "origin_ip": analysis_rec.origin_assessment.get("probable_origin_ip") if analysis_rec and analysis_rec.origin_assessment else "Unknown",
            "origin_country": analysis_rec.origin_assessment.get("geolocation", {}).get("country_code") if analysis_rec and analysis_rec.origin_assessment else "XX"
        })

    return output

@router.get("/{email_id}", response_model=Dict[str, Any])
async def get_email_details(
    email_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns complete detail and forensic evidence for a specific email."""
    stmt = select(EmailRecord).where(EmailRecord.id == email_id)
    res = await db.execute(stmt)
    email_rec = res.scalar_one_or_none()
    if not email_rec:
        raise HTTPException(status_code=404, detail="Email record not found.")

    stmt_analysis = select(AnalysisResult).where(AnalysisResult.email_id == email_id)
    res_analysis = await db.execute(stmt_analysis)
    analysis = res_analysis.scalar_one_or_none()

    stmt_evidence = select(EvidenceVault).where(EvidenceVault.email_id == email_id)
    res_evidence = await db.execute(stmt_evidence)
    evidence = res_evidence.scalar_one_or_none()

    return {
        "email": model_to_dict(email_rec),
        "analysis": model_to_dict(analysis),
        "evidence": model_to_dict(evidence)
    }

@router.get("/{email_id}/report")
async def get_email_forensic_report(
    email_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns structured JSON forensic intelligence report."""
    data = await get_email_details(email_id, db)
    email_rec = data["email"] or {}
    analysis = data["analysis"] or {}
    evidence = data["evidence"] or {}

    return {
        "report_id": f"REP-{email_id[:8].upper()}",
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "email_id": email_rec.get("id"),
        "overall_threat_score": analysis.get("overall_threat_score", 0.0),
        "threat_level": analysis.get("threat_level", "LOW"),
        "classification": {
            "primary": analysis.get("primary_classification", "legitimate"),
            "confidence": analysis.get("classification_confidence", 0.0),
            "model_contributions": analysis.get("model_contributions", {})
        },
        "authentication": {
            "spf": analysis.get("auth_spf", {}),
            "dkim": analysis.get("auth_dkim", {}),
            "dmarc": analysis.get("auth_dmarc", {})
        },
        "header_analysis": {
            "anomalies": analysis.get("header_anomalies", []),
            "relay_hops": analysis.get("relay_hops_count", 0),
            "earliest_reliable_hop": analysis.get("earliest_reliable_hop", {})
        },
        "content_analysis": analysis.get("content_analysis", {}),
        "domain_intel": analysis.get("domain_intel", {}),
        "origin_assessment": analysis.get("origin_assessment", {}),
        "attribution": analysis.get("attribution_assessment", {}),
        "threat_intel": analysis.get("threat_intel_matches", {}),
        "evidence": {
            "sha256": email_rec.get("sha256_hash", ""),
            "chain_of_custody_id": evidence.get("chain_of_custody_id", ""),
            "preserved_at": evidence.get("created_at", ""),
            "chain_entries_count": len(evidence.get("chain_entries", []))
        },
        "recommendations": analysis.get("recommendations", [])
    }

@router.get("/{email_id}/report/pdf")
async def download_pdf_report(
    email_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Generates and downloads the official court-admissible PDF forensic report."""
    data = await get_email_details(email_id, db)
    email_rec = data["email"] or {}
    analysis = data["analysis"] or {}
    evidence = data["evidence"] or {}

    email_dict = {
        "subject": email_rec.get("subject", ""),
        "from_raw": email_rec.get("sender", ""),
        "recipient": email_rec.get("recipient", ""),
        "message_id": email_rec.get("message_id", ""),
        "sha256_hash": email_rec.get("sha256_hash", "")
    }
    analysis_dict = {
        "overall_threat_score": analysis.get("overall_threat_score", 0.0),
        "threat_level": analysis.get("threat_level", "LOW"),
        "primary_classification": analysis.get("primary_classification", "legitimate"),
        "auth_spf": analysis.get("auth_spf", {}),
        "auth_dkim": analysis.get("auth_dkim", {}),
        "auth_dmarc": analysis.get("auth_dmarc", {}),
        "origin_assessment": analysis.get("origin_assessment", {}),
        "attribution_assessment": analysis.get("attribution_assessment", {}),
        "domain_intel": analysis.get("domain_intel", {}),
        "content_analysis": analysis.get("content_analysis", {}),
        "recommendations": analysis.get("recommendations", [])
    }
    evidence_dict = {
        "chain_of_custody_id": evidence.get("chain_of_custody_id", "COC-001"),
        "chain_entries": evidence.get("chain_entries", [])
    }

    pdf_bytes = ReportingService.generate_pdf_report(email_dict, analysis_dict, evidence_dict)
    
    filename = f"SENTRY_Forensic_Report_{email_id[:8]}.pdf"
    return StreamingResponse(
        io.BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )

@router.get("/{email_id}/graph")
async def get_email_graph(
    email_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Returns local graph node network centered around the email."""
    graph_data = CorrelationEngine.get_graph_data(focus_email_id=email_id)
    return graph_data
