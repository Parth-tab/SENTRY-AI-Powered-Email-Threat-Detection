import sys
import os
import time
import json
from pathlib import Path
from collections import Counter

# Add backend to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.services.ingestion import IngestionService
from app.services.header_forensics import HeaderForensicsService
from app.services.content_analysis import ContentAnalysisService
from app.services.domain_intel import DomainIntelService
from app.services.geo_origin import GeoOriginService
from app.services.threat_intel import ThreatIntelService
from app.ml.classifier import ThreatClassifier
import argparse

REPO_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CORPUS_DIR = REPO_ROOT / "sample_emails"

def process_single_email(file_path: Path):
    raw_bytes = file_path.read_bytes()
    
    # 1. Ingestion
    email_data = IngestionService.parse_raw_email(raw_bytes, source=f"ham_test_{file_path.name}")
    
    # 2. Header Forensics
    hops, earliest_hop, hop_anomalies = HeaderForensicsService.parse_received_chain(email_data.get("received_headers", []))
    auth_results = HeaderForensicsService.evaluate_authentication(email_data.get("headers", {}))
    detected_anomalies = HeaderForensicsService.detect_anomalies(email_data, earliest_hop)
    all_anomalies = list(set(hop_anomalies + detected_anomalies))
    
    header_res = {
        "relay_hops_count": len(hops),
        "relay_path": hops,
        "earliest_reliable_hop": earliest_hop,
        "authentication": auth_results,
        "header_anomalies": all_anomalies
    }
    
    # 3. Content Analysis
    content_res = ContentAnalysisService.analyze_content(email_data)
    
    # 4. Domain Intelligence
    domain_res = DomainIntelService.analyze_domain(
        email_data.get("sender_domain", ""),
        sender_ip=earliest_hop.get("from_ip") if earliest_hop else None
    )
    
    # 5. Geolocation & Origin
    origin_res = GeoOriginService.evaluate_origin(earliest_hop, relay_hops_count=len(hops))
    
    # 6. Mock/Local Threat Intel (offline safe)
    threat_intel_res = {
        "corroboration_score": 0.0,
        "feed_matches": [],
        "risk_level": "CLEAN"
    }
    
    # 7. Threat Classification
    classification_res = ThreatClassifier.evaluate(
        email_data=email_data,
        header_res=header_res,
        content_res=content_res,
        domain_res=domain_res,
        origin_res=origin_res,
        threat_intel_res=threat_intel_res
    )
    
    return {
        "file": file_path.name,
        "subject": email_data.get("subject", ""),
        "sender": email_data.get("sender", ""),
        "threat_score": float(classification_res.get("overall_threat_score", 0.0)),
        "threat_level": classification_res.get("threat_level", "UNKNOWN"),
        "primary_classification": classification_res.get("primary_classification", "UNKNOWN"),
        "confidence": float(classification_res.get("classification_confidence", 0.0)),
        "hops_count": len(hops),
        "origin_ip": origin_res.get("probable_origin_ip", "Unknown"),
        "origin_country": origin_res.get("geolocation", {}).get("country", "Unknown")
    }

