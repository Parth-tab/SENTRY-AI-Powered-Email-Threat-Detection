import pytest
from app.services.content_analysis import ContentAnalysisService

def test_content_linguistic_urgency_and_credentials():
    email_data = {
        "subject": "URGENT: Verify your account immediately",
        "body_plain": "Dear Customer, Your account is suspended. Verify credentials within 24 hours.",
        "body_html": "<p>Dear Customer</p><a href='https://apex-secureverify.com/login'>https://online.apexbank.internal/login</a>",
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

def test_advance_fee_lottery_lexicon_and_pii_extraction():
    """EXT-001: Asserts advance-fee fraud phrases and PII harvesting forms are extracted."""
    email_data = {
        "subject": "OFFICIAL NOTIFICATION: INTERNATIONAL LOTTERY WINNER -- CLAIM YOUR PRIZE OF $2,500,000.00 USD",
        "body_plain": (
            "Congratulations! You are the lucky winner of the annual lottery promotion. "
            "To claim your prize, you must remit the initial processing fee to our claim agent. "
            "Please provide your full passport copy, residential address, date of birth, and bank account details."
        ),
        "body_html": "",
        "attachments": []
    }

    res = ContentAnalysisService.analyze_content(email_data)
    assert res["advance_fee_score"] > 0.5
    assert res["pii_score"] > 0.3
    assert res["action_requested"] == "advance_fee_pii_solicitation"
    adv_matches = res["linguistic_features"]["advance_fee_matches"]
    pii_matches = res["linguistic_features"]["pii_matches"]
    assert len(adv_matches) >= 2
    assert len(pii_matches) >= 2

def test_adversarial_hr_and_newsletter_do_not_flag_advance_fee():
    """EXT-001 Adversarial Controls: Routine HR and newsletter emails must not falsely trigger advance-fee."""
    # 1. HR Benefits Enrollment with "beneficiary"
    hr_email = {
        "subject": "Annual Benefits Enrollment — Designate your Beneficiary",
        "body_plain": "Hello Team, please log in to the internal HR portal to verify your insurance beneficiary selections.",
        "body_html": "",
        "attachments": []
    }
    hr_res = ContentAnalysisService.analyze_content(hr_email)
    assert len(hr_res["linguistic_features"]["advance_fee_matches"]) < 2
    assert hr_res["advance_fee_score"] <= 0.40

    # 2. Tech Newsletter with "prize"
    newsletter_email = {
        "subject": "Engineering Weekly: Hackathon Winner Announcements",
        "body_plain": "Join us on Friday for demos. First prize winner will receive team recognition and a trophy.",
        "body_html": "",
        "attachments": []
    }
    news_res = ContentAnalysisService.analyze_content(newsletter_email)
    assert len(news_res["linguistic_features"]["advance_fee_matches"]) < 2
    assert news_res["advance_fee_score"] <= 0.40
