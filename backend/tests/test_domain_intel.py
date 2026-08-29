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

def test_short_acronym_lookalike_bounds():
    """HAM-003: Short acronym brands vs near-strings (no false positives, real typosquats still match)."""
    # Short acronym near-strings must NOT match (e.g. sub.com vs sbi, biz.com vs ibm)
    res_sub = DomainIntelService.check_lookalike("sub.com")
    assert res_sub["is_lookalike"] is False

    res_biz = DomainIntelService.check_lookalike("biz.com")
    assert res_biz["is_lookalike"] is False

    # Real typosquats and lookalikes must STILL match
    res_sbi = DomainIntelService.check_lookalike("sbi-secureverify.com")
    assert res_sbi["is_lookalike"] is True
    assert res_sbi["impersonated_brand"] == "State Bank of India"

    res_paypal = DomainIntelService.check_lookalike("paypa1.com")
    assert res_paypal["is_lookalike"] is True
    assert res_paypal["impersonated_brand"] == "PayPal"

