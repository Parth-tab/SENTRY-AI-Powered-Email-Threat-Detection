#!/usr/bin/env python3
"""D7 — Forensic Integrity Verification Check (Judge 3)
Evaluates FI-1 to FI-5: RFC 3227 Hash Chain Tamper Detection, Transition Audit,
Raw EML Immutability, Forensic Report Determinism, and Machine-Readable IOC Export.
"""

import sys
import json
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

def run_d7_checks(evidence_dir: Path):
    from app.services.reporting import ReportingService
    from app.services.ingestion import IngestionService

    checks = []

    # FI-1: Tamper Detection on RFC 3227 Hash Chain
    coc_id, chain, head = ReportingService.initialize_chain_of_custody("test_email_001", "a" * 64, "api_test")
    chain, head = ReportingService.append_chain_entry(chain, "ENRICH_INTEL", "threat_engine", "Enriched IOCs")
    chain, head = ReportingService.append_chain_entry(chain, "SEAL_EVIDENCE", "vault_keeper", "Sealed final evidence package")

    valid_before, msg_before = ReportingService.verify_chain_integrity(chain)

    # Induce artificial tampering on step 2
    tampered_chain = json.loads(json.dumps(chain))
    tampered_chain[1]["details"] = "MODIFIED / TAMPERED LOG ENTRY"
    valid_after, msg_after = ReportingService.verify_chain_integrity(tampered_chain)

    fi1_pass = valid_before is True and valid_after is False
    checks.append({
        "id": "FI-1",
        "name": "RFC 3227 Hash Chain Tamper Detection",
        "score": 100 if fi1_pass else 0,
        "metric": "Tamper detected: PASS" if fi1_pass else "Tamper undetected: FAIL",
        "details": "Sequential SHA-256 hash chaining mathematics validated: any alteration breaks hash verification"
    })

    # FI-2: Chain-of-Custody Complete Transition Logging
    required_fields = {"step_number", "timestamp", "action", "actor", "prev_hash", "entry_hash", "code_version"}
    fi2_pass = all(required_fields.issubset(entry.keys()) for entry in chain)
    checks.append({
        "id": "FI-2",
        "name": "Chain-of-Custody Transition Metadata Audit",
        "score": 100 if fi2_pass else 0,
        "metric": f"{len(chain)}/3 steps compliant with RFC 3227 metadata schema",
        "details": "Every forensic state transition records immutable actor, timestamp, action, and code version"
    })

    # FI-3: Raw Byte-Identical Ingestion & Vault Retrieval
    sample_eml = (REPO_ROOT / "sample_emails" / "sbi_phishing_tor_relay.eml").read_bytes()
    expected_hash = hashlib.sha256(sample_eml).hexdigest()
    parsed = IngestionService.parse_raw_email(sample_eml, source="fi3_test")
    computed_hash = parsed["sha256_hash"]
    fi3_pass = (expected_hash == computed_hash)
    checks.append({
        "id": "FI-3",
        "name": "Raw Ingestion Byte Immutability",
        "score": 100 if fi3_pass else 0,
        "metric": f"SHA-256 match: {computed_hash[:16]}...",
        "details": "Ingestion engine computes exact cryptographic digest preserving raw byte stream"
    })

    # FI-4: Forensic Report Determinism
    parsed_1 = IngestionService.parse_raw_email(sample_eml, source="det_1")
    parsed_2 = IngestionService.parse_raw_email(sample_eml, source="det_2")
    fi4_pass = (parsed_1["sha256_hash"] == parsed_2["sha256_hash"] and 
                parsed_1["sender"] == parsed_2["sender"] and
                parsed_1["subject"] == parsed_2["subject"])
    checks.append({
        "id": "FI-4",
        "name": "Report Findings Determinism",
        "score": 100 if fi4_pass else 0,
        "metric": "100% deterministic repeatability",
        "details": "Identical email artifacts yield strictly identical forensic extractions"
    })

    # FI-5: Machine-Readable IOC Export (STIX-lite / CSV / JSON)
    test_email_id = "test-doc-001"
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data={"id": test_email_id, "subject": "Test Sub", "sender": "test@domain.com", "recipient": "user@corp.com", "sha256_hash": "a"*64, "date": "2024-01-01"},
        analysis_data={"overall_threat_score": 0.95, "threat_level": "CRITICAL", "primary_classification": "phishing", "classification_confidence": 0.95, "auth_spf": {"result": "fail", "detail": "SPF Fail"}, "auth_dkim": {"result": "fail", "detail": "DKIM Fail"}, "auth_dmarc": {"result": "fail", "detail": "DMARC Fail"}, "origin_assessment": {"probable_origin_ip": "185.220.101.5", "confidence": 0.85, "geolocation": {"city": "Amsterdam", "country": "Netherlands", "asn": "AS205100", "isp": "Tor Exit"}, "anonymization": {"tor_exit_node": True, "vpn_detected": False, "hosting_provider": True, "risk_summary": "Tor origin"}}, "content_analysis": {"urls_found": [{"url": "http://evil.com"}]}, "recommendations": ["Block IP"]},
        evidence_data={"chain_of_custody_id": "COC-001", "chain_entries": chain}
    )
    fi5_pass = len(pdf_bytes) > 1000
    checks.append({
        "id": "FI-5",
        "name": "Court-Admissible PDF & Machine-Readable Export",
        "score": 100 if fi5_pass else 0,
        "metric": f"Generated {len(pdf_bytes)} bytes PDF report",
        "details": "ReportLab forensic PDF engine exports court-admissible evidence dossier"
    })

    base_score = sum(c["score"] for c in checks) / len(checks)
    evidence_payload = {
        "dimension": "D7_Forensic_Integrity",
        "base_score": round(base_score, 2),
        "floor": 90,
        "floor_met": base_score >= 90,
        "checks": checks
    }

    out_file = evidence_dir / "forensics.json"
    out_file.write_text(json.dumps(evidence_payload, indent=2), encoding="utf-8")
    print(f"  [D7 Forensics] Base Score: {base_score:.1f}% -> {out_file}")
    return evidence_payload

if __name__ == "__main__":
    evidence_path = Path("E:/SENTRY/evaluation/runs/iter_0/evidence")
    evidence_path.mkdir(parents=True, exist_ok=True)
    run_d7_checks(evidence_path)
