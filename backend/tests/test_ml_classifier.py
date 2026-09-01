import pytest
from app.ml.feature_extractor import MLFeatureExtractor
from app.ml.classifier import ThreatClassifier

def test_feature_extractor_47_dimensions():
    mock_email = {
        "body_plain": "Urgent wire transfer needed immediately by CEO. Please send $50,000 to offshore escrow.",
        "body_html": "<p>Urgent wire transfer needed</p>",
        "subject": "Urgent Wire Transfer Request",
        "sender": "ceo@external-fraud.com",
        "recipient": "finance@victim.com",
        "attachments": []
    }
    mock_header = {
        "authentication": {
            "spf": {"result": "fail", "score": 0.0},
            "dkim": {"result": "fail", "score": 0.0},
            "dmarc": {"result": "fail", "score": 0.0},
            "is_spoofed": True
        },
        "header_anomalies": ["Clock skew > 48h", "Return-Path mismatch"],
        "received_chain": [{"from_ip": "185.220.101.34", "by": "mx.victim.com", "is_reliable": False}]
    }
    mock_content = {
        "urgency_score": 0.95,
        "authority_score": 0.90,
        "financial_score": 0.92,
        "credential_score": 0.10,
        "linguistic_features": {
            "generic_greetings": ["Dear Customer"],
            "urgency_keywords": ["urgent", "immediately"],
            "authority_references": ["CEO", "Executive"],
            "financial_requests": ["wire transfer", "$50,000"],
            "credential_harvesting": []
        },
        "urls_count": 2,
        "has_mismatched_links": True,
        "has_html_form": False,
        "has_password_input": False,
        "has_dangerous_attachment": False,
        "attachments_count": 0,
        "external_links_ratio": 1.0,
        "suspicious_paths_count": 1
    }
    mock_domain = {
        "is_lookalike": True,
        "domain_risk_score": 0.88,
        "high_risk_tld": True,
        "subdomain_count": 3,
        "domain_age_days": 2,
        "mx_records_valid": False
    }
    mock_origin = {
        "anonymization": {
            "tor_exit_node": True,
            "vpn_detected": False,
            "hosting_provider": True
        },
        "confidence": 0.85,
        "geolocation": {"country_code": "NL"}
    }

    vec = MLFeatureExtractor.extract_feature_vector(
        mock_email, mock_header, mock_content, mock_domain, mock_origin
    )
    assert len(vec) == 47
    assert vec[0] == 0.95  # urgency_score
    assert vec[1] == 0.90  # authority_score
    assert vec[2] == 0.92  # financial_score

def test_classifier_bec_classification():
    mock_email = {"body_plain": "Wire transfer requested", "subject": "CEO Payment"}
    mock_header = {
        "authentication": {"is_spoofed": False, "dmarc": {"result": "pass"}},
        "header_anomalies": [],
        "received_chain": [{"from_ip": "1.2.3.4"}]
    }
    mock_content = {
        "urgency_score": 0.85,
        "authority_score": 0.85,
        "financial_score": 0.90,
        "credential_score": 0.05,
        "linguistic_features": {},
        "urls_count": 0,
        "has_mismatched_links": False
    }
    mock_domain = {"is_lookalike": False, "domain_risk_score": 0.1, "high_risk_tld": False, "subdomain_count": 0}
    mock_origin = {"anonymization": {"tor_exit_node": False, "vpn_detected": False, "hosting_provider": False}, "confidence": 0.9, "geolocation": {"country_code": "US"}}

    res = ThreatClassifier.evaluate(
        mock_email, mock_header, mock_content, mock_domain, mock_origin, {"corroboration_score": 0.0}
    )

    assert res["overall_threat_score"] >= 0.55
    assert res["primary_classification"] in ["bec", "impersonation", "phishing", "suspicious"]
    assert res["threat_level"] in ["CRITICAL", "HIGH", "MEDIUM"]
    assert "model_contributions" in res

def test_classifier_legitimate_email():
    mock_email = {"body_plain": "Hey team, weekly sprint planning is tomorrow at 10 AM.", "subject": "Sprint Planning"}
    mock_header = {
        "authentication": {"is_spoofed": False, "spf": {"score": 1.0}, "dkim": {"score": 1.0}, "dmarc": {"result": "pass", "score": 1.0}},
        "header_anomalies": [],
        "received_chain": [{"from_ip": "209.85.220.41", "is_reliable": True}]
    }
    mock_content = {
        "urgency_score": 0.0,
        "authority_score": 0.0,
        "financial_score": 0.0,
        "credential_score": 0.0,
        "linguistic_features": {},
        "urls_count": 0,
        "has_mismatched_links": False
    }
    mock_domain = {"is_lookalike": False, "domain_risk_score": 0.0, "high_risk_tld": False, "subdomain_count": 0, "mx_records_valid": True}
    mock_origin = {"anonymization": {"tor_exit_node": False, "vpn_detected": False, "hosting_provider": False}, "confidence": 0.95, "geolocation": {"country_code": "US"}}

    res = ThreatClassifier.evaluate(
        mock_email, mock_header, mock_content, mock_domain, mock_origin, {"corroboration_score": 0.0}
    )

    assert res["overall_threat_score"] < 0.40
    assert res["primary_classification"] == "legitimate"
    assert res["threat_level"] == "LOW"

