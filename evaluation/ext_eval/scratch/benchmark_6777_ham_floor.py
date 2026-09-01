import os
import sys
import zipfile
import io
import time
from pathlib import Path
from collections import Counter

REPO_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(REPO_ROOT / "backend"))

from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.ml.classifier import ThreatClassifier

HAM_ZIP_PATH = r"C:\Users\Parth\Downloads\ham_zipped.zip"

def main():
    if not os.path.exists(HAM_ZIP_PATH):
        print(f"Error: {HAM_ZIP_PATH} not found.")
        return

    print(f"Opening 6,777 Ham Corpus archive: {HAM_ZIP_PATH} ({os.path.getsize(HAM_ZIP_PATH):,} bytes)...")
    zf = zipfile.ZipFile(HAM_ZIP_PATH, 'r')
    names = [n for n in zf.namelist() if not n.endswith('/') and not n.startswith('__MACOSX')]
    total_files = len(names)
    print(f"Total entries in archive: {total_files}")

    pre_floor_levels = Counter()
    post_floor_levels = Counter()
    
    # Trackers for floor delta
    elevated_by_floor = []
    auth_patterns_for_elevated = Counter()
    auth_patterns_overall = Counter()

    start_time = time.time()
    processed = 0

    for name in names:
        try:
            raw_bytes = zf.read(name)
            if not raw_bytes:
                continue
            data = IngestionService.parse_raw_email(raw_bytes, source=name)
            
            # Fast header analysis
            hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(data.get("received_headers", []))
            auth = HeaderForensicsService.evaluate_authentication(data.get("headers", {}))
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

            spf = auth.get("spf", {}).get("result", "none")
            dkim = auth.get("dkim", {}).get("result", "none")
            dmarc = auth.get("dmarc", {}).get("result", "none")
            auth_pat = f"SPF:{spf}|DKIM:{dkim}|DMARC:{dmarc}"
            auth_patterns_overall[auth_pat] += 1

            pre_score = cls_res["score_pre_floor"]
            post_score = cls_res["overall_threat_score"]
            floor_active = cls_res["floor_applied"]

            # Compute pre-floor level
            if pre_score >= 0.85:
                pre_lvl = "CRITICAL"
            elif pre_score >= 0.70:
                pre_lvl = "HIGH"
            elif pre_score >= 0.40:
                pre_lvl = "MEDIUM"
            else:
                pre_lvl = "LOW"

            post_lvl = cls_res["threat_level"]

            pre_floor_levels[pre_lvl] += 1
            post_floor_levels[post_lvl] += 1

            if floor_active:
                auth_patterns_for_elevated[auth_pat] += 1
                elevated_by_floor.append({
                    "file": name,
                    "subject": data.get("subject", "")[:60],
                    "sender": data.get("sender", ""),
                    "auth_pat": auth_pat,
                    "pre_score": pre_score,
                    "post_score": post_score
                })

            processed += 1
            if processed % 1000 == 0 or processed == total_files:
                elapsed = time.time() - start_time
                print(f"Processed {processed:,}/{total_files:,} ({processed/total_files*100:.1f}%) -- {processed/elapsed:.1f} emails/sec")

        except Exception as e:
            continue

    elapsed = time.time() - start_time
    print("\n" + "="*80)
    print("6,777 HAM CORPUS BENCHMARK & SEVERITY FLOOR DELTA RECEIPT")
    print("="*80)
    print(f"Total Emails Evaluated:  {processed:,}")
    print(f"Execution Wall Time:     {elapsed:.2f}s ({processed/elapsed:.1f} emails/sec)")
    print("\nPre-Floor Threat Level Distribution:")
    for lvl in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        print(f"  - {lvl:8}: {pre_floor_levels[lvl]:5,} ({pre_floor_levels[lvl]/processed*100:.2f}%)")

    print("\nPost-Floor Threat Level Distribution:")
    for lvl in ["LOW", "MEDIUM", "HIGH", "CRITICAL"]:
        print(f"  - {lvl:8}: {post_floor_levels[lvl]:5,} ({post_floor_levels[lvl]/processed*100:.2f}%)")

    print(f"\nTotal Emails Elevated by Severity Floor: {len(elevated_by_floor)} ({len(elevated_by_floor)/processed*100:.2f}%)")
    print("\nAuthentication Header Patterns for Floor-Elevated Emails:")
    for pat, count in auth_patterns_for_elevated.most_common():
        print(f"  - {pat:35}: {count:5,} emails ({count/len(elevated_by_floor)*100:.1f}%)")

    if elevated_by_floor:
        print("\nSample Floor-Elevated Ham Emails (first 10):")
        for item in elevated_by_floor[:10]:
            print(f"  * {item['file']:30} | {item['auth_pat']:35} | Pre: {item['pre_score']:.2f} -> Post: {item['post_score']:.2f} | Subj: {item['subject']}")

if __name__ == "__main__":
    main()
