import os
import re
import json
from pathlib import Path

REPO_ROOT = Path("E:/SENTRY")

GROUND_TRUTH = {
    "pytest_tests": 156,
    "pytest_modules": 23,
    "golden_gates": 21,
    "total_defects": 68,
    "resolved_defects": 58,
    "accuracy": 0.961,
    "macro_f1": 0.952,
    "roc_auc": 0.988,
    "validation_samples": 15240,
    "demo_emails": 18,
    "demo_campaigns": 3,
    "demo_threat_critical": 15,
    "demo_threat_medium": 1,
    "demo_threat_low": 2,
    "ham_unique": 6777,
    "ham_files": 6951,
    "ham_fp_rate": 0.0,
    "app_version": "1.1.0",
    "feature_dims": 47,
    "fastapi_endpoints": 29,
    "business_endpoints": 24,
}

CONFIG_ENV_VARS = [
    "PROJECT_NAME", "VERSION", "API_V1_STR", "ENVIRONMENT", "DEBUG",
    "DATABASE_URL", "SYNC_DATABASE_URL", "REDIS_URL", "NEO4J_URI",
    "NEO4J_USER", "NEO4J_PASSWORD", "SERVE_STATIC", "BUILD_MODE",
    "FRONTEND_DIST_DIR", "CORS_ORIGINS", "SENTRY_API_TOKEN", "SECRET_KEY",
    "ADMIN_TOKEN", "ALGORITHM", "ACCESS_TOKEN_EXPIRE_MINUTES",
    "EVIDENCE_VAULT_DIR", "LOGS_DIR", "VIRUSTOTAL_API_KEY",
    "URLHAUS_API_KEY", "THREATFOX_API_KEY"
]

ALL_DOCS = [
    "README.md",
    "DILIGENCE.md",
    "AGENTS.md",
    "CONTRIBUTING.md",
    "DEPLOYMENT.md",
    "SECURITY.md",
    "CHANGELOG.md",
    "docs/ARCHITECTURE.md",
    "docs/API.md",
    "docs/DEMO_SCRIPT.md",
    "docs/FEATURE_TOUR.md",
    "docs/RUNBOOK.md",
    "docs/TRACEABILITY_MATRIX.md",
    "docs/DIFFERENTIATION_DOSSIER.md",
    "docs/QA_ARMOR.md",
    "docs/RELEASE_NOTES_v1.1.0.md",
    "sample_emails/README.md",
    "evaluation/final_report.md",
    "evaluation/ERRATA.md",
    "evaluation/HANDOFF.md",
    "evaluation/MASTER_SPEC.md",
    "evaluation/ext_eval/EXT_REVIEW.md",
    "evaluation/graph_redesign/GRAPH_REVIEW.md",
    "evaluation/mrws/SHIP_GATE_REVIEW.md",
    "evaluation/viability/VIABILITY_REPORT.md",
    "evaluation/viability/kill_memo.md",
    "evaluation/final_inch/HUMAN_RUNBOOK.md",
    "evaluation/final_inch/STRANGER_PROTOCOL.md",
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md"
]

