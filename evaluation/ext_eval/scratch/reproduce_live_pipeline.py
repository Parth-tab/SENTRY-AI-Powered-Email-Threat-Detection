import asyncio
import os
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

import json
import re
from datetime import datetime, timezone
import io
from app.config import settings

from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.services.threat_intel import ThreatIntelService
from app.services.correlation_engine import CorrelationEngine
from app.services.reporting import ReportingService
from app.ml.classifier import ThreatClassifier
from app.schemas.email import EmailResponse, EmailDetailResponse
from app.schemas.analysis import AnalysisResultResponse

async def main():
    eml_path = Path("tests/fixtures/advance_fee_lottery.eml")
    raw_bytes = eml_path.read_bytes()

    print("=" * 80)
    print("PHASE 0: LIVE PIPELINE REPRODUCTION RUN")
    print("=" * 80)

    # 1. Ingestion
    email_data = IngestionService.parse_raw_email(raw_bytes, source="eml_upload")
    print(f"\n[1. INGESTION LAYER]")
    print(f"  SHA-256 Digest: {email_data['sha256_hash']}")
    print(f"  Subject (Ingestion): {email_data['subject']} (len={len(email_data['subject'])})")
    print(f"  Sender: {email_data['sender']}")
    print(f"  Sender Domain: {email_data['sender_domain']}")
    print(f"  Recipient: {email_data['recipient']}")
    print(f"  Vault Path: {email_data['vault_path']}")
    print(f"  Reply-To in headers dict: {email_data['headers'].get('Reply-To')}")

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
    print(f"\n[2. HEADER FORENSICS LAYER]")
    print(f"  Hops Count: {len(hops)}")
    print(f"  Earliest Reliable Hop: {json.dumps(earliest_hop, default=str, indent=4)}")
    print(f"  Authentication Results: {json.dumps(auth_results, indent=4)}")
    print(f"  Header Anomalies: {all_anomalies}")

    # 3. Geo Origin
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))
    print(f"\n[3. GEO ORIGIN LAYER]")
    print(f"  Probable Origin IP: {origin_res.get('probable_origin_ip')}")
    print(f"  Geolocation: {json.dumps(origin_res.get('geolocation'), indent=4)}")
    print(f"  Anonymization: {json.dumps(origin_res.get('anonymization'), indent=4)}")
    print(f"  Confidence: {origin_res.get('confidence')}")

    # 4. Content Analysis
    content_res = ContentAnalysisService.analyze_content(email_data)
    print(f"\n[4. CONTENT ANALYSIS LAYER]")
    print(f"  Linguistic Scores: {json.dumps({k: v for k, v in content_res.items() if 'score' in k}, indent=4)}")
    print(f"  Extracted URLs: {content_res.get('urls_found')}")
    print(f"  Keywords Matched: {content_res.get('keywords_matched')}")

    # 5. Domain Intel
    domain_res = DomainIntelService.analyze_domain(
        email_data.get("sender_domain", ""),
        sender_ip=earliest_hop.get("from_ip") if (earliest_hop and isinstance(earliest_hop, dict)) else None
    )
    print(f"\n[5. DOMAIN INTEL LAYER]")
    print(f"  Domain: {domain_res.get('domain')}")
    print(f"  Is Lookalike: {domain_res.get('is_lookalike')}")
    print(f"  Lookalike Details: {domain_res.get('lookalike_details')}")

    # 6. Threat Intel
    threat_intel_res = await ThreatIntelService.evaluate_threat_intelligence(
        ip=origin_res.get("probable_origin_ip") or "",
        domain=domain_res.get("domain", ""),
        urls=content_res.get("urls_found", [])
    )
    print(f"\n[6. THREAT INTEL LAYER]")
    print(f"  Corroboration Score: {threat_intel_res.get('corroboration_score')}")
    print(f"  Matched IOCs: {threat_intel_res.get('matched_iocs')}")

    # 7. Correlation Engine
    attribution_res = CorrelationEngine.correlate(email_data, origin_res, domain_res, content_res)
    print(f"\n[7. CORRELATION LAYER]")
    print(f"  Campaign ID: {attribution_res.get('campaign_id')}")
    print(f"  Threat Actor: {attribution_res.get('threat_actor')}")

    # 8. ML Multi-Signal Classification
    classification_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res,
        threat_intel_res=threat_intel_res
    )
    print(f"\n[8. CLASSIFICATION LAYER]")
    print(f"  Primary Classification: {classification_res.get('primary_classification')}")
    print(f"  Classification Confidence: {classification_res.get('classification_confidence')}")
    print(f"  Threat Level: {classification_res.get('threat_level')}")
    print(f"  Overall Threat Score: {classification_res.get('overall_threat_score')}")
    print(f"  Model Contributions: {json.dumps(classification_res.get('model_contributions'), indent=4)}")
    print(f"  Rule Reasons: {classification_res.get('rule_reasons')}")
    print(f"  Recommendations: {json.dumps(classification_res.get('recommendations'), indent=4)}")

    # 9. Evidence Vault & Chain of Custody
    coc_id, chain_entries, last_hash = ReportingService.initialize_chain_of_custody(
        email_id=email_data["email_id"],
        sha256_hash=email_data["sha256_hash"],
        source="eml_upload"
    )
    chain_entries, last_hash = ReportingService.append_chain_entry(
        entries=chain_entries,
        action="AUTOMATED_FORENSIC_ANALYSIS",
        actor="SENTRY_CORRELATION_ENGINE",
        details=f"Extracted {len(hops)} relay hops, verified SPF/DKIM/DMARC, classified as {classification_res['threat_level']} ({classification_res['overall_threat_score']:.2f})"
    )
    evidence_data = {
        "chain_of_custody_id": coc_id,
        "chain_entries": chain_entries,
        "last_entry_hash": last_hash,
        "sha256_hash": email_data["sha256_hash"]
    }
    print(f"\n[9. EVIDENCE VAULT & HASH CHAIN]")
    print(f"  Chain of Custody ID: {coc_id}")
    print(f"  Last Entry Hash: {last_hash} (regex match: {bool(re.match(r'^[0-9a-f]{64}$', last_hash))})")
    for idx, entry in enumerate(chain_entries):
        print(f"    Entry {entry['step_number']}: timestamp='{entry['timestamp']}' action='{entry['action']}' hash='{entry['entry_hash']}' (hash regex: {bool(re.match(r'^[0-9a-f]{64}$', entry['entry_hash']))})")

    # 10. PDF Report Generation & Inspection
    analysis_data_for_pdf = {
        "overall_threat_score": classification_res["overall_threat_score"],
        "threat_level": classification_res["threat_level"],
        "primary_classification": classification_res["primary_classification"],
        "auth_spf": auth_results.get("spf"),
        "auth_dkim": auth_results.get("dkim"),
        "auth_dmarc": auth_results.get("dmarc"),
        "origin_assessment": origin_res,
        "domain_intel": domain_res,
        "content_analysis": content_res,
        "attribution_assessment": attribution_res,
        "recommendations": classification_res["recommendations"]
    }
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data=email_data,
        analysis_data=analysis_data_for_pdf,
        evidence_data=evidence_data
    )
    print(f"\n[10. PDF REPORT LAYER]")
    print(f"  PDF Generated: {len(pdf_bytes)} bytes")

    # Inspect PDF bytes / stream text directly
    pdf_text = pdf_bytes.decode("latin1", errors="replace")

    # Inspect PDF Subject rendering via raw PDF strings
    subject_match = re.findall(r'\(([^)]+)\)', pdf_text)
    print(f"\n  PDF String Elements (first 25): {subject_match[:25]}")
    
    # Check hashes in PDF
    pdf_hashes = re.findall(r'[0-9a-f]{64}', pdf_text, re.IGNORECASE)
    print(f"  PDF 64-char Hex Hashes found: {len(pdf_hashes)} occurrences ({pdf_hashes})")

    # Check IOC Table extracted from PDF
    print(f"\n[11. IOC TABLE CONTENTS (REPORT GENERATOR)]")
    # Let's inspect what ReportingService.generate_pdf_report created for IOCs:
    iocs = []
    if origin_res.get("probable_origin_ip") and origin_res.get("probable_origin_ip") != "Unknown":
        iocs.append(["IPv4 Address", origin_res.get("probable_origin_ip"), "Originating SMTP Client"])
    if domain_res.get("domain"):
        iocs.append(["Domain", domain_res.get("domain"), f"Sender Domain (Lookalike: {domain_res.get('is_lookalike')})"])
    
    # Reply-To structured IOC extraction
    reply_to_raw = email_data.get("reply_to") or email_data.get("headers", {}).get("Reply-To") or ""
    if reply_to_raw:
        from email.utils import parseaddr
        _, r_email = parseaddr(str(reply_to_raw))
        if r_email:
            r_domain = r_email.split("@")[-1].lower() if "@" in r_email else ""
            s_domain = str(email_data.get("sender_domain", "")).lower()
            is_mismatch = bool(r_domain and s_domain and r_domain != s_domain)
            iocs.append(["Reply-To Email", r_email, f"Response Routing (Mismatch: {is_mismatch})"])
            if is_mismatch and r_domain:
                iocs.append(["Reply-To Domain", r_domain, f"External Diversion Channel (From: {s_domain})"])

    for u in content_res.get("urls_found", [])[:3]:
        iocs.append(["URL", u.get("url", ""), "Extracted Payload Link"])
    for ioc_row in iocs:
        print(f"  IOC Row: {ioc_row}")

    # Return full output payload
    return {
        "email_data": email_data,
        "header_res": header_res,
        "origin_res": origin_res,
        "content_res": content_res,
        "domain_res": domain_res,
        "threat_intel_res": threat_intel_res,
        "attribution_res": attribution_res,
        "classification_res": classification_res,
        "evidence_data": evidence_data,
        "pdf_text": pdf_text
    }

if __name__ == "__main__":
    asyncio.run(main())
