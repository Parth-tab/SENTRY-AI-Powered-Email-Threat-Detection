import re
import pytest
from app.ml.classifier import ThreatClassifier
from app.services.reporting import ReportingService
from app.services.header_forensics import HeaderForensicsService

def test_countermeasure_self_spoof_scenario_matrix():
    """
    EXT-008: 4-Scenario Matrix for Countermeasure Routing.
    Guarantees that SENTRY structurally refuses to recommend blocking the internal domain
    when self-spoofing is detected (derived from recipient_domain == sender_domain).
    """
    # -------------------------------------------------------------------------
    # Scenario 1: Self-Spoof with External Reply-To (Advance-Fee / Lottery Phish)
    # -------------------------------------------------------------------------
    email_s1 = {
        "sender": "promotions@targetcorp.example",
        "sender_domain": "targetcorp.example",
        "recipient": "victim@targetcorp.example",
        "reply_to": "claims-agent@example.com",
        "headers": {"reply-to": "claims-agent@example.com"}
    }
    header_s1 = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": ["reply_to_domain_mismatch"]
    }
    res_s1 = ThreatClassifier.evaluate(email_s1, header_s1, {"financial_score": 0.5}, {"domain": "targetcorp.example"}, {"probable_origin_ip": "192.0.2.1"})
    recs_s1 = res_s1["recommendations"]

    assert any("Enforce strict DMARC 'p=reject'" in r for r in recs_s1)
    assert any("SEG) anti-spoofing filter" in r for r in recs_s1)
    assert any("Block external diversion Reply-To domain 'example.com'" in r for r in recs_s1)
    assert not any("Block sender domain 'targetcorp.example'" in r for r in recs_s1), (
        "CRITICAL ERROR: Self-spoof countermeasure recommended self-DoS rule: 'Block sender domain targetcorp.example'!"
    )

    # -------------------------------------------------------------------------
    # Scenario 2: External Lookalike / Foreign Phishing
    # -------------------------------------------------------------------------
    email_s2 = {
        "sender": "alerts@targetc0rp.example",
        "sender_domain": "targetc0rp.example",
        "recipient": "victim@targetcorp.example",
        "reply_to": ""
    }
    header_s2 = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": []
    }
    res_s2 = ThreatClassifier.evaluate(email_s2, header_s2, {"credential_score": 0.5}, {"domain": "targetc0rp.example", "is_lookalike": True}, {"probable_origin_ip": "198.51.100.20"})
    recs_s2 = res_s2["recommendations"]

    assert any("Block sender domain 'targetc0rp.example'" in r for r in recs_s2)
    assert not any("internal domain" in r for r in recs_s2)

    # -------------------------------------------------------------------------
    # Scenario 3: Self-Spoof without Reply-To (Internal Executive BEC Impersonation)
    # -------------------------------------------------------------------------
    email_s3 = {
        "sender": "ceo@targetcorp.example",
        "sender_domain": "targetcorp.example",
        "recipient": "finance@targetcorp.example",
        "reply_to": ""
    }
    header_s3 = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": []
    }
    res_s3 = ThreatClassifier.evaluate(email_s3, header_s3, {"financial_score": 0.5, "authority_score": 0.5}, {"domain": "targetcorp.example"}, {})
    recs_s3 = res_s3["recommendations"]

    assert any("Enforce strict DMARC 'p=reject'" in r for r in recs_s3)
    assert any("anti-spoofing filter" in r for r in recs_s3)
    assert not any("Block sender domain 'targetcorp.example'" in r for r in recs_s3)

    # -------------------------------------------------------------------------
    # Scenario 4: Legitimate Internal Communication
    # -------------------------------------------------------------------------
    email_s4 = {
        "sender": "ceo@targetcorp.example",
        "sender_domain": "targetcorp.example",
        "recipient": "finance@targetcorp.example",
        "reply_to": ""
    }
    header_s4 = {
        "authentication": {"is_spoofed": False, "spf": {"result": "pass"}, "dmarc": {"result": "pass"}},
        "header_anomalies": []
    }
    res_s4 = ThreatClassifier.evaluate(email_s4, header_s4, {}, {"domain": "targetcorp.example"}, {})
    recs_s4 = res_s4["recommendations"]

    assert res_s4["threat_level"] == "LOW"
    assert any("allow delivery to inbox" in r for r in recs_s4)

def test_mutation_kill_self_spoof_prevents_self_dos_rule():
    """
    EXT-008 Mutation Kill Assertion:
    Verifies that self-spoofed internal email NEVER outputs 'Block sender domain <own_domain>'.
    If the self-spoof branch is removed/mutated, this test fails explicitly quoting the self-DoS lie.
    """
    email_data = {
        "sender": "admin@targetcorp.example",
        "sender_domain": "targetcorp.example",
        "recipient": "employee@targetcorp.example",
        "reply_to": "attacker@evil.com"
    }
    header_res = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": ["reply_to_domain_mismatch"]
    }
    res = ThreatClassifier.evaluate(email_data, header_res, {}, {"domain": "targetcorp.example"}, {})

    self_dos_rule = "Block sender domain 'targetcorp.example' across perimeter email gateway (SEG)."
    assert self_dos_rule not in res["recommendations"], (
        f"Mutation Kill: Self-spoof countermeasure falsely recommended self-DoS rule: '{self_dos_rule}'"
    )
    assert any("DMARC 'p=reject'" in r for r in res["recommendations"])

def test_reply_to_ioc_extraction_and_dual_surface_display():
    """
    EXT-005: Asserts Reply-To email and domain are extracted into structured IOC rows
    and that mismatch discrepancies surface in both the IOC list and Header Anomaly panel.
    """
    email_data = {
        "sender": "promotions@targetcorp.example",
        "sender_domain": "targetcorp.example",
        "recipient": "victim@targetcorp.example",
        "reply_to": "claims-agent@example.com",
        "headers": {"reply-to": "Claims Officer Mikhail <claims-agent@example.com>"},
        "sha256_hash": "a" * 64,
        "subject": "Lottery Notification"
    }

    # 1. Header Anomaly Detection
    anomalies = HeaderForensicsService.detect_anomalies(email_data, earliest_hop={})
    assert "reply_to_domain_mismatch" in anomalies, "Expected reply_to_domain_mismatch in header anomalies panel!"

    # 2. PDF IOC Table Extraction
    pdf_bytes = ReportingService.generate_pdf_report(
        email_data=email_data,
        analysis_data={"threat_level": "CRITICAL", "overall_threat_score": 0.90, "primary_classification": "phishing"},
        evidence_data={"chain_of_custody_id": "COC-1", "chain_entries": []}
    )
    assert len(pdf_bytes) > 1000

    # Verify Reply-To structured elements in PDF stream
    import zlib, base64
    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")

    assert "Reply-To Email" in decompressed, "Expected 'Reply-To Email' row in PDF IOC table!"
    assert "claims-agent@example.com" in decompressed, "Expected Reply-To email value in PDF IOC table!"
    assert "Reply-To Domain" in decompressed, "Expected 'Reply-To Domain' row in PDF IOC table!"
    assert "example.com" in decompressed, "Expected Reply-To domain in PDF IOC table!"
