import os
import glob
import sys
sys.path.insert(0, "backend")

from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.ml.classifier import ThreatClassifier
from app.services.domain_intel import DomainIntelService
from app.services.content_analysis import ContentAnalysisService
from app.services.geo_origin import GeoOriginService

print(f"{'Filename':35} | {'SPF':8} | {'DKIM':8} | {'DMARC':8} | {'Policy':10} | {'Spoofed':7} | {'Pre-Score':9} | {'Pre-Lvl':8}")
print("-" * 110)

for f in sorted(glob.glob("sample_emails/*.eml")):
    with open(f, "rb") as fp:
        raw = fp.read()
    data = IngestionService.parse_raw_email(raw)
    auth = HeaderForensicsService.evaluate_authentication(data["headers"])
    hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(data["received_headers"])
    anomalies = HeaderForensicsService.detect_anomalies(data, earliest_hop)
    all_anomalies = list(set(hop_anomalies + anomalies))
    
    header_res = {
        "relay_hops_count": len(hops),
        "relay_path": hops,
        "earliest_reliable_hop": earliest_hop,
        "authentication": auth,
        "header_anomalies": all_anomalies
    }
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))
    content_res = ContentAnalysisService.analyze_content(data)
    domain_res = DomainIntelService.analyze_domain(data.get("sender_domain", ""))
    
    cls_res = ThreatClassifier.evaluate(
        email_data=data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res
    )
    
    spf = auth["spf"]["result"]
    dkim = auth["dkim"]["result"]
    dmarc = auth["dmarc"]["result"]
    pol = auth["dmarc"].get("policy", "none")
    spoofed = str(auth["is_spoofed"])
    score = f"{cls_res['overall_threat_score']:.2f}"
    lvl = cls_res["threat_level"]
    print(f"{os.path.basename(f):35} | {spf:8} | {dkim:8} | {dmarc:8} | {pol:10} | {spoofed:7} | {score:9} | {lvl:8}")