def main():
    parser = argparse.ArgumentParser(description="SENTRY Ham Corpus Benchmark Runner")
    parser.add_argument("--corpus-path", type=str, default=str(DEFAULT_CORPUS_DIR),
                        help="Path to directory containing email corpus files (.eml or raw text)")
    parser.add_argument("--output-dir", type=str, default="evaluation/runs/ham_test",
                        help="Directory to save summary and aggregate evaluation artifacts")
    parser.add_argument("--limit", type=int, default=None,
                        help="Optional limit on maximum number of emails to evaluate")
    args = parser.parse_args()

    corpus_dir = Path(args.corpus_path)
    if not corpus_dir.exists() or not corpus_dir.is_dir():
        print(f"Error: Corpus directory '{corpus_dir}' does not exist or is not a directory.")
        print("Usage: python tools/test_ham_corpus.py --corpus-path /path/to/ham_emails")
        sys.exit(1)
        
    all_files = sorted([
        f for f in corpus_dir.iterdir()
        if f.is_file() and not f.name.endswith((".md", ".py", ".pyc", ".json", ".png", ".log"))
        and f.name.lower() not in ("readme.md", "license", ".gitignore")
    ])
    if args.limit:
        all_files = all_files[:args.limit]
    total_files = len(all_files)
    if total_files == 0:
        print(f"Error: No files found in corpus directory '{corpus_dir}'.")
        sys.exit(1)

    print(f"Found {total_files} email files in {corpus_dir}")
    
    # Run test on all files
    start_time = time.time()
    results = []
    errors = []
    
    threat_levels = Counter()
    classifications = Counter()
    score_bins = Counter()
    countries = Counter()
    
    print(f"Starting analysis of {total_files} ham emails...")
    
    for idx, f in enumerate(all_files, 1):
        try:
            res = process_single_email(f)
            results.append(res)
            
            lvl = res["threat_level"]
            cls_name = res["primary_classification"]
            score = res["threat_score"]
            country = res["origin_country"]
            
            threat_levels[lvl] += 1
            classifications[cls_name] += 1
            countries[country] += 1
            
            if score < 0.2:
                score_bins["0.00-0.19 (Minimal)"] += 1
            elif score < 0.4:
                score_bins["0.20-0.39 (Low)"] += 1
            elif score < 0.6:
                score_bins["0.40-0.59 (Moderate)"] += 1
            elif score < 0.8:
                score_bins["0.60-0.79 (High)"] += 1
            else:
                score_bins["0.80-1.00 (Critical)"] += 1
                
        except Exception as e:
            errors.append({"file": f.name, "error": str(e)})
            
        if idx % 1000 == 0 or idx == total_files:
            elapsed = time.time() - start_time
            rate = idx / elapsed if elapsed > 0 else 0
            print(f"Processed {idx}/{total_files} ({idx/total_files*100:.1f}%) -- Rate: {rate:.1f} emails/sec")
            
    total_time = time.time() - start_time
    avg_latency_ms = (total_time / total_files * 1000) if total_files > 0 else 0
    throughput = total_files / total_time if total_time > 0 else 0
    
    # Compute accuracy on Ham dataset
    # On a pure ham dataset, Legitimate / Low Threat = True Negative (TN)
    # High / Critical / Phishing / BEC = False Positive (FP)
    legit_count = classifications["legitimate"]
    low_threat_count = threat_levels["LOW"]
    fp_critical = threat_levels["CRITICAL"]
    fp_high = threat_levels["HIGH"]
    fp_medium = threat_levels["MEDIUM"]
    
    clean_rate = (low_threat_count / len(results) * 100) if results else 0
    fp_rate = ((fp_high + fp_critical) / len(results) * 100) if results else 0
    
    summary = {
        "dataset": str(corpus_dir),
        "total_files": total_files,
        "successful_parses": len(results),
        "parse_errors": len(errors),
        "total_time_seconds": round(total_time, 2),
        "average_latency_ms": round(avg_latency_ms, 2),
        "throughput_emails_per_sec": round(throughput, 1),
        "threat_level_distribution": dict(threat_levels),
        "primary_classification_distribution": dict(classifications),
        "score_distribution": dict(score_bins),
        "top_origin_countries": dict(countries.most_common(10)),
        "clean_classification_rate_pct": round(clean_rate, 2),
        "false_positive_rate_pct": round(fp_rate, 2),
        "errors": errors[:10]
    }
    
    # Save detailed JSON output
    out_dir = Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ham_test_summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    
    # Also save top false positive samples for inspection
    high_threat_samples = [r for r in results if r["threat_level"] in ["HIGH", "CRITICAL"]]
    (out_dir / "ham_false_positives.json").write_text(json.dumps(high_threat_samples, indent=2), encoding="utf-8")
    
    print("\n" + "="*60)
    print("SENTRY HAM CORPUS EVALUATION COMPLETE")
    print("="*60)
    print(f"Total Emails Analyzed: {total_files}")
    print(f"Successful: {len(results)} | Errors: {len(errors)}")
    print(f"Execution Time: {total_time:.2f}s ({throughput:.1f} emails/sec | {avg_latency_ms:.2f}ms/email)")
    print(f"\nThreat Level Distribution:")
    for lvl, cnt in threat_levels.most_common():
        print(f"  - {lvl:<10}: {cnt:>5} ({cnt/len(results)*100:.2f}%)")
    print(f"\nPrimary Classification Distribution:")
    for cls_name, cnt in classifications.most_common():
        print(f"  - {cls_name:<15}: {cnt:>5} ({cnt/len(results)*100:.2f}%)")
    print(f"\nClean Rate (LOW threat): {clean_rate:.2f}%")
    print(f"False Positive Rate (HIGH/CRITICAL): {fp_rate:.2f}%")
    print("="*60)

if __name__ == "__main__":
    main()
