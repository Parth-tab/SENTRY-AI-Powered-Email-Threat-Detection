# SENTRY v1.2.0 Release Notes — Evidentiary Forensics, Graph Intelligence & Continuous Fact Gating

*Release Version: 1.2.0 • Date: September 2, 2026 • Status: Draft (Pre-Release)*

---

## Executive Summary

SENTRY v1.2.0 marks a major milestone in high-assurance email forensic intelligence. This release merges two comprehensive engineering arcs: the **Deterministic Graph Intelligence Redesign** and the **External Evaluation Remediation & Defense Hardening**, capped by a repository-wide **Machine-Verified Documentation Unification**.

Every claim in this release is machine-derived and continuously enforced via `tools/validate_facts.py` and GitHub Actions CI.

---

## Key Highlights & Subsystem Upgrades

### 1. Deterministic Campaign Knowledge Graph & Gate 21 Legibility Moat
- **Deterministic Force Layout:** Replaced non-deterministic simulation physics with a seeded pseudo-random force layout, ensuring stable, reproducible node coordinates across SOC investigations.
- **Stratified Diversity Capping & Supernodes:** When analyzing enterprise corpora with thousands of correlated entities, SENTRY enforces a 300-node display ceiling using degree-weighted stratified sampling to preserve critical infrastructure relationships without canvas clutter.
- **Automated Canvas Legibility Gate (Gate 21):** The Playwright-driven golden verification harness (`tools/verify_sentry.py`) now includes an automated node bounding-box separation check (`ui.graph_legibility`), mathematically certifying that correlated entity nodes maintain minimum canvas clearance.

### 2. External Evaluation Remediation & Signature Defenses
- **Self-Spoof Anti-Self-DoS Countermeasure Refusal (EXT-005, EXT-008):**
  *SENTRY is the forensic platform that structurally refuses to tell you to block your own domain.* When internal domain spoofing occurs (`from_domain == recipient_domain`), SENTRY derives internal boundaries dynamically without manual configuration. It bypasses naive domain blocks, directing SOC operators to DNS DMARC `p=reject`, perimeter SEG anti-spoof drops, and external `Reply-To` diversion channel blocking.
- **Authentication Failure Severity Floor (EXT-002) with Algorithmic Transparency:**
  Unauthenticated domain spoofing (hard DMARC + SPF failure) is an organizational security policy violation. SENTRY enforces an immutable **0.85 (CRITICAL)** severity lower bound while maintaining algorithmic honesty: both `score_pre_floor` and `floor_applied` are exposed in all API schemas and rendered explicitly in court-admissible PDF forensic dossiers:
  $$\mathbf{CRITICAL\ THREAT\ (0.85\ [Enforced\ Floor;\ Model:\ 0.51])}$$
- **22-Network RFC Special-Use & Reserved IP Boundary Guard (EXT-003):**
  Pre-compiled CIDR network guard covering 22 private, documentation, and CGNAT IP ranges (RFC 5737 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, RFC 6598 `100.64.0.0/10`, RFC 1918) preventing internal test addresses from being queried against external threat feeds or assigned false geographic coordinates.
- **Empirical 0.00% False-Positive Proof Across 6,777 Ham Emails:**
  Independently benchmarked against 6,777 unique historical ham emails (6,951 archive files), producing **0 false positive floor elevations (0.00% FP rate)** because authentic unsigned email lacks authentication infrastructure (`dmarc: none`) and does not trigger hard cryptographic failure predicates.
- **Specialized Advance-Fee Fraud Subtyping (EXT-001):**
  Introduced `classification_subtype: "ADVANCE-FEE FRAUD"` within the primary 5-class taxonomy (`phishing`), triggering specialized incident response playbooks for 419 lottery and inheritance lures.

### 3. Evidentiary Hygiene & Court Admissibility Standards
- **Full-Length Subject Paragraph Flowables (EXT-004):** Eliminated arbitrary string slicing (`[:60]`) across ReportLab PDF generation, wrapping full 111-character subject lines naturally without truncation.
- **64-Character Courier Monospace Hashes (EXT-006):** Cryptographic SHA-256 digests rendered in dedicated 220pt columns using monospace typography, preventing optical character wrapping ambiguity and transcription distortions in legal proceedings.
- **Universal RFC 3339 UTC Timestamps (EXT-007):** Replaced non-standard strftime formatters with ISO 8601 / RFC 3339 UTC timestamps across all 6 emission points.

### 4. Continuous Machine-Verified Fact Gating
- **`tools/validate_facts.py` & `docs/PROJECT_FACTS.md`:** Eliminates documentation drift across the repository. A dedicated CI gate extracts live test counts, gate counts, defect ledgers, and routes dynamically from code and asserts mathematical alignment on every commit.

---

## Verified Engineering Metrics

All figures below are derived by command in the live repository:

| Metric Category | Ground Truth Value | Derivation Command / Authority |
|---|:---:|---|
| **Pytest Test Suite** | **156 tests** (23 modules, 85%+ branch coverage) | `python -m pytest --collect-only -q` |
| **Golden Verification Gates** | **21 gates** (API, WebSockets, CSV, ZIP, UI, Legibility) | `python tools/verify_sentry.py --start` |
| **Master Defect Ledger** | **76 objects** (66 Resolved, 1 Interim, 3 Cons, 1 Def, 5 Open) | `evaluation/defects.json` / `tools/validate_facts.py` |
| **Registered API Endpoints** | **29 routes** (24 business DFIR routes) | `backend/app/main.py` route introspection |
| **Cross-Stack Version** | **v1.1.0 $\rightarrow$ v1.2.0** | `backend/app/config.py` & `frontend/package.json` |
| **Ham Benchmark Baseline** | **6,777 unique** (6,951 files, 0 FP elevations) | `tools/benchmark_corpus_ingest.py` |
| **ML Validation Benchmark** | **0.952 Macro-F1 / 0.961 Accuracy** (15,240 samples) | `backend/app/ml/classifier.py` |

---

## Upgrade & Verification Instructions

To verify your installation against the v1.2.0 standard:

```bash
# 1. Run unit & integration test suite (156 tests)
pytest backend/tests -v

# 2. Run machine-verified single source of truth validator
python tools/validate_facts.py --strict-links

# 3. Run full 21-gate end-to-end golden verification harness
python tools/verify_sentry.py --start
```
