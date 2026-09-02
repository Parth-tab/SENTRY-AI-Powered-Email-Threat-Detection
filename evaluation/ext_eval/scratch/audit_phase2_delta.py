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

print(f"{'Filename':33} | {'Auth SPF':8} | {'Auth DMARC':10} | {'DMARC Pol':9} | {'Spoofed':7} | {'Pre-Score':9} | {'Post-Score':10} | {'Subtype':18} | {'Post-Lvl':8}")
print("-" * 135)

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
    dmarc = auth["dmarc"]["result"]
    pol = auth["dmarc"].get("policy", "none")
    spoofed = str(auth["is_spoofed"])
    score = f"{cls_res['overall_threat_score']:.2f}"
    subtype = str(cls_res.get("classification_subtype") or "None")
    lvl = cls_res["threat_level"]
    print(f"{os.path.basename(f):33} | {spf:8} | {dmarc:10} | {pol:9} | {spoofed:7} | {'—':9} | {score:10} | {subtype:18} | {lvl:8}")
