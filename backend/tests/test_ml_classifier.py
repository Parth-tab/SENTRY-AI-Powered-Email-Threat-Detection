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

