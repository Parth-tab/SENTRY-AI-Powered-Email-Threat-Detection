import pytest
from app.services.reporting import ReportingService

def test_rfc_3227_hash_chain_integrity():
    email_id = "test-uuid-1234"
    sha = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
    
    coc_id, chain, h0 = ReportingService.initialize_chain_of_custody(email_id, sha, "test_upload")
    assert len(chain) == 1
    assert chain[0]["entry_hash"] == h0

    chain, h1 = ReportingService.append_chain_entry(chain, "FORENSIC_TRIAGE", "AGENT_A", "Triage completed")
    assert len(chain) == 2
    assert chain[1]["prev_hash"] == h0
    assert chain[1]["entry_hash"] == h1

    # Verify unbroken chain
    is_valid, msg = ReportingService.verify_chain_integrity(chain)
    assert is_valid is True

    # Tamper test: Alter step 1 payload details
    chain[0]["details"] = "TAMPERED DATA"
    is_valid_after_tamper, msg_tamper = ReportingService.verify_chain_integrity(chain)
    assert is_valid_after_tamper is False
    assert "Tampering detected" in msg_tamper

def test_pdf_report_generation():
    email_dict = {
        "subject": "Test Security Warning",
        "from_raw": "Security Desk <alert@test.com>",
        "recipient": "analyst@test.com",
        "message_id": "<test-msg-123>",
        "sha256_hash": "a" * 64
    }
    analysis_dict = {
        "overall_threat_score": 0.92,
        "threat_level": "CRITICAL",
        "primary_classification": "phishing",
        "auth_spf": {"result": "fail"},
        "auth_dkim": {"result": "none"},
        "auth_dmarc": {"result": "fail"},
        "origin_assessment": {"probable_origin_ip": "185.220.101.34", "geolocation": {"country": "Netherlands", "city": "Amsterdam", "asn": "AS205100", "isp": "Tor Relay"}},
        "attribution_assessment": {"campaign_id": "CMP-2024-0034", "actor_sophistication": "medium-high"},
        "domain_intel": {"domain": "apex-secureverify.com", "is_lookalike": True},
        "content_analysis": {"urls_found": [{"url": "https://apex-secureverify.com/login"}]},
        "recommendations": ["Block IP immediately", "Revoke credentials"]
    }
    evidence_dict = {
        "chain_of_custody_id": "COC-TEST-001",
        "chain_entries": [{"step_number": 1, "action": "INGESTION", "actor": "SENTRY", "timestamp": "2024-01-15T10:00:00Z", "entry_hash": "b"*64}]
    }

    pdf_bytes = ReportingService.generate_pdf_report(email_dict, analysis_dict, evidence_dict)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes.startswith(b"%PDF")
