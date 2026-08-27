import pytest
from app.services.content_analysis import ContentAnalysisService

def test_content_linguistic_urgency_and_credentials():
    email_data = {
        "subject": "URGENT: Verify your account immediately",
        "body_plain": "Dear Customer, Your account is suspended. Verify credentials within 24 hours.",
        "body_html": "<p>Dear Customer</p><a href='https://sbi-secureverify.com/login'>https://onlinesbi.sbi/login</a>",
        "attachments": []
    }

    res = ContentAnalysisService.analyze_content(email_data)
    assert res["urgency_score"] > 0.3
    assert res["credential_score"] > 0.3
    assert res["has_mismatched_links"] is True
    assert res["action_requested"] == "credential_verification"
    assert "verify your account" in res["linguistic_features"]["credential_harvesting"]

def test_bec_financial_and_authority_detection():
    email_data = {
        "subject": "Immediate Wire Transfer Request",
        "body_plain": "I am the CEO. Please process an urgent wire transfer of $142,500 to our offshore bank account.",
        "body_html": "",
        "attachments": []
    }

    res = ContentAnalysisService.analyze_content(email_data)
    assert res["authority_score"] > 0.3
    assert res["financial_score"] > 0.3
    assert res["action_requested"] == "financial_transaction"