def extract_all():
    extracted_claims = []
    broken_links = []
    env_var_diffs = []

    for doc_rel in ALL_DOCS:
        doc_path = REPO_ROOT / doc_rel
        if not doc_path.exists():
            continue

        text = doc_path.read_text(encoding="utf-8")
        lines = text.splitlines()
        curr_section = "Top"

        is_historical = any(h in doc_rel for h in ["CHANGELOG.md", "evaluation/final_report.md", "evaluation/mrws/SHIP_GATE_REVIEW.md", "docs/RELEASE_NOTES_v1.1.0.md", "evaluation/HANDOFF.md"])

        for idx, line in enumerate(lines, 1):
            if line.startswith("#"):
                curr_section = line.lstrip("#").strip()

            # Check test count claims
            for m in re.finditer(r"\b(\d+)\s*(tests|unit tests|integration tests|pytest suite|passing tests)", line, re.I):
                num = int(m.group(1))
                if num in [41, 59, 99, 138, 149, 153, 156]:
                    status = "AGREE" if num == GROUND_TRUTH["pytest_tests"] else ("AGREE_HISTORICAL" if is_historical else "DRIFT")
                    extracted_claims.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "claim_type": "test_count",
                        "claim_text": line.strip(),
                        "current_val": num,
                        "ground_truth": GROUND_TRUTH["pytest_tests"],
                        "status": status
                    })

            # Check gate count claims
            for m in re.finditer(r"\b(\d+)\s*(?:/\s*\d+\s*)?(golden gates|golden checks|verification gates|gates passing|checks across|gate harness)", line, re.I):
                num = int(m.group(1))
                if num in [3, 8, 19, 20, 21]:
                    status = "AGREE" if num == GROUND_TRUTH["golden_gates"] else ("AGREE_HISTORICAL" if is_historical else "DRIFT")
                    extracted_claims.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "claim_type": "gate_count",
                        "claim_text": line.strip(),
                        "current_val": num,
                        "ground_truth": GROUND_TRUTH["golden_gates"],
                        "status": status
                    })

            # Check defect count claims
            for m in re.finditer(r"\b(\d+)\s*(tracked defect|defect and gap objects|defects across repo|tracked defects|defects total)", line, re.I):
                num = int(m.group(1))
                if num in [50, 55, 59, 67, 68]:
                    status = "AGREE" if num == GROUND_TRUTH["total_defects"] else ("AGREE_HISTORICAL" if is_historical else "DRIFT")
                    extracted_claims.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "claim_type": "defect_count",
                        "claim_text": line.strip(),
                        "current_val": num,
                        "ground_truth": GROUND_TRUTH["total_defects"],
                        "status": status
                    })

            # Check version claims
            for m in re.finditer(r"\b(v\d+\.\d+\.\d+)\b", line):
                ver = m.group(1)
                # If document claims current version is v1.0.0 or v1.0.1 in non-historical context
                if ver in ["v1.0.0", "v1.0.1", "v1.1.0", "v1.2.0"]:
                    status = "AGREE" if ver == "v1.1.0" or (ver == "v1.2.0" and "roadmap" in line.lower()) else ("AGREE_HISTORICAL" if is_historical else "INFO")
                    extracted_claims.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "claim_type": "version_mention",
                        "claim_text": line.strip(),
                        "current_val": ver,
                        "ground_truth": "v1.1.0 (v1.2.0 on roadmap / graph release)",
                        "status": status
                    })

            # Check dead links
            for m in re.finditer(r"\[([^\]]+)\]\(([^)]+)\)", line):
                link_text = m.group(1)
                link_url = m.group(2).strip()
                # Exclude external urls and anchors
                if link_url.startswith("http://") or link_url.startswith("https://") or link_url.startswith("mailto:") or link_url.startswith("#"):
                    continue

                clean_url = link_url.split("#")[0].split("?")[0]
                if not clean_url:
                    continue

                if clean_url.startswith("file:///"):
                    # file URI in markdown is a portability defect
                    broken_links.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "link_text": link_text,
                        "link_target": link_url,
                        "reason": "Absolute file:/// URI instead of repo-relative path"
                    })
                    continue

                # Relative resolution
                doc_dir = (REPO_ROOT / doc_rel).parent
                target1 = (doc_dir / clean_url).resolve()
                target2 = (REPO_ROOT / clean_url.lstrip("/")).resolve()

                if not target1.exists() and not target2.exists():
                    broken_links.append({
                        "doc": doc_rel,
                        "line": idx,
                        "section": curr_section,
                        "link_text": link_text,
                        "link_target": link_url,
                        "reason": "Target file does not exist in repo"
                    })

    # Audit DEPLOYMENT.md env vars vs config.py
    deploy_doc = REPO_ROOT / "DEPLOYMENT.md"
    if deploy_doc.exists():
        deploy_text = deploy_doc.read_text(encoding="utf-8")
        for env_var in re.findall(r"\b([A-Z0-9_]{4,})\b", deploy_text):
            if any(env_var.startswith(prefix) for prefix in ["SENTRY_", "DATABASE_", "REDIS_", "NEO4J_", "SECRET_", "ADMIN_", "CORS_", "LOGS_", "BUILD_", "SERVE_", "EVIDENCE_"]):
                if env_var not in CONFIG_ENV_VARS:
                    env_var_diffs.append({
                        "doc": "DEPLOYMENT.md",
                        "env_var": env_var,
                        "status": "NOT_IN_CONFIG_PY"
                    })

    return extracted_claims, broken_links, env_var_diffs

if __name__ == "__main__":
    claims, broken_links, env_var_diffs = extract_all()
    out = {
        "ground_truth": GROUND_TRUTH,
        "claims_count": len(claims),
        "claims": claims,
        "broken_links_count": len(broken_links),
        "broken_links": broken_links,
        "env_var_diffs": env_var_diffs
    }
    out_file = REPO_ROOT / "evaluation/docs_unification/claim_ledger.json"
    out_file.write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"Total claims: {len(claims)}")
    print(f"Broken links: {len(broken_links)}")
    print(f"Env var diffs: {len(env_var_diffs)}")
