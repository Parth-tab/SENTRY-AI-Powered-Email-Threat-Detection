# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [1.2.1] - 2026-09-02

### Added
- **Fraud Subtype Classification Layer (`EXT-001`):** Added specialized advance-fee fraud subtyping (`classification_subtype: "ADVANCE-FEE FRAUD"`) within the primary 5-class taxonomy, triggering dedicated Nigerian 419 / advance-fee incident response playbooks.
- **22-Network RFC Special-Use & Reserved IP Boundary Guard (`EXT-003`):** Pre-compiled CIDR subnet boundary guarding 22 private, documentation, and CGNAT IP ranges (RFC 5737 `192.0.2.0/24`, `198.51.100.0/24`, `203.0.113.0/24`, RFC 6598 `100.64.0.0/10`, RFC 1918) against external geolocation leakage or false infrastructure attribution.
- **Machine-Verified Fact & Link Validator (`DOC-005`):** Created `tools/validate_facts.py` and `docs/PROJECT_FACTS.md` providing dynamic zero-constant verification of test suite counts (156 tests across 23 modules), golden gates (21 gates), master defect ledgers (76 objects), route counts (29 endpoints), cross-stack version uniformity, and repository link integrity with CI gating.

### Fixed
- **Full-Length Subject Flowables in Forensic PDF Dossiers (`EXT-004`):** Eliminated silent string slicing (`[:60]`) across ReportLab PDF generation, replacing it with wrapping Paragraph flowables preserving complete 111-character subject lines.
- **Evidentiary Hash Formatting & Monospace Typography (`EXT-006`):** Dedicated 220pt column allocation in Courier monospace font preventing optical character wrapping ambiguity and transcription distortions in legal proceedings.
- **Universal RFC 3339 UTC Timestamps (`EXT-007`):** Replaced non-standard strftime formatters with ISO 8601 / RFC 3339 UTC timestamps across all 6 emission points.
- **Case-Insensitive Header Forensics Anomaly Detection:** Normalized SMTP header dictionary keys to lowercase preventing case-sensitivity bypasses on synthetic or adversarial headers.

### Security
- **Incident Response Self-Spoof Anti-Self-DoS Refusal (`EXT-005`, `EXT-008`):** Dynamically identifies internal domain spoofing (`from_domain == recipient_domain`) without manual configuration and structurally refuses to recommend blocking the organization's own domain, directing countermeasures to DNS DMARC `p=reject`, perimeter SEG anti-spoof drops, and external `Reply-To` channel blocks.
- **Deterministic 0.85 Authentication Failure Severity Floor (`EXT-002`):** Enforces an immutable 0.85 (CRITICAL) severity floor on hard DMARC+SPF cryptographic authentication failure while preserving algorithmic transparency via `score_pre_floor` in schemas and PDF forensic dossiers.
- **Empirical Ham Corpus Baseline Receipt:** Stress-tested across 6,777 unique historical ham emails (6,951 files) with 0 false positive elevations (0.00% FP rate).

### Changed
- **Defect Ledger Unification (`DOC-001`):** Integrated external evaluation items (`EXT-001..009`) into master registry (`evaluation/defects.json`), reconciling arithmetic to 76 total items (66 resolved, 1 interim mitigated, 3 consolidated, 1 deferred, 5 open).
- **Documentation Unification:** Synchronized all public documentation, PR templates, and QA armor with machine-verified facts from `docs/PROJECT_FACTS.md`.

## [1.2.0] - 2026-08-30

### Added
- **Deterministic Campaign Knowledge Graph & Gate 21 Legibility Verification (`GRAPH-003`, `GRAPH-004`, `GRAPH-005`, `BP-004`):** Upgraded campaign network graph with deterministic pseudo-random force simulation layout, stratified degree-weighted sampling cap (300 nodes), supernode clustering, and automated canvas node bounding-box separation legibility check in golden harness (`Gate 21`).

## [1.1.0] - 2026-08-30