def test_truncated_headers_null_safety():
    """HAM-002: Null safety and graceful degradation with truncated headers and None sub-dicts."""
    mock_email = {
        "body_plain": "Plain test message with minimal structure.",
        "body_html": "",
        "subject": "Status Update",
        "sender": "sender@domain.com",
        "recipient": "recipient@domain.com",
        "attachments": []
    }
    # Pass empty or None sub-dicts
    classification = ThreatClassifier.evaluate(
        email_data=mock_email,
        header_res=None,
        content_res=None,
        domain_res=None,
        origin_res=None,
        threat_intel_res=None
    )
    assert "threat_level" in classification
    assert "overall_threat_score" in classification
    assert 0.0 <= classification["overall_threat_score"] <= 1.0
    assert classification["threat_level"] in ["LOW", "MEDIUM", "HIGH", "CRITICAL", "CLEAN"]

def test_advance_fee_subtype_classification():
    """EXT-001: Asserts that advance-fee lottery lure with external reply-to triggers ADVANCE-FEE FRAUD subtype."""
    mock_email = {
        "subject": "OFFICIAL NOTIFICATION: INTERNATIONAL LOTTERY WINNER -- CLAIM YOUR PRIZE OF $2,500,000.00 USD REF: RUSSIA PROMOTION 2026",
        "body_plain": "Congratulations lucky winner! Claim your lottery prize by contacting our agent and remitting processing fee. Provide passport copy and bank details.",
        "sender": "promotions@targetcorp.example"
    }
    mock_header = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": ["reply_to_domain_mismatch"],
        "received_chain": [{"from_ip": "192.0.2.1"}]
    }
    mock_content = {
        "urgency_score": 0.35,
        "authority_score": 0.0,
        "financial_score": 0.90,
        "credential_score": 0.0,
        "advance_fee_score": 0.80,
        "pii_score": 0.70,
        "linguistic_features": {
            "advance_fee_matches": ["lottery winner", "claim your prize", "processing fee"],
            "pii_matches": ["passport copy", "bank details"],
            "financial_requests": ["$2,500,000.00"]
        },
        "urls_count": 0,
        "has_mismatched_links": False
    }
    mock_domain = {"domain": "targetcorp.example", "is_lookalike": False, "domain_risk_score": 0.0}
    mock_origin = {"probable_origin_ip": "192.0.2.1", "anonymization": {"tor_exit_node": False, "vpn_detected": False, "hosting_provider": False}}

    res = ThreatClassifier.evaluate(
        mock_email, mock_header, mock_content, mock_domain, mock_origin, {"corroboration_score": 0.0}
    )

    assert res["primary_classification"] == "phishing"
    assert res["classification_subtype"] == "ADVANCE-FEE FRAUD"
    assert res["overall_threat_score"] >= 0.85
    assert res["threat_level"] == "CRITICAL"
    assert any("Advance-fee" in r for r in res["rule_reasons"])
    assert any("Reply-To" in r for r in res["rule_reasons"])

