# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Auditor's Annex & Errata (Phase 0):** Formalized viability audit corrections, SY-1 scale-out analysis errata, memory profiling notes, and market math reconciliations.
- **MaxMind GeoLite2 EULA Attribution:** Explicit attribution notice and direct links on UI footer, PDF dossiers, and README.
- **Trademark & Brand Disclaimers:** Non-affiliation statement regarding `sentry.io` (Functional Software, Inc.) in README and SECURITY.md.

### Changed
- **Positioning Copy Recalibration (GAP-008):** Aligned all public documentation and demo scripts to "Calibrated Machine Learning & Evidentiary Email Forensics" (eliminating uncalibrated "AI-Powered" phrasing).

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
