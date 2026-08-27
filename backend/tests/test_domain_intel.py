import pytest
from app.services.domain_intel import DomainIntelService

def test_lookalike_detection_sbi():
    res = DomainIntelService.check_lookalike("sbi-secureverify.com")
    assert res["is_lookalike"] is True
    assert res["impersonated_brand"] == "State Bank of India"
    assert res["confidence"] >= 0.90

def test_lookalike_detection_paypal_typosquat():
    res = DomainIntelService.check_lookalike("paypa1.com")
    assert res["is_lookalike"] is True
    assert res["impersonated_brand"] == "PayPal"

def test_legitimate_google_domain():
    res = DomainIntelService.check_lookalike("google.com")
    assert res["is_lookalike"] is False
    assert res.get("is_legitimate_brand") is True
