# SENTRY — Single Machine-Verified Source of Truth (`PROJECT_FACTS.md`)

<!--
SENTRY MASTER FACTS SPECIFICATION
This document is the sole machine-verified source of truth for all quantitative
and architectural claims across the repository.
It is validated in CI via: python tools/validate_facts.py
Every quantitative fact carries a derivation comment and classification tag:
  [derived]            : Recomputed dynamically by validate_facts.py from live code/tests
  [derived-historical] : Cryptographically / empirically verified against immutable receipts
  [asserted]           : Architectural invariant, positioning, or operational policy
-->

## 1. Machine-Derivable Live Engineering Metrics

The following metrics are dynamically extracted and validated by `tools/validate_facts.py`:

<!-- fact: TEST_SUITE_COUNT -->
<!-- derivation: python -m pytest --collect-only -q -->
- **Test Suite Count [derived]:** `TEST_SUITE_COUNT: 156` passing unit and integration tests across 23 modules (`backend/tests`).

<!-- fact: GOLDEN_GATES_COUNT -->
<!-- derivation: python tools/verify_sentry.py --start -->
- **Golden Verification Gates [derived]:** `GOLDEN_GATES_COUNT: 21` end-to-end gates (API, UI, WebSocket, CSV, ZIP, graph legibility, single-origin production mode).

<!-- fact: DEFECT_TOTAL_COUNT -->
<!-- derivation: python -c "import json; len(json.load(open('evaluation/defects.json')))" -->
- **Master Defect Ledger Total [derived]:** `DEFECT_TOTAL_COUNT: 76` tracked defect and gap objects across repository history.

<!-- fact: DEFECT_RESOLVED_COUNT -->
<!-- derivation: python -c "import json; len([x for x in json.load(open('evaluation/defects.json')) if x.get('status')=='resolved'])" -->
- **Resolved Defects [derived]:** `DEFECT_RESOLVED_COUNT: 66` fully resolved and test-guarded defect objects.

<!-- fact: DEFECT_STATUS_BREAKDOWN -->
<!-- derivation: 66 resolved + 1 interim + 3 consolidated + 1 deferred + 5 open = 76 -->
- **Defect Ledger Breakdown [derived]:**
  - **Resolved:** 66 (43 core + 7 MRWS + 4 CI + 4 Graph + 8 EXT)
  - **Interim Mitigated:** 1 (`GAP-005` trademark notice)
  - **Consolidated:** 3 (`BATCH-003`, `CORP-002`, `ING-003`)
  - **Deferred:** 1 (`BP-005` v1.3.0 server-side graph expand)
  - **Open (Targeted Roadmap):** 5 (`DEF-005` forged-header battery, `MBOX-001` mbox delimiter parser, `GAP-001` scale-out daemons, `GAP-002` automated IMAP/M365 mailbox connector, `EXT-009` synthetic attribution label)
  - **Sum Invariant:** $66 + 1 + 3 + 1 + 5 = 76$ (100% mathematically reconciled).

<!-- fact: APP_VERSION -->
<!-- derivation: backend/app/config.py (VERSION) == frontend/package.json (version) -->
- **Unified Software Version [derived]:** `APP_VERSION: 1.1.0` (Workstation certified delivery; v1.2.0 graph engine & ext-eval remediation prepared for release).

<!-- fact: FASTAPI_ROUTES_COUNT -->
<!-- derivation: python -c "from app.main import app; len([r for r in app.routes if hasattr(r, 'methods')])" -->
- **Registered Application Routes [derived]:** `FASTAPI_ROUTES_COUNT: 29` routes (24 business API routes under `/api/v1/`, `/health`, `/metrics` + 5 system documentation routes).

<!-- fact: FEATURE_VECTOR_DIMENSIONS -->
<!-- derivation: backend/app/ml/classifier.py (len(FeatureExtractor.FEATURE_NAMES)) -->
- **ML Feature Vector Dimensions [derived]:** `FEATURE_VECTOR_DIMENSIONS: 47` tabular header, content, network, and entropy dimensions.

