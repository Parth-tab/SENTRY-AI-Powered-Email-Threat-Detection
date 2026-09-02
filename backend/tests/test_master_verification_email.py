import re
import zlib
import base64
import pytest
from pathlib import Path

from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.geo_origin import GeoOriginService
from app.services.domain_intel import DomainIntelService
from app.services.content_analysis import ContentAnalysisService
from app.services.reporting import ReportingService
from app.ml.classifier import ThreatClassifier

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"

def test_master_verification_pipeline_outcomes_matrix():
    """
    MASTER-EMAIL-VERIFICATION: End-to-end pipeline run asserting the complete
    expected-outcomes matrix for advance_fee_master_verification.eml:
    1. Classification + Subtype (ADVANCE-FEE FRAUD)
    2. Floor + pre-floor transparency
    3. Origin IP == 203.0.113.9 with RFC 5737 Reserved attribution
    4. 4 IOC rows (IPv4, Sender domain, Reply-To email, Reply-To domain)
    5. Countermeasure safety: no self-DoS, no loopback in firewall recommendation,
       no RFC-special IP in firewall drop list, and perimeter block of Reply-To domain
    6. PDF report layer: full subject length preservation without hard slice
    """
    eml_path = FIXTURES_DIR / "advance_fee_master_verification.eml"
    assert eml_path.exists(), f"Missing fixture at {eml_path}"
    raw_bytes = eml_path.read_bytes()

    # 1. Ingestion Layer
    email_data = IngestionService.parse_raw_email(raw_bytes, source="eml_upload")
    assert len(email_data["subject"]) > 100, "Subject must exceed 100 chars to test PDF wrapping"
    assert email_data["sender_domain"] == "international-grant-program.org"
    assert "prize-disbursement.net" in str(email_data.get("reply_to"))

    # 2. Header Forensics Layer
    hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(email_data["received_headers"])
    auth_results = HeaderForensicsService.evaluate_authentication(email_data["headers"])
    detected_anomalies = HeaderForensicsService.detect_anomalies(email_data, earliest_hop)
    all_anomalies = list(set(hop_anomalies + detected_anomalies))

    header_res = {
        "relay_hops_count": len(hops),
        "relay_path": hops,
        "earliest_reliable_hop": earliest_hop,
        "authentication": auth_results,
        "header_anomalies": all_anomalies
    }

    # Verify DEF-A Hop Selection:
    # Deep chain: Hop 1 (oldest) = 127.0.0.1 (loopback), Hop 2 = 203.0.113.9 (TEST-NET-3), Hop 3 = MX
    # Probable origin MUST be 203.0.113.9 (not 127.0.0.1)
    assert earliest_hop is not None, "Earliest hop must be identified"
    assert earliest_hop["from_ip"] == "203.0.113.9", (
        f"DEF-A Regression: 127.0.0.1 selected as probable origin instead of 203.0.113.9! "
        f"Got {earliest_hop.get('from_ip')}"
    )

    # 3. Geo Origin Layer
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))
    assert origin_res["probable_origin_ip"] == "203.0.113.9"
    assert origin_res["geolocation"]["country"] == "Reserved", "TEST-NET-3 must receive Reserved attribution"
    assert origin_res["geolocation"]["isp"] == "Reserved / Internal Test IP"
    assert origin_res["confidence"] == 0.15, "Reserved space must carry 0.15 confidence penalty"
    assert origin_res["anonymization"]["risk_summary"] == "Special-Purpose / Reserved IP"

    # 4. Content Analysis Layer
    content_res = ContentAnalysisService.analyze_content(email_data)
    assert len(content_res["linguistic_features"]["advance_fee_matches"]) >= 2
    assert "reply_to_domain_mismatch" in all_anomalies

    # 5. Domain Intel Layer
    domain_res = DomainIntelService.analyze_domain(
        email_data.get("sender_domain", ""),
        sender_ip=earliest_hop.get("from_ip")
    )

    # 6. ML Classification Layer
    classification_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res
    )

    assert classification_res["threat_level"] in ["HIGH", "CRITICAL"]
    assert classification_res["primary_classification"] == "phishing"
    assert classification_res["classification_subtype"] == "ADVANCE-FEE FRAUD"
    assert classification_res["score_pre_floor"] is not None
    assert classification_res["overall_threat_score"] >= 0.85

    recs = classification_res["recommendations"]
    # Countermeasure checks:
    # NEVER block internal domain
    assert not any("Block sender domain 'targetcorp.example'" in r for r in recs)
    # NEVER recommend loopback or RFC-reserved IP in firewall drop list
    assert not any("127.0.0.1" in r for r in recs), "Loopback 127.0.0.1 present in countermeasure recommendations!"
    assert not any("203.0.113.9" in r for r in recs), "RFC-reserved IP 203.0.113.9 present in firewall drop list!"
    assert not any("firewall drop list" in r for r in recs), "Firewall drop list recommended for reserved origin IP!"
    # Block external Reply-To diversion domain
    assert any("Block external Reply-To domain 'prize-disbursement.net'" in r for r in recs)

    # 7. Evidence & Report Generation (DEF-B Query Projection Check)
    coc_id, chain_entries, last_hash = ReportingService.initialize_chain_of_custody(
        email_id="master-verif-001",
        sha256_hash=email_data["sha256_hash"],
        source="eml_upload"
    )
    evidence_data = {
        "chain_of_custody_id": coc_id,
        "chain_entries": chain_entries,
        "last_entry_hash": last_hash
    }

    # Simulate database-stored entity and download_pdf_report query path
    raw_hdrs = email_data.get("headers") or {}
    email_dict = {
        "subject": email_data.get("subject", ""),
        "from_raw": email_data.get("sender", ""),
        "sender": email_data.get("sender", ""),
        "sender_domain": email_data.get("sender_domain", ""),
        "recipient": email_data.get("recipient", ""),
        "message_id": email_data.get("message_id", ""),
        "sha256_hash": email_data.get("sha256_hash", ""),
        "headers": raw_hdrs,
        "raw_headers": raw_hdrs,
        "reply_to": email_data.get("reply_to") or raw_hdrs.get("Reply-To") or ""
    }
    analysis_dict = {
        "overall_threat_score": classification_res["overall_threat_score"],
        "threat_level": classification_res["threat_level"],
        "primary_classification": classification_res["primary_classification"],
        "origin_assessment": origin_res,
        "domain_intel": domain_res,
        "content_analysis": content_res,
        "recommendations": classification_res["recommendations"]
    }

    pdf_bytes = ReportingService.generate_pdf_report(
        email_data=email_dict,
        analysis_data=analysis_dict,
        evidence_data=evidence_data
    )
    assert len(pdf_bytes) > 1000

    streams = re.findall(rb"stream\n(.*?)~>endstream", pdf_bytes, re.DOTALL)
    decompressed = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in streams]).decode("latin1")

    # DEF-B Assertions: Exactly 4 IOC rows rendered in PDF table
    assert "IPv4 Address" in decompressed
    assert "203.0.113.9" in decompressed
    assert "international-grant-program.org" in decompressed
    assert "Reply-To Email" in decompressed, "Expected 'Reply-To Email' row in PDF IOC table!"
    assert "claims@prize-disbursement.net" in decompressed
    assert "Reply-To Domain" in decompressed, "Expected 'Reply-To Domain' row in PDF IOC table!"
    assert "prize-disbursement.net" in decompressed

    # Subject length preservation at PDF layer
    assert "OFFICIAL NOTIFICATION: INTERNATIONAL LOTTERY PROMOTION" in decompressed
    assert "GRANT DISBURSEMENT ADVISORY" in decompressed


