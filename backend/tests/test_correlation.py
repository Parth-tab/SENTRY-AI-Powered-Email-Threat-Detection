import pytest
from app.services.correlation_engine import CorrelationEngine

def test_campaign_correlation_ghostrelay():
    email_data = {"sender_domain": "sbi-secureverify.com"}
    origin_data = {"probable_origin_ip": "185.220.101.34", "anonymization": {"tor_exit_node": True}, "geolocation": {"asn": "AS205100"}}
    domain_data = {"impersonated_brand": "State Bank of India"}
    content_data = {"financial_score": 0.1, "authority_score": 0.1}

    attrib = CorrelationEngine.correlate(email_data, origin_data, domain_data, content_data)
    assert attrib["campaign_id"] == "CMP-2024-0034"
    assert attrib["campaign_confidence"] > 0.80
    assert attrib["related_emails"] == 14
    assert "AS205100" in attrib["infrastructure_cluster"]["name"]
