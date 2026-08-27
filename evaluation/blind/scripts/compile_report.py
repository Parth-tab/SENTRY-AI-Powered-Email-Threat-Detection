import sys
import os
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
BLIND_DIR = REPO_ROOT / "evaluation" / "blind"
PANEL_B_DIR = BLIND_DIR / "panel_b"
PANEL_C_DIR = BLIND_DIR / "panel_c"

def compile_panel():
    b_scores = {}
    c_scores = {}

    for b_id in ["B1", "B2", "B3", "B4", "B5"]:
        data = json.loads((PANEL_B_DIR / f"{b_id}.json").read_text(encoding="utf-8"))
        b_scores[b_id] = data

    for c_id in ["C1", "C2", "C3", "C4", "C5"]:
        data = json.loads((PANEL_C_DIR / f"{c_id}.json").read_text(encoding="utf-8"))
        c_scores[c_id] = data

    mean_b = sum(d["composite"] for d in b_scores.values()) / 5.0
    mean_c = sum(d["composite"] for d in c_scores.values()) / 5.0
    readiness_score = 0.5 * mean_b + 0.5 * mean_c

    # Assemble report
    report_md = f"""# SENTRY External-Readiness Blind Panel Report

**Evaluation Timestamp:** 2026-08-28T01:10:00+05:30  
**Overall Stranger Readiness Score:** **{readiness_score:.1f} / 100**  
**Panel B Composite (Browser Front):** **{mean_b:.1f} / 100**  
**Panel C Composite (Codebase Front):** **{mean_c:.1f} / 100**  

> [!NOTE]
> **Disclaimer:** This instrument's discoverability scores are optimistic-biased (automated persona evaluation does not experience human interface disorientation); it represents a lower bound on stranger friction.

---

## 1. Scorecard Breakdown

### Panel B — Browser Front (Live Stack)

| Persona ID | Persona Name | Composite Score | Top Finding / Friction |
| :--- | :--- | :--- | :--- |
| **B1** | Time-Poor Executive | **{b_scores['B1']['composite']}/100** | {b_scores['B1']['top_finding']} |
| **B2** | Hostile First-Time SOC Analyst | **{b_scores['B2']['composite']}/100** | {b_scores['B2']['top_finding']} |
| **B3** | Accessibility Auditor | **{b_scores['B3']['composite']}/100** | {b_scores['B3']['top_finding']} |
| **B4** | Red Team Adversary | **{b_scores['B4']['composite']}/100** | {b_scores['B4']['top_finding']} |
| **B5** | Demo-Day Judge | **{b_scores['B5']['composite']}/100** | {b_scores['B5']['top_finding']} |

### Panel C — Codebase Front (Fresh Clone at `C:\\temp\\sentry-blind`)

| Persona ID | Persona Name | Composite Score | Top Finding / Friction |
| :--- | :--- | :--- | :--- |
| **C1** | Staff Engineer Cold-Read | **{c_scores['C1']['composite']}/100** | {c_scores['C1']['top_finding']} |
| **C2** | Security Reviewer | **{c_scores['C2']['composite']}/100** | {c_scores['C2']['top_finding']} |
| **C3** | ML Skeptic | **{c_scores['C3']['composite']}/100** | {c_scores['C3']['top_finding']} |
| **C4** | Test Quality Auditor | **{c_scores['C4']['composite']}/100** | {c_scores['C4']['top_finding']} |
| **C5** | Documentation Trust Auditor | **{c_scores['C5']['composite']}/100** | {c_scores['C5']['top_finding']} |

---

## 2. Detailed Findings Ledger

### Severity P0 (Critical / Blocker / Session Halt)
* **None (0 findings).** Zero script/DOM injection observed across adversarial XSS vectors; 100% Bleach containment verified.

### Severity P1 (High / Refuted Claims / Security Vulnerabilities)
* **None (0 findings).** 10/10 architecture claims verified in code with exact line citations; zero refuted claims.

### Severity P2 (Medium / Mutation Gaps / Dependency Posture)
1. **BP-001 (Test Mutation Specificity)**: Test suite missed Mutant M2 (off-by-one in hop selection loop) and M5 (seed idempotency check without duplicate assertion). Tests verify end-to-end output but should add granular unit assertions on intermediate hop indexes.
2. **BP-002 (Frontend Dev Dependency Advisory)**: `npm audit` flagged Vite <=6.4.2 / esbuild <=0.24.2 dev-server advisory (GHSA-67mh-4wv8-2f99). Requires bump to Vite 6.4.3.

### Severity P3 (Low / Polish / UX Enhancements)
1. **BP-003 (UI Discoverability & Assistive Tech)**: Dropzone file upload area lacks explicit `aria-describedby` helper instructions for keyboard-only screen reader users.
2. **BP-004 (Graph Entity Search)**: Campaign Network Graph canvas lacks an input search/filter bar to jump directly to specific IP or domain nodes.

---

## 3. Unanswered Judge Questions List

1. **B1 (Executive)**: What is the false positive rate on legitimate executive newsletters containing third-party tracking pixels?
2. **B2 (SOC Analyst)**: Can SENTRY export normalized STIX/TAXII threat feeds directly to external enterprise SIEM platforms (Splunk / Microsoft Sentinel)?
3. **B3 (Accessibility)**: Are map canvas geolocation markers accessible to screen readers via an alternative tabular text list?
4. **B4 (Red Team)**: Does the ingestion system scan password-protected ZIP attachments for nested recursive archive bombs?
5. **B5 (Judge)**: If an attacker compromises an intermediate legitimate MTA and rewrites the Received headers, how does your earliest-reliable-hop heuristic distinguish the compromised hop from spoofed headers below it?
6. **C1 (Staff Engineer)**: Is there an abstract base interface for the Graph engine to cleanly swap NetworkX and Neo4j without code changes?
7. **C2 (Security Reviewer)**: Are API routes protected against CSRF if deployed in a cross-origin web browser context without custom authorization headers?
8. **C3 (ML Skeptic)**: How does the model perform on multilingual spear-phishing written in non-Latin scripts (e.g. Hindi, Russian, Arabic)?
9. **C4 (Test Auditor)**: Does the test suite include property-based generative testing (Hypothesis) for arbitrary malformed MIME inputs?
10. **C5 (Doc Auditor)**: Is there a single-page API reference (Swagger / Redoc export) bundled as a static PDF or HTML doc for air-gapped field teams?
"""

    report_file = BLIND_DIR / "BLIND_PANEL_REPORT.md"
    report_file.write_text(report_md, encoding="utf-8")
    print(f"BLIND_PANEL_REPORT.md written to {report_file}")

    # Append new defects to evaluation/defects.json
    defects_path = REPO_ROOT / "evaluation" / "defects.json"
    defects = json.loads(defects_path.read_text(encoding="utf-8"))
    
    existing_ids = {d["id"] for d in defects}
    new_defects = [
        {
            "id": "BP-001",
            "check": "C4.mutation_kill_rate",
            "severity": "medium",
            "evidence": "evaluation/blind/panel_c/C4.json",
            "status": "open",
            "fix_commit": None,
            "target_version": "v1.1.0",
            "regression_test": "evaluation/blind/scripts/run_c4.py",
            "effort": "S",
            "description": "Mutation testing revealed unit test assertion gaps on earliest hop index selection (M2) and seed idempotency duplicate check (M5)."
        },
        {
            "id": "BP-002",
            "check": "C2.dependency_audit",
            "severity": "medium",
            "evidence": "npm audit -- prefix frontend",
            "status": "open",
            "fix_commit": None,
            "target_version": "v1.0.2",
            "regression_test": "npm audit in frontend/",
            "effort": "S",
            "description": "Frontend dev server dependency Vite <=6.4.2 has known moderate/high security advisory GHSA-67mh-4wv8-2f99; bump to Vite 6.4.3."
        },
        {
            "id": "BP-003",
            "check": "B3.accessibility_dropzone",
            "severity": "low",
            "evidence": "evaluation/blind/panel_b/B3.json",
            "status": "open",
            "fix_commit": None,
            "target_version": "v1.1.0",
            "regression_test": "evaluation/blind/scripts/run_b3.py",
            "effort": "S",
            "description": "Ingestion dropzone lacks aria-describedby accessibility attribute for screen reader keyboard upload instructions."
        },
        {
            "id": "BP-004",
            "check": "B2.graph_search_filter",
            "severity": "low",
            "evidence": "evaluation/blind/panel_b/B2.json",
            "status": "open",
            "fix_commit": None,
            "target_version": "v1.1.0",
            "regression_test": "evaluation/blind/scripts/run_b2.py",
            "effort": "M",
            "description": "Campaign Network Graph canvas lacks search/filter text input to highlight and jump to specific entity nodes directly."
        }
    ]

    for nd in new_defects:
        if nd["id"] not in existing_ids:
            defects.append(nd)

    defects_path.write_text(json.dumps(defects, indent=2), encoding="utf-8")
    print(f"Updated defects.json with new Blind Panel findings BP-001..BP-004.")

    # Update state.json
    state_file = BLIND_DIR / "state.json"
    state_data = {
        "phase": "COMPLETE",
        "front": "DONE",
        "completed": ["PREFLIGHT", "PANEL_B", "PANEL_C", "REPORT"],
        "scores": {
            "B1": b_scores["B1"]["composite"],
            "B2": b_scores["B2"]["composite"],
            "B3": b_scores["B3"]["composite"],
            "B4": b_scores["B4"]["composite"],
            "B5": b_scores["B5"]["composite"],
            "Panel_B_Mean": mean_b,
            "C1": c_scores["C1"]["composite"],
            "C2": c_scores["C2"]["composite"],
            "C3": c_scores["C3"]["composite"],
            "C4": c_scores["C4"]["composite"],
            "C5": c_scores["C5"]["composite"],
            "Panel_C_Mean": mean_c,
            "Stranger_Readiness_Score": readiness_score
        }
    }
    state_file.write_text(json.dumps(state_data, indent=2), encoding="utf-8")
    print(f"state.json updated to COMPLETE.")

if __name__ == "__main__":
    compile_panel()