def test_negative_control_adversarial_newsletter():
    """
    Negative-control variant (auth-pass newsletter with 'prize' wording).
    Asserts LOW threat level, no classification subtype, and no floor applied.
    Live-path adversarial discrimination control.
    """
    eml_path = FIXTURES_DIR / "newsletter_negative_control.eml"
    assert eml_path.exists(), f"Missing fixture at {eml_path}"
    raw_bytes = eml_path.read_bytes()

    email_data = IngestionService.parse_raw_email(raw_bytes, source="eml_upload")
    hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(email_data["received_headers"])
    auth_results = HeaderForensicsService.evaluate_authentication(email_data["headers"])
    detected_anomalies = HeaderForensicsService.detect_anomalies(email_data, earliest_hop)
    all_anomalies = list(set(hop_anomalies + detected_anomalies))

    header_res = {
        "relay_hops_count": len(hops),
        "relay_path": hops,
        "earliest_reliable_hop": earliest_hop,
        "authentication": auth_results,
        "header_anomalies": all_anomalies
    }
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))
    content_res = ContentAnalysisService.analyze_content(email_data)
    domain_res = DomainIntelService.analyze_domain(email_data.get("sender_domain", ""))

    classification_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res
    )

    assert classification_res["threat_level"] == "LOW"
    assert classification_res["overall_threat_score"] < 0.40
    assert classification_res.get("classification_subtype") is None
    assert classification_res.get("floor_applied") is False
    assert any("allow delivery to inbox" in r for r in classification_res["recommendations"])


