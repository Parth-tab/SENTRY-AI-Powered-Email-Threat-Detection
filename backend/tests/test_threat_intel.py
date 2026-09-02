import pytest
from app.services.threat_intel import ThreatIntelService

@pytest.mark.asyncio
async def test_threat_intel_urlhaus_hit():
    urls = [{"url": "https://apex-secureverify.com/login"}]
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
        domain="apex-secureverify.com",
        urls=[{"url": "https://apex-secureverify.com/login"}]
    )
    assert res["total_matches"] >= 2
    assert res["corroboration_score"] >= 0.70

@pytest.mark.asyncio
async def test_threat_intel_skips_reserved_and_special_use_ips():
    """EXT-003: Asserts ThreatIntelService ignores reserved IPs and avoids false IOC queries."""
    matches = await ThreatIntelService.check_threatfox("192.0.2.1", "clean-domain.example")
    assert matches == []

    res = await ThreatIntelService.evaluate_threat_intelligence(
        ip="192.0.2.1",
        domain="clean-domain.example",
        urls=[]
    )
    assert res["total_matches"] == 0
    assert res["corroboration_score"] == 0.0
