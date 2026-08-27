#!/usr/bin/env python3
"""GAUNTLET Test Battery Master Runner
Executes all 12 evaluation dimension check scripts and compiles evidence artifacts.
"""

import sys
import os
import argparse
import importlib.util
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
CHECKS_DIR = Path(__file__).resolve().parent / "checks"

DIMENSION_SCRIPTS = [
    ("D4_Security", "check_d04_security.py"),
    ("D7_Forensics", "check_d07_forensic_integrity.py"),
    ("D5_Reliability", "check_d05_reliability.py"),
    ("D12_Product_Fit", "check_d12_product_fit.py"),
    ("D6_Performance", "check_d06_performance.py"),
    ("D8_ML_Rigor", "check_d08_ml_rigor.py"),
    ("D9_API_Quality", "check_d09_api_quality.py"),
    ("D10_UX_Frontend", "check_d10_ux_frontend.py"),
    ("D11_Production", "check_d11_production.py"),
    ("D1_Code_Quality", "check_d01_code_quality.py"),
    ("D2_Test_Quality", "check_d02_test_quality.py"),
    ("D3_Architecture", "check_d03_architecture.py")
]

def run_battery(iteration: int = 0):
    evidence_dir = REPO_ROOT / "evaluation" / "runs" / f"iter_{iteration}" / "evidence"
    evidence_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n{'='*70}")
    print(f"  GAUNTLET BATTERY EXECUTION — ITERATION {iteration}")
    print(f"  Target Evidence Directory: {evidence_dir}")
    print(f"{'='*70}\n")

    results = {}
    for dim_name, script_name in DIMENSION_SCRIPTS:
        script_path = CHECKS_DIR / script_name
        if not script_path.exists():
            print(f"[-] Missing check script: {script_name}")
            continue

        spec = importlib.util.spec_from_file_location(dim_name, str(script_path))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)

        # Run dimension main function
        run_func = getattr(mod, f"run_{script_name.split('.')[0].replace('check_', '')}_checks", None)
        if not run_func:
            # Fallback to finding the first run_*_checks function
            for attr in dir(mod):
                if attr.startswith("run_") and attr.endswith("_checks"):
                    run_func = getattr(mod, attr)
                    break

        if run_func:
            res = run_func(evidence_dir)
            results[dim_name] = res
        else:
            print(f"[-] No runner function found in {script_name}")

    print(f"\n{'='*70}")
    print(f"  BATTERY SUMMARY — {len(results)}/12 DIMENSIONS COMPLETED")
    for dim, data in results.items():
        score = data.get("base_score", 0)
        floor = data.get("floor", 85)
        status = "PASS" if score >= floor else "BELOW FLOOR"
        print(f"    {dim:<22}: {score:>5.1f}% (Floor: {floor}%) [{status}]")
    print(f"{'='*70}\n")

    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="GAUNTLET Test Battery Master Runner")
    parser.add_argument("--iter", type=int, default=0, help="Iteration number for output artifacts")
    args = parser.parse_args()
    run_battery(args.iter)