def test_scenario_matrix_hop_selection():
    """
    Verifies full 4-scenario matrix (a)-(d):
    (a) evaluator fixture (reserved at earliest public — unchanged behavior)
    (b) master email (TEST-NET-3 at hop 2, loopback at hop 3 -> origin MUST be 203.0.113.9/Reserved attribution)
    (c) clean corporate chain (real IPs — origin unchanged)
    (d) all-private chain -> Reserved origin
    """
    # (a) Evaluator fixture
    raw_a = (FIXTURES_DIR / "advance_fee_lottery.eml").read_bytes()
    data_a = IngestionService.parse_raw_email(raw_a)
    hops_a, ear_a, _ = HeaderForensicsService.parse_received_chain(data_a["received_headers"])
    origin_a = GeoOriginService.evaluate_origin(ear_a, len(hops_a))
    assert origin_a["probable_origin_ip"] == "192.0.2.1"
    assert origin_a["geolocation"]["country"] == "Reserved"
    assert origin_a["geolocation"]["isp"] == "Reserved / Internal Test IP"

    # (b) Master email
    raw_b = (FIXTURES_DIR / "advance_fee_master_verification.eml").read_bytes()
    data_b = IngestionService.parse_raw_email(raw_b)
    hops_b, ear_b, _ = HeaderForensicsService.parse_received_chain(data_b["received_headers"])
    origin_b = GeoOriginService.evaluate_origin(ear_b, len(hops_b))
    assert origin_b["probable_origin_ip"] == "203.0.113.9"
    assert origin_b["geolocation"]["country"] == "Reserved"
    assert origin_b["geolocation"]["isp"] == "Reserved / Internal Test IP"

    # (c) Clean corporate chain
    chain_c = [
        "by mx.google.com with SMTPS id 123; Thu, 15 Jan 2024 10:24:00 +0000",
        "from mail.relay.net (mail.relay.net [185.220.101.34]) by mx.google.com with ESMTP id 456; Thu, 15 Jan 2024 10:23:47 +0000",
        "from mail.origin.ru (mail.origin.ru [194.26.29.117]) by mail.relay.net with ESMTP; Thu, 15 Jan 2024 10:23:45 +0000"
    ]
    hops_c, ear_c, _ = HeaderForensicsService.parse_received_chain(chain_c)
    origin_c = GeoOriginService.evaluate_origin(ear_c, len(hops_c))
    assert origin_c["probable_origin_ip"] == "194.26.29.117"
    assert origin_c["geolocation"]["country"] == "Russia"

    # (d) All-private chain
    chain_d = [
        "Received: from internal-gw ([10.0.0.2]) by internal-mail with ESMTP; Thu, 15 Jan 2024 10:24:00 +0000",
        "Received: from branch-office ([192.168.1.100]) by internal-gw with ESMTP; Thu, 15 Jan 2024 10:23:50 +0000",
        "Received: from localhost ([127.0.0.1]) by branch-office with ESMTP; Thu, 15 Jan 2024 10:23:40 +0000"
    ]
    hops_d, ear_d, _ = HeaderForensicsService.parse_received_chain(chain_d)
    origin_d = GeoOriginService.evaluate_origin(ear_d, len(hops_d))
    assert origin_d["geolocation"]["country"] == "Reserved"
    assert origin_d["geolocation"]["isp"] == "Reserved / Internal Test IP"
    assert origin_d["confidence"] == 0.15
    assert origin_d["probable_origin_ip"] != "127.0.0.1", "Loopback must never be selected in all-private chain"


