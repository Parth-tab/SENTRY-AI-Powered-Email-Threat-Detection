import pytest

@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "RFC 3227 (Evidence)" in data["rfc_compliance"]

from app.config import settings

@pytest.mark.asyncio
async def test_raw_email_upload_and_analysis_endpoint(client):
    raw_email = """From: Security <alert@apex-secureverify.com>
To: target@victim.com
Subject: URGENT: Action Required
Date: Mon, 15 Jan 2024 10:00:00 +0000
Received: from [185.220.101.34] by mx.victim.com with SMTP; Mon, 15 Jan 2024 10:00:00 +0000

Dear Customer, verify your credentials immediately within 24 hours.
"""
    auth_headers = {
        "Content-Type": "text/plain",
        "Authorization": f"Bearer {settings.SENTRY_API_TOKEN}"
    }
    res = await client.post("/api/v1/emails/raw", content=raw_email, headers=auth_headers)
    assert res.status_code == 201
    data = res.json()
    assert data["subject"] == "URGENT: Action Required"
    assert data["analysis"]["threat_level"] in ["HIGH", "CRITICAL"]
    assert data["evidence"]["chain_of_custody_id"].startswith("COC-")

@pytest.mark.asyncio
async def test_dashboard_stats_endpoint(client):
    res = await client.get("/api/v1/dashboard/stats")
    assert res.status_code == 200
    data = res.json()
    assert "total_emails_analyzed" in data
    assert "threat_distribution" in data
    assert "active_campaigns_count" in data

@pytest.mark.asyncio
async def test_seed_endpoint_idempotency(client):
    auth_headers = {"Authorization": f"Bearer {settings.SENTRY_API_TOKEN}"}
    # First seed call
    res1 = await client.post("/api/v1/samples/seed", headers=auth_headers)
    assert res1.status_code in [200, 201]
    
    # Second seed call must not duplicate records
    res2 = await client.post("/api/v1/samples/seed", headers=auth_headers)
    assert res2.status_code == 200
    data2 = res2.json()
    assert len(data2.get("seeded_email_ids", [])) == 0, "Second seed call must create 0 duplicate records"

@pytest.mark.asyncio
@pytest.mark.parametrize("params,expected_status,expected_mode", [
    ({}, 200, "cluster"),
    ({"mode": "cluster"}, 200, "cluster"),
    ({"mode": "supernode"}, 200, "supernode"),
    ({"mode": "detailed"}, 200, "detailed"),
    ({"mode": "invalid_mode_xyz"}, 200, "cluster"), # Graceful fallback to default cluster
    ({"campaign_id": "CMP-2024-0034", "mode": "cluster"}, 200, "cluster"),
    ({"campaign_id": "nonexistent_camp", "mode": "cluster"}, 200, "cluster"),
    ({"max_nodes": 50}, 200, "cluster"),
])
async def test_graph_endpoints_parameter_contract(client, params, expected_status, expected_mode):
    res = await client.get("/api/v1/campaigns/graph/all", params=params)
    assert res.status_code == expected_status
    data = res.json()
    assert "nodes" in data
    assert "links" in data
    assert data.get("mode") == expected_mode

@pytest.mark.asyncio
async def test_aggregated_graph_alias_endpoint(client):
    res = await client.get("/api/v1/campaigns/graph/aggregated")
    assert res.status_code == 200
    data = res.json()
    assert data.get("mode") == "supernode"
    assert "nodes" in data
    assert "links" in data

