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

@pytest.mark.parametrize("reserved_ip, range_name", [
    # RFC 1918 Private IPv4
    ("10.0.0.1", "RFC 1918 (10/8)"),
    ("172.16.5.1", "RFC 1918 (172.16/12)"),
    ("192.168.1.1", "RFC 1918 (192.168/16)"),
    # RFC 5737 Documentation Address Blocks (TEST-NET-1, TEST-NET-2, TEST-NET-3)
    ("192.0.2.1", "RFC 5737 TEST-NET-1 (192.0.2.0/24)"),
    ("198.51.100.42", "RFC 5737 TEST-NET-2 (198.51.100.0/24)"),
    ("203.0.113.100", "RFC 5737 TEST-NET-3 (203.0.113.0/24)"),
    # RFC 6598 Carrier-Grade NAT
    ("100.64.0.1", "RFC 6598 CGNAT (100.64.0.0/10)"),
    # RFC 1122 Loopback
    ("127.0.0.1", "RFC 1122 Loopback (127.0.0.0/8)"),
    # RFC 3927 Link-Local
    ("169.254.1.1", "RFC 3927 Link-Local (169.254.0.0/16)"),
    # RFC 5771 Multicast
    ("224.0.0.1", "RFC 5771 Multicast (224.0.0.0/4)"),
    # RFC 1122 Unspecified
    ("0.0.0.0", "RFC 1122 Unspecified (0.0.0.0/8)"),
    # RFC 1112 / RFC 6890 Reserved / Broadcast
    ("240.0.0.1", "RFC 1112 Reserved / Future Use (240.0.0.0/4)"),
    ("255.255.255.255", "RFC 6890 Limited Broadcast"),
    # RFC 2544 Benchmarking
    ("198.18.0.1", "RFC 2544 Benchmarking (198.18.0.0/15)"),
    # RFC 3068 6to4 Relay
    ("192.88.99.1", "RFC 3068 6to4 Relay (192.88.99.0/24)"),
    # IPv6 Special-Purpose Ranges
    ("::1", "RFC 4291 IPv6 Loopback (::1/128)"),
    ("::", "RFC 4291 IPv6 Unspecified (::/128)"),
    ("2001:db8::1", "RFC 3849 IPv6 Documentation (2001:db8::/32)"),
    ("fc00::1", "RFC 4193 IPv6 ULA (fc00::/7)"),
    ("fe80::1", "RFC 4291 IPv6 Link-Local (fe80::/10)"),
    ("ff02::1", "RFC 4291 IPv6 Multicast (ff00::/8)"),
])
def test_reserved_ip_enrichment_guard_scenario_matrix(reserved_ip, range_name):
    """
    EXT-003: Asserts that every RFC special-purpose and reserved IP range
    is recognized, skips external Geo/Tor/VPN/ThreatIntel enrichment, and returns
    explicit 'Reserved / Internal Test IP' attribution without fabricated ASNs.
    """
    assert GeoOriginService.is_reserved_or_special_use_ip(reserved_ip) is True, (
        f"Failed to identify {reserved_ip} ({range_name}) as special-purpose/reserved IP"
    )

    geo = GeoOriginService.lookup_ip_geo(reserved_ip)
    assert geo["country"] == "Reserved"
    assert geo["country_code"] == "XX"
    assert geo["city"] == "Reserved"
    assert geo["isp"] == "Reserved / Internal Test IP"
    assert geo["asn"] == "N/A"
    assert geo["connection_type"] == "Special-Purpose / Reserved"

    # Verify Tor and VPN guards return clean False
    assert GeoOriginService.is_tor_exit_node(reserved_ip) is False
    is_vpn, vpn_name = GeoOriginService.is_vpn(reserved_ip)
    assert is_vpn is False
    assert vpn_name is None

    # Verify evaluate_origin returns low-confidence reserved assessment
    earliest_hop = {"from_ip": reserved_ip, "is_private": True, "is_reliable": True}
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=1)
    assert origin_res["probable_origin_ip"] == reserved_ip
    assert origin_res["anonymization"]["tor_exit_node"] is False
    assert origin_res["anonymization"]["hosting_provider"] is False
    assert origin_res["confidence"] == 0.15
    assert origin_res["anonymization"]["risk_summary"] == "Special-Purpose / Reserved IP"

@pytest.mark.parametrize("real_ip, expected_country, expected_asn, expected_tor", [
    ("185.220.101.34", "Netherlands", "AS205100", True),
    ("209.85.220.41", "United States", "AS15169", False),
    ("51.15.43.205", "France", "AS12876", True),
    ("40.107.92.54", "United States", "AS8075", False),
])
def test_real_ip_controls_enrich_accurately(real_ip, expected_country, expected_asn, expected_tor):
    """
    Control: Synthetic-resolver consistency and non-overreach controls (air-gapped appliance fixtures).
    Real public IPs must NOT trigger the reserved guard and must enrich to their authentic
    geolocation, ISP, ASN, and anonymization status.
    """
    assert GeoOriginService.is_reserved_or_special_use_ip(real_ip) is False
    geo = GeoOriginService.lookup_ip_geo(real_ip)
    assert geo["country"] == expected_country
    assert geo["asn"] == expected_asn
    assert GeoOriginService.is_tor_exit_node(real_ip) is expected_tor

def test_mutation_kill_reserved_ip_guard_prevents_false_attribution():
    """
    EXT-003 Mutation Kill Assertion:
    Verifies that RFC 5737 TEST-NET-1 IP 192.0.2.1 is strictly guarded as Reserved.
    If the guard is reverted/removed, this test fails by name quoting the exact fabricated
    attribution ('Amazon.com, Inc. AS16509') that the guard prevents.
    """
    ip = "192.0.2.1"
    geo = GeoOriginService.lookup_ip_geo(ip)
    
    # If the guard is removed, geo['isp'] evaluates to 'Amazon.com, Inc.' and geo['asn'] to 'AS16509'
    # This assertion catches that mutation directly:
    assert geo["isp"] == "Reserved / Internal Test IP", (
        f"Mutation Kill: Expected 'Reserved / Internal Test IP', got '{geo.get('isp')}' "
        f"({geo.get('asn')}, {geo.get('city')}, {geo.get('country')}) — false attribution fabricated!"
    )
    assert geo["asn"] == "N/A"
    assert geo["country"] == "Reserved"