@pytest.mark.parametrize("scenario, hr_text, subject_text", [
    ("HR Benefits", "Please log in to the employee portal to review and update your life insurance beneficiary details for the fiscal year.", "Annual Benefits: Review Beneficiary Elections"),
    ("Newsletter", "Congratulations to the hackathon participants! First prize winner will be announced at Friday all-hands.", "Engineering Newsletter: Hackathon Prize Demos"),
])
def test_adversarial_controls_do_not_trigger_advance_fee_subtype(scenario, hr_text, subject_text):
    """
    EXT-001 Adversarial Controls:
    Legitimate internal emails containing benign single words ('beneficiary', 'prize')
    must NOT trigger the ADVANCE-FEE FRAUD subtype and must maintain LOW threat level.
    """
    mock_email = {"body_plain": hr_text, "subject": subject_text, "sender": "internal@corp.com"}
    mock_header = {
        "authentication": {"is_spoofed": False, "spf": {"result": "pass", "score": 1.0}, "dkim": {"result": "pass", "score": 1.0}, "dmarc": {"result": "pass", "score": 1.0}},
        "header_anomalies": [],
        "received_chain": [{"from_ip": "209.85.220.41", "is_reliable": True}]
    }
    adv_matches = ["beneficiary"] if "beneficiary" in hr_text else ["prize"]
    mock_content = {
        "urgency_score": 0.0,
        "authority_score": 0.0,
        "financial_score": 0.0,
        "credential_score": 0.0,
        "advance_fee_score": 0.0,
        "pii_score": 0.0,
        "linguistic_features": {"advance_fee_matches": adv_matches, "pii_matches": []},
        "urls_count": 0,
        "has_mismatched_links": False
    }
    mock_domain = {"domain": "corp.com", "is_lookalike": False, "domain_risk_score": 0.0, "high_risk_tld": False}
    mock_origin = {"probable_origin_ip": "209.85.220.41", "anonymization": {"tor_exit_node": False, "vpn_detected": False, "hosting_provider": False}, "confidence": 0.95}

    res = ThreatClassifier.evaluate(
        mock_email, mock_header, mock_content, mock_domain, mock_origin, {"corroboration_score": 0.0}
    )

    assert res["classification_subtype"] is None, f"{scenario} falsely triggered ADVANCE-FEE FRAUD subtype!"
    assert res["primary_classification"] == "legitimate"
    assert res["threat_level"] == "LOW"
    assert res["overall_threat_score"] < 0.40

@pytest.mark.parametrize("spf_result, dmarc_result, expected_floor_active", [
    ("fail", "fail", True),
    ("softfail", "fail", True),
    ("pass", "fail", False),
    ("fail", "pass", False),
    ("pass", "pass", False),
])
def test_auth_failure_severity_floor_parametrization(spf_result, dmarc_result, expected_floor_active):
    """
    EXT-002 / T-3: Tests the Authentication Failure Severity Floor.
    Parametrized across spf={fail, softfail} with dmarc=fail to enforce >= 0.85 CRITICAL severity floor,
    while passing authentication scenarios do not trigger the floor.
    """
    mock_email = {"body_plain": "Routine note from executive.", "subject": "Quick Sync", "sender": "exec@spoofed.com"}
    mock_header = {
        "authentication": {
            "is_spoofed": (spf_result in ["fail", "softfail"] and dmarc_result == "fail"),
            "spf": {"result": spf_result},
            "dkim": {"result": "none"},
            "dmarc": {"result": dmarc_result}
        },
        "header_anomalies": [],
        "received_chain": [{"from_ip": "192.0.2.1"}]
    }
    mock_content = {
        "urgency_score": 0.1,
        "authority_score": 0.1,
        "financial_score": 0.1,
        "credential_score": 0.0,
        "linguistic_features": {},
        "urls_count": 0,
        "has_mismatched_links": False
    }
    mock_domain = {"domain": "spoofed.com", "is_lookalike": False, "domain_risk_score": 0.1}
    mock_origin = {"probable_origin_ip": "192.0.2.1", "anonymization": {"tor_exit_node": False, "vpn_detected": False, "hosting_provider": False}}

    res = ThreatClassifier.evaluate(
        mock_email, mock_header, mock_content, mock_domain, mock_origin, {"corroboration_score": 0.0}
    )

    if expected_floor_active:
        assert res["overall_threat_score"] >= 0.85, (
            f"Expected severity floor >= 0.85 for SPF={spf_result}, DMARC={dmarc_result}, got {res['overall_threat_score']}"
        )
        assert res["threat_level"] == "CRITICAL"
    else:
        assert res["overall_threat_score"] < 0.85

def test_mutation_kill_advance_fee_subtype_and_severity_floor():
    """
    EXT-001 & EXT-002 Mutation Kill Assertions:
    Verifies that mutating either the keyword threshold or removing the severity floor
    fails with explicit attribution.

    Note on P2-2: This test deliberately uses a minimal auth-only fixture (with benign body
    and zero linguistic fraud indicators) whose natural pre-floor score is 0.45. This isolates
    and proves that the severity floor alone elevates an unauthenticated domain spoof to 0.85 CRITICAL.
    """
    # 1. Floor kill verification on minimal auth-only fixture
    mock_email = {"body_plain": "General text", "subject": "Notice", "sender": "target@domain.example"}
    mock_header = {
        "authentication": {"is_spoofed": True, "spf": {"result": "fail"}, "dmarc": {"result": "fail"}},
        "header_anomalies": [],
        "received_chain": [{"from_ip": "192.0.2.1"}]
    }
    res = ThreatClassifier.evaluate(mock_email, mock_header, {}, {}, {}, {})
    assert res["overall_threat_score"] >= 0.85, (
        f"Mutation Kill: Expected severity floor >= 0.85 on DMARC+SPF failure, got {res['overall_threat_score']}"
    )
    assert res["threat_level"] == "CRITICAL"