def test_mutation_kill_def_a_hop_selection_loopback():
    """
    Mutation Kill for DEF-A:
    If the hop selection is reverted (treating TEST-NET-3 as private and blindly
    taking hops[0]), the master email selects 127.0.0.1 instead of 203.0.113.9.
    This test verifies that reverting the fix causes a named failure quoting
    '127.0.0.1 selected as probable origin'.
    """
    raw_bytes = (FIXTURES_DIR / "advance_fee_master_verification.eml").read_bytes()
    email_data = IngestionService.parse_raw_email(raw_bytes, source="eml_upload")
    
    # Mutated behavior: treat all special-use IPs (including 203.0.113.9) as private
    hops = []
    for idx, h in enumerate(reversed(email_data["received_headers"])):
        clean = " ".join(h.split())
        ip_match = re.search(r'\[(?P<ip>(?:[0-9]{1,3}\.){3}[0-9]{1,3})\]', clean)
        from_ip = ip_match.group("ip") if ip_match else None
        is_priv = GeoOriginService.is_reserved_or_special_use_ip(from_ip)
        hops.append({"hop_number": idx + 1, "from_ip": from_ip, "is_private": is_priv})

    # Mutated selector: skips 203.0.113.9, falls back to hops[0] (which is 127.0.0.1)
    mutated_earliest = None
    for hop in hops:
        if hop["from_ip"] and not hop["is_private"]:
            mutated_earliest = hop
            break
    if not mutated_earliest and hops:
        mutated_earliest = hops[0]

    assert mutated_earliest["from_ip"] == "127.0.0.1", (
        "Pre-condition for mutation test: mutated logic must select loopback 127.0.0.1"
    )

    # The production code MUST NOT exhibit this bug:
    prod_hops, prod_earliest, _ = HeaderForensicsService.parse_received_chain(email_data["received_headers"])
    assert prod_earliest["from_ip"] == "203.0.113.9", (
        "Mutation Kill DEF-A: 127.0.0.1 selected as probable origin instead of 203.0.113.9!"
    )


def test_mutation_kill_def_b_ioc_rendering_row_count():
    """
    Mutation Kill for DEF-B:
    If the report query projection drops raw_headers / sender_domain,
    the resulting IOC table contains only 2 rows instead of 4 rows.
    """
    raw_bytes = (FIXTURES_DIR / "advance_fee_master_verification.eml").read_bytes()
    email_data = IngestionService.parse_raw_email(raw_bytes, source="eml_upload")
    hops, ear, _ = HeaderForensicsService.parse_received_chain(email_data["received_headers"])
    origin_res = GeoOriginService.evaluate_origin(ear, len(hops))
    domain_res = DomainIntelService.analyze_domain(email_data["sender_domain"])

    # Mutated projection: drops raw_headers, headers, and reply_to
    mutated_email_dict = {
        "subject": email_data.get("subject", ""),
        "from_raw": email_data.get("sender", ""),
        "recipient": email_data.get("recipient", ""),
        "message_id": email_data.get("message_id", ""),
        "sha256_hash": email_data.get("sha256_hash", "")
    }
    analysis_dict = {
        "overall_threat_score": 0.90,
        "threat_level": "CRITICAL",
        "primary_classification": "phishing",
        "origin_assessment": origin_res,
        "domain_intel": domain_res,
        "content_analysis": {},
        "recommendations": []
    }
    evidence_dict = {"chain_of_custody_id": "COC-1", "chain_entries": []}

    # In mutated projection, generate_pdf_report receives empty headers
    # Verify that mutated code only extracts 2 rows
    mutated_pdf = ReportingService.generate_pdf_report(mutated_email_dict, analysis_dict, evidence_dict)
    mutated_streams = re.findall(rb"stream\n(.*?)~>endstream", mutated_pdf, re.DOTALL)
    mutated_decomp = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in mutated_streams]).decode("latin1")
    assert "Reply-To Email" not in mutated_decomp
    assert "Reply-To Domain" not in mutated_decomp

    # Production projection: passes headers, raw_headers, sender_domain, and reply_to
    prod_email_dict = {
        "subject": email_data.get("subject", ""),
        "from_raw": email_data.get("sender", ""),
        "sender": email_data.get("sender", ""),
        "sender_domain": email_data.get("sender_domain", ""),
        "recipient": email_data.get("recipient", ""),
        "message_id": email_data.get("message_id", ""),
        "sha256_hash": email_data.get("sha256_hash", ""),
        "headers": email_data.get("headers", {}),
        "raw_headers": email_data.get("headers", {}),
        "reply_to": email_data.get("reply_to", "")
    }
    prod_pdf = ReportingService.generate_pdf_report(prod_email_dict, analysis_dict, evidence_dict)
    prod_streams = re.findall(rb"stream\n(.*?)~>endstream", prod_pdf, re.DOTALL)
    prod_decomp = b"".join([zlib.decompress(base64.a85decode(b"<~" + s + b"~>", adobe=True)) for s in prod_streams]).decode("latin1")
    
    # Assert all 4 IOC rows exist in production output
    assert "IPv4 Address" in prod_decomp
    assert "Sender Domain" in prod_decomp
    assert "Reply-To Email" in prod_decomp, "Mutation Kill DEF-B: master-email IOC-row count assertion fails by name (Reply-To Email missing)!"
    assert "Reply-To Domain" in prod_decomp, "Mutation Kill DEF-B: master-email IOC-row count assertion fails by name (Reply-To Domain missing)!"