<!-- fact: DEMO_CORPUS_COUNTS -->
<!-- derivation: backend/app/api/v1/stats.py (len(DEMO_EMAILS)) -->
- **Demonstration Corpus Composition [derived]:** `DEMO_EMAILS_COUNT: 18` synthetic emails spanning `DEMO_CAMPAIGNS_COUNT: 3` attack campaigns.
- **Demo Threat Distribution [derived]:** 15 CRITICAL, 1 MEDIUM, 2 LOW (governed by 0.85 DMARC spoofing severity floor).

---

## 2. Immutable Benchmark & Evaluation Receipts

The following metrics are anchored in historical evaluation runs and cryptographic verification reports:

<!-- fact: HAM_BENCHMARK_RECEIPTS -->
<!-- receipt: evaluation/runs/ham_test/ham_test_summary.json -->
- **Ham Corpus False-Positive Benchmark [derived-historical]:**
  - `HAM_UNIQUE_COUNT: 6777` unique historical ham email digests (from `HAM_ARCHIVE_COUNT: 6951` archive files).
  - `HAM_FP_ELEVATIONS: 0` false positive severity floor elevations (**0.00% FP rate**).
  - *Mechanism:* Authenticated legitimate and unsigned mail evaluate to `dmarc: none` / `spf: none`, which does not trigger the hard cryptographic failure floor (`dmarc: fail` + `spf: fail/softfail`).

<!-- fact: ML_BENCHMARK_METRICS -->
<!-- receipt: evaluation/final_report.md & evaluation/runs/iter_3/evidence/ -->
- **Threat Classification Performance [derived-historical]:**
  - **Macro-F1 Score:** `0.952` (synthetic/augmented multi-class validation corpus).
  - **Accuracy (Macro OvR):** `0.961` (15,240 validation samples).
  - **ROC-AUC (Macro OvR):** `0.988`.
  - **Adversarial Evasion Resilience:** 9/10 evasions detected (zero-width spaces, Unicode homoglyphs, IDN punycode, RTLO).

<!-- fact: GAUNTLET_AUDIT_COMPOSITE -->
<!-- receipt: evaluation/final_report.md -->
- **GAUNTLET 12-Dimension Score [derived-historical]:** `97.5 / 100` composite score adjusted under hostile audit.

---

## 3. Strategic & Architectural Assertions

The following operational policies govern SENTRY's system architecture:

- **Single Air-Gapped Appliance Topology [asserted]:** SENTRY runs completely self-contained on a single workstation (asynchronous SQLite via `aiosqlite` + in-memory NetworkX graph). No external daemons (Redis, Celery, PostgreSQL, Neo4j) are active in the live path.
- **One Port Policy [asserted]:** Backend binds strictly to port `8000`, Frontend dev binds strictly to port `3000`. In production mode, FastAPI serves the pre-compiled SPA statically on port `8000`.
- **Self-Spoof Anti-Self-DoS Invariant [asserted]:** When `from_domain == recipient_domain` with failed authentication, SENTRY structurally refuses to recommend blocking the internal domain, routing countermeasures instead to DNS DMARC `p=reject`, perimeter SEG anti-spoof drops, and blocking external Reply-To channels.
- **Severity Floor Transparency Invariant [asserted]:** When the 0.85 authentication floor elevates an ML score, SENTRY preserves and displays both the floor and the underlying model score (`score_pre_floor`) in schemas and PDF forensic dossiers (`"0.85 [Enforced Floor; Model: 0.51]"`).
- **Target Addressable Market (TAM) Calibration [asserted]:** SENTRY targets the specialized DFIR Incident Response & State Cyber Crime Investigation Unit niche (~6,000 global units $\times$ $2,000–$3,000/license = $12M–$18M TAM).
