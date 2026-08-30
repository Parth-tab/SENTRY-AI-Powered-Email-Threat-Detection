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
    email_data = {"sender_domain": "apex-secureverify.com"}
    origin_data = {"probable_origin_ip": "185.220.101.34", "anonymization": {"tor_exit_node": True}, "geolocation": {"asn": "AS205100"}}
    domain_data = {"impersonated_brand": "Apex National Bank"}
    content_data = {"financial_score": 0.1, "authority_score": 0.1}

    match = CorrelationEngine.correlate(email_data, origin_data, domain_data, content_data)
    assert match is not None
    assert match["campaign_id"] == "CMP-2024-0034"
    assert "credential harvesting" in match["assessment"]

def test_campaign_cluster_filtering():
    CorrelationEngine.reset_graph()
    
    # Add dummy campaign emails
    CorrelationEngine.add_email_to_graph(
        email_id="test-email-1",
        email_data={"subject": "GhostRelay Attack", "sender": "hacker@apex-secureverify.com", "sender_domain": "apex-secureverify.com"},
        analysis_data={
            "overall_threat_score": 0.95,
            "threat_level": "CRITICAL",
            "origin_assessment": {"probable_origin_ip": "185.220.101.34", "geolocation": {"asn": "AS205100", "isp": "F3 Netze"}},
            "attribution_assessment": {"campaign_id": "CMP-2024-0034", "assessment": "GhostRelay"},
            "domain_intel": {"is_lookalike": True, "impersonated_brand": "Apex National Bank"}
        }
    )
    
    cluster_res = CorrelationEngine.get_graph_data(campaign_id="CMP-2024-0034", mode="cluster")
    assert cluster_res["mode"] == "cluster"
    assert cluster_res["active_campaign_id"] == "CMP-2024-0034"
    node_ids = [n["id"] for n in cluster_res["nodes"]]
    assert "campaign:CMP-2024-0034" in node_ids
    assert "test-email-1" in node_ids
    assert "domain:apex-secureverify.com" in node_ids
    assert "infra:AS205100" in node_ids

def test_campaign_supernode_aggregation():
    CorrelationEngine.reset_graph()
    super_res = CorrelationEngine.get_graph_data(mode="supernode")
    assert super_res["mode"] == "supernode"
    supernodes = [n for n in super_res["nodes"] if n["type"] == "CampaignSupernode"]
    assert len(supernodes) >= 1
    assert any(n["campaign_id"] == "CMP-2024-0034" for n in supernodes)
    
    # Verify links have weights
    for link in super_res["links"]:
        assert "weight" in link
        assert link["weight"] >= 1

def test_synthetic_import_entity_badging():
    CorrelationEngine.reset_graph()
    CorrelationEngine.add_email_to_graph(
        email_id="test-csv-import-email",
        email_data={"subject": "Imported Email", "sender": "csv-import@unknown.local", "sender_domain": "unknown.local"},
        analysis_data={"overall_threat_score": 0.1, "threat_level": "LOW"}
    )
    graph_res = CorrelationEngine.get_graph_data(mode="detailed")
    synthetic_nodes = [n for n in graph_res["nodes"] if n.get("is_synthetic")]
    assert len(synthetic_nodes) >= 1
    assert any("unknown.local" in n["id"] for n in synthetic_nodes)

