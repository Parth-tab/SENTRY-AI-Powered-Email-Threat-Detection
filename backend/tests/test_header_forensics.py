import pytest
from app.services.header_forensics import HeaderForensicsService

def test_received_chain_reconstruction():
    headers = [
        "by mx.google.com with SMTPS id 123; Thu, 15 Jan 2024 10:24:00 +0000",
        "from mail.bulletproof-relay.net (mail.bulletproof-relay.net [185.220.101.34]) by mx.google.com with ESMTP id 456; Thu, 15 Jan 2024 10:23:47 +0000",
        "from unknown (HELO tor-exit.de) (185.220.101.34) by mail.bulletproof-relay.net with ESMTP; Thu, 15 Jan 2024 10:23:45 +0000"
    ]

    hops, earliest_hop, anomalies = HeaderForensicsService.parse_received_chain(headers)
    assert len(hops) == 3
    assert earliest_hop is not None
    assert earliest_hop["from_ip"] == "185.220.101.34"
    assert earliest_hop["is_private"] is False

def test_earliest_reliable_hop_selection_multi_hop():
    # Chronological bottom-to-top:
    # Header[2] (bottom) is earliest sender hop: 194.26.29.117
    # Header[1] (middle) is relay hop: 185.220.101.34
    # Header[0] (top) is recipient MX: 209.85.220.41
    headers = [
        "by mx.google.com with SMTPS id 123; Thu, 15 Jan 2024 10:24:00 +0000",
        "from mail.relay.net (mail.relay.net [185.220.101.34]) by mx.google.com with ESMTP id 456; Thu, 15 Jan 2024 10:23:47 +0000",
        "from mail.origin.ru (mail.origin.ru [194.26.29.117]) by mail.relay.net with ESMTP; Thu, 15 Jan 2024 10:23:45 +0000"
    ]
    hops, earliest_hop, anomalies = HeaderForensicsService.parse_received_chain(headers)
    assert len(hops) == 3
    assert earliest_hop is not None
    assert earliest_hop["from_ip"] == "194.26.29.117", "Earliest reliable hop must match the first public hop (chronological index 0)"
    assert earliest_hop["hop_number"] == 1

def test_authentication_evaluation_pass():
    headers = {
        "Authentication-Results": "mx.google.com; dkim=pass header.i=@google.com; spf=pass smtp.mailfrom=user@google.com; dmarc=pass (p=REJECT)",
        "Received-SPF": "pass (google.com: domain of user@google.com designates 209.85.220.41 as permitted sender)"
    }
    auth = HeaderForensicsService.evaluate_authentication(headers)
    assert auth["spf"]["result"] == "pass"
    assert auth["dkim"]["result"] == "pass"
    assert auth["dmarc"]["result"] == "pass"
    assert auth["total_auth_score"] > 0
    assert auth["is_spoofed"] is False

def test_authentication_evaluation_fail():
    headers = {
        "Authentication-Results": "mx.google.com; dkim=none; spf=fail smtp.mailfrom=support@apex-secureverify.com; dmarc=fail (p=REJECT)",
        "Received-SPF": "fail (domain does not designate IP)"
    }
    auth = HeaderForensicsService.evaluate_authentication(headers)
    assert auth["spf"]["result"] == "fail"
    assert auth["dmarc"]["result"] == "fail"
    assert auth["total_auth_score"] < 0
    assert auth["is_spoofed"] is True

def test_mixed_timezone_awareness_chronology():
    """HAM-001: Mixed offset-naive and offset-aware datetimes in Received headers."""
    headers = [
        "from mail.relay.net (mail.relay.net [185.220.101.34]) by mx.google.com with ESMTP id 123; Thu, 15 Jan 2024 10:24:00 +0000",
        "from sender.net (sender.net [198.51.100.1]) by mail.relay.net with ESMTP id 456; 15 Jan 2024 10:23:47"
    ]
    hops, earliest_hop, anomalies = HeaderForensicsService.parse_received_chain(headers)
    assert len(hops) == 2
    assert earliest_hop is not None
    assert earliest_hop["from_ip"] == "185.220.101.34"
    assert "impossible_timestamp_sequence_hop_1_to_2" not in anomalies

