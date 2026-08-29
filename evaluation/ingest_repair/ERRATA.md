# SENTRY Evaluation Errata: Ingest Repair & Harness State

## 1. Explanation of the 39-Item Count in Prior Verification Logs

In earlier test iterations prior to `ING-003`, the verification harness ran against the shared live database (`backend/sentry.db`) rather than an isolated harness scratch DB. Because write-path endpoints lacked strict SHA-256 byte deduplication during initial diagnosis and benchmark runs, repeated runs accumulated items:
- **18 Seed Baseline:** The standard 18 curated demo emails seeded via `/api/v1/samples/seed`.
- **19 Pre-Dedupe Test Artifacts:** Ingested during initial diagnosis (`diagnose_ingest.py`), manual triage testing, and exploratory test uploads before SHA-256 dedupe was wired into general write-paths.
- **2 Probe Artifacts:** Upload and paste verification items ingested during subsequent gate executions.

Totaling **39 rows** accumulated in the persistent `backend/sentry.db`.

### Permanent Resolution in `ING-003`:
1. **Isolated Harness Scratch World:** `tools/verify_sentry.py` now runs backend tests against `evaluation/harness_scratch.db`, which is unlinked prior to backend boot.
2. **Untouched Live Appliance DB:** The live appliance database (`backend/sentry.db`) is never modified or polluted by automated verification suites.
3. **Exact Invariant Enforcement:** `api.emails_list` asserts exactly 18 items on fresh scratch boot, and Gates 16/17 assert $+1$ and $+2$ item count deltas alongside unique probe subjects (`HARNESS-PROBE-GATE16-UPLOAD` and `HARNESS-PROBE-GATE17-PASTE`).
