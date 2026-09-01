import re
import os
import json
from pathlib import Path
from collections import defaultdict

REPO_ROOT = Path("E:/SENTRY")

GROUND_TRUTH = {
    "test_count": 156,
    "gate_count": 21,
    "defect_total": 68,
    "defect_resolved": 58,
    "accuracy": "0.961",
    "macro_f1": "0.952",
    "roc_auc": "0.988",
    "validation_samples": 15240,
    "demo_emails": 18,
    "demo_campaigns": 3,
    "ham_unique": 6777,
    "ham_total": 6951,
    "app_version": "1.1.0",
}

DOC_FILES = [
    # Root
    "AGENTS.md",
    "CHANGELOG.md",
    "CONTRIBUTING.md",
    "DEPLOYMENT.md",
    "DILIGENCE.md",
    "README.md",
    "SECURITY.md",
    # Docs
    "docs/API.md",
    "docs/ARCHITECTURE.md",
    "docs/DEMO_SCRIPT.md",
    "docs/DIFFERENTIATION_DOSSIER.md",
    "docs/FEATURE_TOUR.md",
    "docs/QA_ARMOR.md",
    "docs/RELEASE_NOTES_v1.1.0.md",
    "docs/RUNBOOK.md",
    "docs/TRACEABILITY_MATRIX.md",
    # Sample emails
    "sample_emails/README.md",
    # Public Evaluation docs
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
    # GitHub
    ".github/PULL_REQUEST_TEMPLATE.md",
    ".github/ISSUE_TEMPLATE/bug_report.md",
    ".github/ISSUE_TEMPLATE/feature_request.md"
]

def scan_markdown_files():
    claims = []
    dead_links = []

    # Patterns for quantitative claims
    test_re = re.compile(r"(\b\d+\b)\s*(?:passed|automated tests|unit & integration tests|unit tests|tests passing|tests collected|tests\b|test battery)", re.I)
    gate_re = re.compile(r"(\b\d+\b)\s*(?:golden checks|golden verification gates|golden gates|verification gates|gates passing|checks across|gate Playwright)", re.I)
    defect_re = re.compile(r"(\b\d+\b)\s*(?:tracked defect|defect and gap objects|defects|tracked defects|defect objects)", re.I)
    version_re = re.compile(r"\b(v\d+\.\d+\.\d+)\b", re.I)
    metric_re = re.compile(r"\b(0\.\d{3})\b")
    ham_re = re.compile(r"\b(6,?951|6,?777)\b")
    link_re = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

    for rel_path in DOC_FILES:
        full_path = REPO_ROOT / rel_path
        if not full_path.exists():
            continue
        
        content = full_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        current_section = "Header / Top"
        for line_idx, line in enumerate(lines, 1):
            if line.startswith("#"):
                current_section = line.strip("# ").strip()

            # 1. Test count claims
            for m in test_re.finditer(line):
                val_str = m.group(1)
                val = int(val_str)
                # Ignore small numbers like 1, 2, 3, 4, 5, 6, 8, 12, 18, 23 (module counts, dimensions, etc.) unless phrased as tests
                if val in [41, 50, 59, 99, 138, 149, 153, 156]:
                    classification = "AGREE" if val == GROUND_TRUTH["test_count"] else "DRIFT"
                    # If this is historical changelog or historical report, mark as AGREE (historical)
                    if "CHANGELOG.md" in rel_path or "final_report.md" in rel_path or "SHIP_GATE_REVIEW.md" in rel_path or "RELEASE_NOTES_v1.1.0.md" in rel_path:
                        if val != GROUND_TRUTH["test_count"]:
                            classification = "AGREE_HISTORICAL"
                    claims.append({
                        "doc": rel_path,
                        "line": line_idx,
                        "section": current_section,
                        "claim_type": "test_count",
                        "claim_text": line.strip(),
                        "current_doc_value": val,
                        "ground_truth_value": GROUND_TRUTH["test_count"],
                        "status": classification
                    })

            # 2. Gate count claims
            for m in gate_re.finditer(line):
                val_str = m.group(1)
                val = int(val_str)
                if val in [3, 8, 19, 20, 21]:
                    classification = "AGREE" if val == GROUND_TRUTH["gate_count"] else "DRIFT"
                    if "CHANGELOG.md" in rel_path or "final_report.md" in rel_path or "SHIP_GATE_REVIEW.md" in rel_path or "RELEASE_NOTES_v1.1.0.md" in rel_path:
                        if val != GROUND_TRUTH["gate_count"]:
                            classification = "AGREE_HISTORICAL"
                    claims.append({
                        "doc": rel_path,
                        "line": line_idx,
                        "section": current_section,
                        "claim_type": "gate_count",
                        "claim_text": line.strip(),
                        "current_doc_value": val,
                        "ground_truth_value": GROUND_TRUTH["gate_count"],
                        "status": classification
                    })

            # 3. Defect count claims
            for m in defect_re.finditer(line):
                val_str = m.group(1)
                val = int(val_str)
                if val in [50, 55, 58, 59, 63, 67, 68]:
                    classification = "AGREE" if val in [GROUND_TRUTH["defect_total"], GROUND_TRUTH["defect_resolved"]] else "DRIFT"
                    if "CHANGELOG.md" in rel_path or "final_report.md" in rel_path or "SHIP_GATE_REVIEW.md" in rel_path:
                        classification = "AGREE_HISTORICAL"
                    claims.append({
                        "doc": rel_path,
                        "line": line_idx,
                        "section": current_section,
                        "claim_type": "defect_count",
                        "claim_text": line.strip(),
                        "current_doc_value": val,
                        "ground_truth_value": GROUND_TRUTH["defect_total"],
                        "status": classification
                    })

            # 4. Check links in markdown
            for m in link_re.finditer(line):
                link_text = m.group(1)
                link_target = m.group(2).split("#")[0].split("?")[0]
                if not link_target or link_target.startswith("http://") or link_target.startswith("https://") or link_target.startswith("mailto:") or link_target.startswith("#"):
                    continue
                # Resolve relative path
                doc_dir = (REPO_ROOT / rel_path).parent
                target_path = (doc_dir / link_target).resolve()
                if not target_path.exists():
                    # Check repo-root relative
                    target_path_root = (REPO_ROOT / link_target.lstrip("/")).resolve()
                    if not target_path_root.exists():
                        dead_links.append({
                            "doc": rel_path,
                            "line": line_idx,
                            "section": current_section,
                            "link_text": link_text,
                            "link_target": link_target
                        })

    return claims, dead_links

if __name__ == "__main__":
    claims, dead_links = scan_markdown_files()
    output = {
        "total_claims_audited": len(claims),
        "claims": claims,
        "dead_links_count": len(dead_links),
        "dead_links": dead_links
    }
    out_path = REPO_ROOT / "evaluation/docs_unification/claim_ledger.json"
    out_path.write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(f"Audited {len(claims)} claims and {len(dead_links)} links across {len(DOC_FILES)} documents.")
    print(f"Results written to {out_path}")
