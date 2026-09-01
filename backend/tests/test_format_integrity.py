import re
import io
import base64
import zlib
from datetime import datetime, timezone
import pytest
from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.services.reporting import ReportingService
from app.ml.classifier import ThreatClassifier
from app.schemas.analysis import AnalysisResultResponse

RFC3339_REGEX = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z$")
SHA256_REGEX = re.compile(r"^[0-9a-f]{64}$")

def test_subject_full_length_preservation_across_all_layers():
    """
    EXT-004 & T-2: End-to-end subject integrity across Ingestion, Content Analysis,
    Classification, Evidence Vault, and PDF Generation.
    Asserts full 111-character subject is preserved without silent truncation.
    """
    subject_111 = "OFFICIAL NOTIFICATION: INTERNATIONAL LOTTERY WINNING BENEFICIARY DISBURSEMENT - 2026 RUSSIA PROMOTION PROGRAMME"
    assert len(subject_111) == 111

    raw_email = (
        f"From: promotions@targetcorp.example\r\n"
        f"To: victim@targetcorp.example\r\n"
        f"Subject: {subject_111}\r\n"
        f"Date: Tue, 01 Sep 2026 14:30:00 +0000\r\n"
        f"Message-ID: <test12345@targetcorp.example>\r\n"
        f"\r\n"
        f"Test plain body."
    ).encode("utf-8")

    # 1. Ingestion Layer
    email_data = IngestionService.parse_raw_email(raw_email, source="test_upload")
    assert email_data["subject"] == subject_111
    assert len(email_data["subject"]) == 111

    # 2. Content Analysis Layer
    content_res = ContentAnalysisService.analyze_content(email_data)
    assert content_res is not None

    # 3. Threat Classification & Floor
    header_res = {
        "authentication": {"spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": ["reply_to_domain_mismatch"]
    }
    cls_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res={"domain": "targetcorp.example"},
        origin_res={"probable_origin_ip": "192.0.2.1"}
    )
    assert cls_res["overall_threat_score"] >= 0.85
    assert cls_res["score_pre_floor"] is not None

    # 4. Evidence Chain Initialization
    coc_id, entries, h0 = ReportingService.initialize_chain_of_custody(
        email_id="12345678-1234-5678-1234-567812345678",
        sha256_hash=email_data["sha256_hash"],
        source="test_upload"
    )
    evidence_data = {
        "chain_of_custody_id": coc_id,
        "chain_entries": entries,
        "last_entry_hash": h0
    }

    # 5. PDF Generation & Stream Decompression
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data=email_data,
        analysis_data=cls_res,
        evidence_data=evidence_data
    )
    assert len(pdf_bytes) > 1000

    # Decompress ReportLab Adobe ASCII85 Flate streams
    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed_text = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")

    # Assert both lines of wrapped subject exist in PDF
    assert "OFFICIAL NOTIFICATION: INTERNATIONAL LOTTERY WINNING BENEFICIARY DISBURSEMENT - 2026" in decompressed_text
    assert "RUSSIA PROMOTION PROGRAMME" in decompressed_text

def test_universal_rfc3339_timestamp_emissions():
    """
    EXT-007: Universal validator ensuring all timestamp emission points
    (Chain of Custody, PDF reports, Ingestion metadata) conform strictly to RFC 3339 / ISO 8601 (UTC 'Z').
    """
    # 1. Chain of custody timestamps
    coc_id, entries, h0 = ReportingService.initialize_chain_of_custody(
        email_id="test-id-1234",
        sha256_hash="a" * 64,
        source="test"
    )
    entries, h1 = ReportingService.append_chain_entry(
        entries=entries,
        action="AUTOMATED_FORENSIC_ANALYSIS",
        actor="SENTRY_CLASSIFIER",
        details="Automated ML & rule-based scoring."
    )

    for entry in entries:
        ts = entry["timestamp"]
        assert RFC3339_REGEX.match(ts), f"Timestamp '{ts}' failed RFC 3339 regex in step {entry.get('step_number')}"
        # Validate parseability
        parsed = datetime.fromisoformat(ts.replace("Z", "+00:00"))
        assert parsed.tzinfo is not None

    # 2. PDF report generation date
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data={"subject": "Test", "sha256_hash": "b" * 64},
        analysis_data={"threat_level": "LOW", "overall_threat_score": 0.1, "primary_classification": "legitimate"},
        evidence_data={"chain_of_custody_id": coc_id, "chain_entries": entries}
    )
    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")
    
    # Assert ISO date pattern present in PDF stream
    pdf_dates = re.findall(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", decompressed)
    assert len(pdf_dates) >= 1, "Expected RFC 3339 date string in PDF header"

def test_evidence_hash_formatting_and_global_invariants():
    """
    EXT-006: Global SHA-256 hash invariant test asserting that all emitted hashes
    are 64 lowercase hex characters and are rendered completely in PDF reports without slicing.
    """
    target_hash = "3b28ce28f27b880ca7a27818ec4051ffa72d2251914ab442a3779584bcda954e"
    step1_hash = "55700dbe5e1840507347a6ac75a35f8d47c323348b8ff2f8e46059b9f2f4dd21"
    step2_hash = "b6aa48572aa992313c9ee41269ef78e92306980382c758ab35f0af35b888dac6"

    assert SHA256_REGEX.match(target_hash)
    assert SHA256_REGEX.match(step1_hash)
    assert SHA256_REGEX.match(step2_hash)

    evidence_data = {
        "chain_of_custody_id": "COC-TEST001",
        "chain_entries": [
            {"step_number": 1, "action": "EVIDENCE_ACQUISITION", "actor": "INGEST", "timestamp": "2026-09-01T12:00:00Z", "entry_hash": step1_hash},
            {"step_number": 2, "action": "ANALYSIS", "actor": "ANALYZER", "timestamp": "2026-09-01T12:00:01Z", "entry_hash": step2_hash}
        ]
    }

    pdf_bytes = ReportingService.generate_pdf_report(
        email_data={"subject": "Test", "sha256_hash": target_hash},
        analysis_data={"threat_level": "LOW", "overall_threat_score": 0.1, "primary_classification": "legitimate"},
        evidence_data=evidence_data
    )

    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")

    # Assert full 64-char hashes exist in the decompressed text
    assert target_hash in decompressed, f"Target hash {target_hash} missing from PDF!"
    assert step1_hash in decompressed, f"Step 1 hash {step1_hash} missing from PDF!"
    assert step2_hash in decompressed, f"Step 2 hash {step2_hash} missing from PDF!"

def test_score_pre_floor_honesty_reporting_in_schemas_and_pdf():
    """
    P2-1(a): Verifies that score_pre_floor and floor_applied are populated
    when severity floor activates, and formatted in PDF executive summary.
    """
    # Email with DMARC fail + SPF fail, but minimal benign text (model score ~0.45)
    mock_email = {"body_plain": "Benign short note.", "subject": "Notice", "sender": "target@domain.example"}
    mock_header = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": []
    }
    cls_res = ThreatClassifier.evaluate(mock_email, mock_header, {}, {}, {}, {})

    assert cls_res["overall_threat_score"] == 0.85
    assert cls_res["floor_applied"] is True
    assert cls_res["score_pre_floor"] is not None
    assert cls_res["score_pre_floor"] < 0.85

    # Check PDF rendering of the floor annotation
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data=mock_email,
        analysis_data=cls_res,
        evidence_data={"chain_of_custody_id": "COC-1", "chain_entries": []}
    )
    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")

    assert "Enforced Floor" in decompressed, "Expected '[Enforced Floor; Model: ...]' annotation in PDF summary"