### Added
- **Database Schema Migration Framework (D5 / GAP-009):** Integrated Alembic migrations with baseline schema revision (`0001_initial_schema`), dynamic database URL detection, batch rendering, and automated upgrade/downgrade lifecycle testing.
- **Evidentiary Hot Backup & Restore Subsystem (D6 / GAP-010):** Implemented atomic hot snapshot tooling (`BackupService`, `tools/backup_vault.py`, `tools/restore_vault.py`) utilizing SQLite online backup and archive manifests with mathematical post-restore RFC 3227 hash-chain verification.
- **Enterprise Log Rotation:** Configured `RotatingFileHandler` with 10MB threshold and 5 backup generations for structured access and error logs.
- **Enterprise Operations Runbook:** Published [`docs/RUNBOOK.md`](docs/RUNBOOK.md) documenting backup automation schedules, disaster recovery restore drills, migration procedures, and disk quota monitoring.
- **Corpus Sanitization & Trademark De-risking (D4 / GAP-004):** Completely rewritten all 18 fixture EMLs in `sample_emails/` and test suites to fictional "Apex National Bank" archetype (`Apex National Bank`, `Apex Commercial Bank`, `apex-secureverify.com`, `onlineapex-kyc-update.com`, `apex-netbanking-alert.xyz`), eliminating all real Indian bank trademarks (SBI, HDFC, ICICI, RBI) across code, fixtures, and docs.
- **Guided Tour Screenshot Recapture:** Re-captured all 8 tour screenshots against the authenticated, production-built UI and updated `FEATURE_TOUR.md` with verified caption alignment under the Caption Honesty Law.
- **Modernized Datetime & Schema Hygiene:** Migrated all Pydantic schemas to `ConfigDict` / `SettingsConfigDict` and modernized timestamp handlers to timezone-aware UTC, slashing test suite deprecation warnings by 99%.
- **DFIR Operator Bearer Token Authentication (D2 / GAP-006):** Secured all 8 writable forensic endpoints (`/upload`, `/batch/archive`, `/batch/csv`, `/batch/upload`, `/raw`, `/samples/seed`, `/evidence/verify/{email_id}`, `/admin/reset-demo`) behind constant-time `SENTRY_API_TOKEN` Bearer authentication with HTTP 401 envelope.
- **Frontend DFIR Operator Auth UI:** Added `AuthModal` component for operator token authentication and session locking, automated HTTP 401 interception, and reactive authentication status management.
- **Security Test Matrix (`test_auth_surface.py`):** Comprehensive automated test coverage validating 401 rejection for missing and forged tokens across all writable routes, plus verification of unauthenticated read telemetry access.
- **Single-Origin Production Serving (D1 / GAP-003):** FastAPI dynamic static mount for pre-compiled React/Vite SPA bundle (`frontend/dist`), eliminating dual-process requirements and CORS barriers in production.
- **Enterprise On-Premises Deployment Guide:** Added [`DEPLOYMENT.md`](DEPLOYMENT.md) covering build instructions, environment variables, port topology, persistent storage paths, and atomic backup procedures.
- **Gate 20 Harness Verification (`ui.production_mode_e2e`):** Extended golden verification battery to 20 gates with end-to-end single-origin serving and unauthenticated writable probe 401 rejection assertions.
- **Auditor's Annex & Errata (Phase 0):** Formalized viability audit corrections, SY-1 scale-out analysis errata, memory profiling notes, and market math reconciliations.
- **MaxMind GeoLite2 EULA Attribution:** Explicit attribution notice and direct links on UI footer, PDF dossiers, and README.
- **Trademark & Brand Disclaimers:** Non-affiliation statement regarding `sentry.io` (Functional Software, Inc.) in README and SECURITY.md.

### Changed
- **Positioning Copy Recalibration (GAP-008):** Aligned all public documentation and demo scripts to "Calibrated Machine Learning & Evidentiary Email Forensics" (eliminating uncalibrated "AI-Powered" phrasing).
- **CORS Allowlist:** Broadened CORS policy to permit single-origin localhost calls (`:8000`) and customizable origins via `CORS_ORIGINS`.

---

## [1.0.0] - 2026-08-29

### Added
- **SIH 2025 Finalist Release (PS ID 26106):** Certified air-gapped Email Threat Detection, Geolocation & Evidentiary Attribution appliance.
- **Forensic Pipeline:**
  - Deterministic header forensics (`Received`-hop reconstruction, SPF/DKIM/DMARC validation, relay anomaly detection).
  - 47-feature calibrated gradient-boosted classifier (LightGBM/scikit-learn) with macro-F1 0.952 and adversarial evasion resistance.
  - Multi-entity in-memory knowledge graph (`networkx`) for threat campaign attribution.
  - Origin tracing with IP geolocation, Tor exit node detection, and bulletproof ASN identification.
- **Evidentiary Standard (RFC 3227):**
  - Tamper-evident sequential SHA-256 evidence vault and chain of custody.
  - Cryptographically audited destruction records for administrative state resets.
  - Court-admissible PDF forensic dossier export (`ReportLab`).
- **Batch & Corpus Ingestion Gateway:**
  - RFC 822 (`.eml`, `.msg`, raw text) intake.
  - In-memory ZIP archive streaming extractor.
  - CSV dataset importer with D4 degradation contract.
- **Verification Harness:**
  - Automated 19-check end-to-end golden verification harness (`tools/verify_sentry.py`) driving real headless Chromium via Playwright.
  - 72-test unit and integration test suite with 85%+ branch coverage.
  - 12-dimension GAUNTLET audit battery (97.5/100 adjusted composite score).
