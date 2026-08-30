import pytest
from app.services.ingestion import IngestionService

def test_parse_legitimate_email(sample_emails_dir):
    eml_file = sample_emails_dir / "legitimate_workplace.eml"
    assert eml_file.exists()
    content = eml_file.read_bytes()

    data = IngestionService.parse_raw_email(content, source="test_upload")
    assert data["subject"] == "Monthly Engineering Architecture & Security Summary - January 2024"
    assert "engineering-updates@google.com" in data["sender"]
    assert data["sender_domain"] == "google.com"
    assert len(data["sha256_hash"]) == 64
    assert len(data["received_headers"]) >= 2
    assert "microservice infrastructure" in data["body_plain"]

def test_parse_phishing_email_with_multiple_received_hops(sample_emails_dir):
    eml_file = sample_emails_dir / "apex_phishing_tor_relay.eml"
    assert eml_file.exists()
    content = eml_file.read_bytes()

    data = IngestionService.parse_raw_email(content, source="test_upload")
    assert "Mandatory KYC Verification Required" in data["subject"]
    assert len(data["received_headers"]) == 3
    assert data["sender_domain"] == "apex-secureverify.com"
    assert "https://apex-secureverify.com/login" in data["body_html"]
