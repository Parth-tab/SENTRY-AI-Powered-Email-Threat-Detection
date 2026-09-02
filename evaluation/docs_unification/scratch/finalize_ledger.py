import json
from pathlib import Path

REPO_ROOT = Path("E:/SENTRY")

GROUND_TRUTH_DATA = {
    "test_suite": {
        "command": "python -m pytest --collect-only",
        "value": 156,
        "modules_count": 23,
        "execution_time_seconds": 3.87
    },
    "golden_harness": {
        "command": "python tools/verify_sentry.py --start",
        "value": 21,
        "status": "PASS (pass=21 fail=0 timeout=0)"
    },
    "defect_registry": {
        "command": "python -c \"import json; d=json.load(open('evaluation/defects.json')); ...\"",
        "current_defects_json_items": 67,
        "ext_eval_items": 9,
        "reconciled_master_total": 76,
        "status_breakdown": {
            "resolved": 65,
            "interim_mitigated": 1,
            "consolidated": 3,
            "deferred": 2,
            "open": 5
        }
    },
    "app_version": {
        "config_py": "1.1.0",
        "package_json": "1.1.0",
        "latest_git_tag": "v1.2.0"
    },
    "ml_metrics": {
        "accuracy": 0.961,
        "macro_f1": 0.952,
        "roc_auc_ovr": 0.988,
        "validation_samples": 15240,
        "feature_dimensions": 47,
        "ensemble_layers": 3
    },
    "corpora_counts": {
        "demo_corpus_emails": 18,
        "demo_campaigns": 3,
        "demo_threat_breakdown": {"CRITICAL": 15, "MEDIUM": 1, "LOW": 2},
        "ham_unique_emails": 6777,
        "ham_archive_files": 6951,
        "ham_fp_rate": 0.0
    },
    "api_endpoints": {
        "total_fastapi_routes": 29,
        "business_api_endpoints": 24
    }
}

DEFECT_FILINGS = [
    {
        "id": "DOC-001",
        "title": "Defect Registry Arithmetic & Diligence Synchronization Drift",
        "category": "Documentation / Ledger",
        "severity": "HIGH",
        "status": "open",
        "description": "Discrepancy between defects.json (67 items), ext_eval/state.json (9 EXT items), and DILIGENCE.md (68 items derived from 59 baseline + 9 EXT). Total objects across repository must be unified to 76 in defects.json and reconciled across all diligence tables."
    },
    {
        "id": "DOC-002",
        "title": "Stale Test Counts in QA Armor and PR Template",
        "category": "Documentation / CI",
        "severity": "MEDIUM",
        "status": "open",
        "description": "docs/QA_ARMOR.md references '43-test suite' and .github/PULL_REQUEST_TEMPLATE.md references '41 tests'. Live suite is 156 tests across 23 modules."
    },
    {
        "id": "DOC-003",
        "title": "Dead Relative Markdown Links and file:/// Absolute URIs",
        "category": "Documentation / Integrity",
        "severity": "MEDIUM",
        "status": "open",
        "description": "55 markdown links contain non-portable file:/// absolute paths or point to missing files (backend/app/api/deps.py in DILIGENCE.md, docker-compose.yml in kill_memo.md)."
    },
    {
        "id": "DOC-004",
        "title": "MBOX Handling Roadmap Target Stale in ARCHITECTURE.md",
        "category": "Documentation / Architecture",
        "severity": "LOW",
        "status": "open",
        "description": "docs/ARCHITECTURE.md:112 references defect MBOX-001 target as 'v1.1.0' instead of 'v1.2.0 roadmap'."
    },
    {
        "id": "DOC-005",
        "title": "Lack of Machine-Verified Fact Validation Gate in CI",
        "category": "Tooling / Verification",
        "severity": "HIGH",
        "status": "open",
        "description": "No automated CI validator exists to regenerate facts from live commands and assert zero drift against documentation."
    }
]

# Load claim extractor results
claims_file = REPO_ROOT / "evaluation/docs_unification/claim_ledger.json"
existing_data = json.loads(claims_file.read_text(encoding="utf-8"))

final_ledger = {
    "audit_phase": "PHASE0_CLAIM_LEDGER_AUDIT",
    "scanned_documents_count": len(existing_data.get("claims", [])),
    "ground_truth": GROUND_TRUTH_DATA,
    "claims_audited": existing_data.get("claims", []),
    "broken_links_audited": existing_data.get("broken_links", []),
    "filed_defects": DEFECT_FILINGS
}

claims_file.write_text(json.dumps(final_ledger, indent=2), encoding="utf-8")
print("Updated claim_ledger.json successfully.")
