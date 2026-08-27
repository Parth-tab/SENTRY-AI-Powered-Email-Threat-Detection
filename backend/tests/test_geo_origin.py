import pytest
from app.services.geo_origin import GeoOriginService

def test_tor_exit_node_detection_and_confidence_penalty():
    earliest_hop = {
        "from_ip": "185.220.101.34",
        "is_private": False,
        "is_reliable": True
    }
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=3)
    assert origin_res["probable_origin_ip"] == "185.220.101.34"
    assert origin_res["anonymization"]["tor_exit_node"] is True
    assert origin_res["confidence"] < 0.50 # Penalized due to Tor masking
    assert any("TOR" in f for f in origin_res["confidence_factors"])

def test_clean_corporate_origin():
    earliest_hop = {
        "from_ip": "209.85.220.41",
        "is_private": False,
        "is_reliable": True
    }
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=1)
    assert origin_res["probable_origin_ip"] == "209.85.220.41"
    assert origin_res["anonymization"]["tor_exit_node"] is False
    assert origin_res["confidence"] >= 0.65
