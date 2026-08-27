import pytest
from app.services.threat_intel import ThreatIntelService

@pytest.mark.asyncio
async def test_threat_intel_urlhaus_hit():
    urls = [{"url": "https://sbi-secureverify.com/login"}]
    matches = await ThreatIntelService.check_urlhaus(urls)
    assert len(matches) == 1
    assert matches[0]["source"] == "URLhaus"

@pytest.mark.asyncio
async def test_threat_intel_threatfox_ip_hit():
    matches = await ThreatIntelService.check_threatfox("185.220.101.34", "clean.com")
    assert len(matches) == 1
    assert matches[0]["ioc"] == "185.220.101.34"

@pytest.mark.asyncio
async def test_threat_intel_parallel_aggregation():
    res = await ThreatIntelService.evaluate_threat_intelligence(
        ip="185.220.101.34",
        domain="sbi-secureverify.com",
        urls=[{"url": "https://sbi-secureverify.com/login"}]
    )
    assert res["total_matches"] >= 2
    assert res["corroboration_score"] >= 0.70
