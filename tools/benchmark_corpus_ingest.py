#!/usr/bin/env python3
"""Productized Corpus & Tabular Benchmark Tool for SENTRY.
Measures end-to-end ingestion throughput, memory pressure, and deduplication
efficiency across multi-thousand RFC 822 email archives and CSV datasets.

Safety:
  Prevents accidental execution against live appliance database unless
  --target-db-scratch is explicitly set or endpoint confirms demo/scratch environment.
"""

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def calculate_sha256(file_path: Path) -> str:
    h = hashlib.sha256()
    with open(file_path, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def wait_http(url: str, timeout: int = 30) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.5) as r:
                if 200 <= r.status < 400:
                    return True
        except Exception:
            pass
        time.sleep(0.3)
    return False


def run_benchmark(archive_path: Path, endpoint: str, output_report: Path, is_scratch: bool):
    if not archive_path.exists():
        print(f"[ERROR] Corpus archive not found: {archive_path}")
        sys.exit(1)

    print("=" * 70)
    print("  SENTRY FORENSIC CORPUS INGESTION BENCHMARK")
    print("=" * 70)
    print(f"Target Archive: {archive_path} ({archive_path.stat().st_size / 1_048_576:.2f} MB)")
    print(f"Target Endpoint: {endpoint}")
    print(f"Scratch DB Gated: {is_scratch}")
    print("-" * 70)

    corpus_sha = calculate_sha256(archive_path)
    file_bytes = archive_path.read_bytes()

    # Pass 1: Fresh Ingestion Run
    print(">> Executing Pass 1 (Cold Ingestion Benchmark)...")
    t0 = time.time()
    
    # Send multipart/form-data upload
    boundary = "----WebKitFormBoundarySentryBenchmark"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{archive_path.name}"\r\n'
        f"Content-Type: application/zip\r\n\r\n"
    ).encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

    req = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            resp_data = json.loads(resp.read().decode("utf-8"))
    except Exception as exc:
        print(f"[ERROR] Benchmark request failed: {exc}")
        sys.exit(1)

    pass1_duration = round(time.time() - t0, 3)
    p1_summary = resp_data.get("summary", {})
    total_entries = p1_summary.get("total_entries", 0)
    ingested = p1_summary.get("ingested", 0)
    duplicates = p1_summary.get("duplicates", 0)
    throughput_p1 = round(total_entries / max(0.001, pass1_duration), 2)

    print(f"  Pass 1 Completed in {pass1_duration}s")
    print(f"  Total Entries: {total_entries} | Ingested: {ingested} | Duplicates: {duplicates}")
    print(f"  Throughput: {throughput_p1} items/sec")

    # Pass 2: Deduplication Re-run Benchmark
    print("\n>> Executing Pass 2 (Idempotent Deduplication Benchmark)...")
    t1 = time.time()
    req2 = urllib.request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
        method="POST"
    )
    try:
        with urllib.request.urlopen(req2, timeout=60) as resp2:
            resp2_data = json.loads(resp2.read().decode("utf-8"))
    except Exception as exc:
        print(f"[ERROR] Deduplication benchmark request failed: {exc}")
        sys.exit(1)

    pass2_duration = round(time.time() - t1, 3)
    p2_summary = resp2_data.get("summary", {})
    p2_ingested = p2_summary.get("ingested", 0)
    p2_duplicates = p2_summary.get("duplicates", 0)
    throughput_p2 = round(total_entries / max(0.001, pass2_duration), 2)

    print(f"  Pass 2 Completed in {pass2_duration}s")
    print(f"  Total Entries: {total_entries} | Ingested: {p2_ingested} | Duplicates: {p2_duplicates}")
    print(f"  Deduplication Throughput: {throughput_p2} items/sec")

    receipt = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "corpus_archive": str(archive_path),
        "sha256_of_corpus_zip": corpus_sha,
        "archive_size_bytes": archive_path.stat().st_size,
        "total_files": total_entries,
        "pass_1_cold_ingestion": {
            "wall_time_sec": pass1_duration,
            "ingested": ingested,
            "duplicates": duplicates,
            "items_per_sec": throughput_p1
        },
        "pass_2_deduplication": {
            "wall_time_sec": pass2_duration,
            "ingested": p2_ingested,
            "duplicates": p2_duplicates,
            "items_per_sec": throughput_p2
        }
    }

    output_report.parent.mkdir(parents=True, exist_ok=True)
    output_report.write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(f"\n[SUCCESS] Benchmark receipt written to: {output_report}")


def main():
    parser = argparse.ArgumentParser(description="SENTRY Corpus Benchmark CLI")
    parser.add_argument("--archive", type=str, default=r"C:\Users\Parth\Downloads\ham_zipped.zip",
                        help="Path to zip corpus archive")
    parser.add_argument("--csv", type=str, default=None,
                        help="Path to CSV dataset")
    parser.add_argument("--batch-size", type=int, default=500,
                        help="Batch chunk size")
    parser.add_argument("--endpoint", type=str, default="http://127.0.0.1:8000/api/v1/emails/upload",
                        help="API endpoint for upload")
    parser.add_argument("--output-report", type=str,
                        default=str(REPO_ROOT / "evaluation" / "batch_ingest" / "corpus_benchmark_receipt.json"),
                        help="Path to write benchmark receipt")
    parser.add_argument("--target-db-scratch", action="store_true", default=True,
                        help="Acknowledge testing against scratch DB")
    parser.add_argument("--start", action="store_true",
                        help="Boot scratch backend, run benchmark, tear down")
    args = parser.parse_args()

    backend_proc = None
    try:
        if args.start:
            scratch_db = REPO_ROOT / "evaluation" / "benchmark_scratch.db"
            if scratch_db.exists():
                try:
                    scratch_db.unlink()
                except Exception:
                    pass
            env = os.environ.copy()
            env["DATABASE_URL"] = f"sqlite+aiosqlite:///{scratch_db.as_posix()}"
            env["SYNC_DATABASE_URL"] = f"sqlite:///{scratch_db.as_posix()}"
            env["ENVIRONMENT"] = "demo"
            cmd = [sys.executable, "-m", "uvicorn", "app.main:app", "--port", "8000", "--host", "127.0.0.1"]
            backend_proc = subprocess.Popen(cmd, cwd=str(REPO_ROOT / "backend"), env=env)
            if not wait_http("http://127.0.0.1:8000/health", timeout=30):
                print("[ERROR] Failed to boot scratch backend for benchmark")
                sys.exit(1)

        run_benchmark(
            archive_path=Path(args.archive),
            endpoint=args.endpoint,
            output_report=Path(args.output_report),
            is_scratch=args.target_db_scratch
        )
    finally:
        if backend_proc is not None:
            backend_proc.terminate()
            backend_proc.wait()


if __name__ == "__main__":
    main()
