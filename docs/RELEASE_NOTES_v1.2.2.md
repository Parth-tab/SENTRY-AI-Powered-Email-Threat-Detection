# SENTRY v1.2.2 Release Notes — Master Verification, Deep Forensics & Provenance Reunification

*Release Version: 1.2.2 • Date: September 2, 2026 • Status: Certified Release*

---

## Executive Summary

SENTRY v1.2.2 delivers a critical high-assurance release that reunifies published container artifacts with the master email verification arc. Following the rapid sequence of v1.2.0 (Graph Redesign) and v1.2.1 (External Evaluation Remediation & Documentation Unification), v1.2.2 resolves two composition defects identified during deep multi-hop Received chain stress-testing, establishes an automated CI gate for version legitimacy, and permanently synchronizes published container artifacts with codebase truth.

Every claim in this release is machine-derived and continuously enforced via `tools/validate_facts.py --strict-links` in GitHub Actions CI.

---

## Provenance Reconciliation Rider (MV-C-1 & MV-C-2)

To maintain absolute evidentiary clarity and auditability across release tags and container registries, this release explicitly reconciles the tag and artifact lineage:

| Version Tag | Release Commit SHA | Published GHCR Artifacts | Delivered Scope & Audit Context |
|---|:---:|---|---|
| **v1.2.0** | `4a60a9b` | *Internal Release* | Deterministic Campaign Knowledge Graph, seeded force physics, stratified 300-node diversity cap, Gate 21 canvas legibility moat (PR #13). |
| **v1.2.1** | `ac32a9c` (tag peel `9b9f02e`) | `ghcr.io/parth-tab/sentry-backend:1.2.1`<br>`ghcr.io/parth-tab/sentry-frontend:1.2.1` | External Evaluation Remediation (`EXT-001..009`), Documentation Unification (`DOC-001..005`), fact validator, and route aggregation fix (`2afba8d`). Published prior to master email composition testing. |
| **v1.2.2** | Final Merge HEAD | `ghcr.io/parth-tab/sentry-backend:1.2.2`<br>`ghcr.io/parth-tab/sentry-frontend:1.2.2` | **Reunified Release Artifact:** DEF-A deep Received chain hop selection, DEF-B complete 4-row IOC table rendering, master email regression suite, and Stage 5 git tag legitimacy gate. |

---

## Key Highlights & Subsystem Upgrades

### 1. Earliest Reliable Hop Selection in Deep Received Chains (DEF-A)
- **Problem Statement:** In deep multi-hop email chains containing simulated public test infrastructure (e.g. RFC 5737 `203.0.113.9` at hop 2) and local relay hops (`127.0.0.1` at hop 1), the previous hop selector classified TEST-NET addresses as reserved and terminated hop scanning prematurely. This caused fallback to `127.0.0.1` as the "probable origin" and erroneously placed loopback on firewall drop lists.
- **Permanent Solution:** Re-engineered the selection loop in `backend/app/services/header_forensics.py`:
  - Iterates Received hops chronologically from oldest (probable boundary relay) to newest.
  - Prioritizes true externally-routable public IPs; if all hops are special-use/private, it prioritizes simulated documentation test networks (`203.0.113.0/24`, `198.51.100.0/24`, `192.0.2.0/24`) over transit private relays.
  - Never selects loopback (`127.0.0.1`) if any other hop exists in the chain.
  - Enforced low-confidence origin labeling (`Reserved / Internal Test IP`) and hardened `backend/app/ml/classifier.py` so firewall drop lists structurally refuse RFC-reserved addresses.

### 2. Complete IOC Table Rendering on Forensic Report Path (DEF-B)
- **Problem Statement:** The forensic report endpoint (`/emails/{email_id}/report`) projected a minimal dictionary for PDF generation that omitted `headers`, `raw_headers`, and `sender_domain`. This prevented Reply-To anomaly detection from evaluating during report rendering, dropping `Reply-To Email` and `Reply-To Domain` rows from the IOC table (rendering only 2 rows instead of 4).
- **Permanent Solution:** Updated `backend/app/api/v1/emails.py:download_pdf_report` to propagate full header context and sender domain metadata. Added case-insensitive header fallback in `backend/app/services/reporting.py`, ensuring all 4 IOC rows render deterministically in court-admissible PDF forensic dossiers and API responses.

### 3. Automated Version Legitimacy Gate (MV-1)
- **CI Gate Enforcement:** Upgraded `tools/validate_facts.py` Stage 5 to interrogate repository git tags dynamically. It asserts that declared software version equals the highest release tag in git history:
  $$\mathbf{APP\_VERSION} = \max(\{\text{git release tags}\})$$
- **Mutation Kill Defense:** Codified in `backend/tests/test_version_legitimacy.py` with 3 automated tests proving that bumping software versions without a corresponding git tag fails CI with an explicit, named error message naming the unbacked version.

### 4. Master Email Verification & Negative Control Test Battery
- Added `backend/tests/fixtures/advance_fee_master_verification.eml` exercising deep Received chains and Reply-To mismatch.
- Added `backend/tests/fixtures/newsletter_negative_control.eml` verifying that legitimate newsletters with "prize" phrasing are not falsely elevated by the severity floor (scoring 0.07 LOW).
- Integrated 5 new regression and mutation tests (`backend/tests/test_master_verification_email.py`).

---

## Verified Engineering Metrics

All figures below are derived by command in the live repository:

| Metric Category | Ground Truth Value | Derivation Command / Authority |
|---|:---:|---|
| **Pytest Test Suite** | **164 tests** (24 modules, 85%+ branch coverage) | `python -m pytest --collect-only -q` |
| **Golden Verification Gates** | **21 gates** (API, WebSockets, CSV, ZIP, UI, Legibility) | `python tools/verify_sentry.py --start` |
| **Master Defect Ledger** | **78 objects** (68 Resolved, 1 Interim, 3 Cons, 1 Def, 5 Open) | `evaluation/defects.json` / `tools/validate_facts.py` |
| **Registered API Endpoints** | **29 routes** (24 business DFIR routes) | `backend/app/main.py` route introspection |
| **Cross-Stack Version** | **v1.2.2** | `backend/app/config.py` & `frontend/package.json` |
| **Ham Benchmark Baseline** | **6,777 unique** (6,951 files, 0 FP elevations) | `tools/benchmark_corpus_ingest.py` |
| **ML Validation Benchmark** | **0.952 Macro-F1 / 0.961 Accuracy** (15,240 samples) | `backend/app/ml/classifier.py` |

---

## Upgrade & Verification Instructions

To verify your installation against the v1.2.2 standard:

```bash
# 1. Run unit & integration test suite (164 tests)
pytest backend/tests -v

# 2. Run machine-verified single source of truth validator
python tools/validate_facts.py --strict-links

# 3. Run full end-to-end golden verification harness (21 gates)
python tools/verify_sentry.py --start
```
