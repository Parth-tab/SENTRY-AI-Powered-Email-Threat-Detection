import pytest

@pytest.mark.asyncio
async def test_health_check_endpoint(client):
    res = await client.get("/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "healthy"
    assert "RFC 3227 (Evidence)" in data["rfc_compliance"]

@pytest.mark.asyncio
async def test_raw_email_upload_and_analysis_endpoint(client):
    raw_email = """From: Security <alert@sbi-secureverify.com>
To: target@victim.com
Subject: URGENT: Action Required
Date: Mon, 15 Jan 2024 10:00:00 +0000
Received: from [185.220.101.34] by mx.victim.com with SMTP; Mon, 15 Jan 2024 10:00:00 +0000

Dear Customer, verify your credentials immediately within 24 hours.
"""
    res = await client.post("/api/v1/emails/raw", content=raw_email, headers={"Content-Type": "text/plain"})
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
