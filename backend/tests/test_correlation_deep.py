import pytest
from app.services.correlation_engine import CorrelationEngine

def test_campaign_correlation_graph_export():
    campaigns = CorrelationEngine.list_campaigns()
    assert len(campaigns) >= 2
    
    # Verify graph topology
    graph_data = CorrelationEngine.get_graph_data()
    assert "nodes" in graph_data
    assert "links" in graph_data
    assert len(graph_data["nodes"]) >= 5
    assert len(graph_data["links"]) >= 4

def test_campaign_ioc_attribution():
    email_data = {"sender_domain": "sbi-secureverify.com"}
    origin_data = {"probable_origin_ip": "185.220.101.34", "anonymization": {"tor_exit_node": True}, "geolocation": {"asn": "AS205100"}}
    domain_data = {"impersonated_brand": "State Bank of India"}
    content_data = {"financial_score": 0.1, "authority_score": 0.1}

    match = CorrelationEngine.correlate(email_data, origin_data, domain_data, content_data)
    assert match is not None
    assert match["campaign_id"] == "CMP-2024-0034"
    assert "credential harvesting" in match["assessment"]
