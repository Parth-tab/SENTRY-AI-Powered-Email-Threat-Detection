# SENTRY Requirement Traceability Matrix (PS ID 26106)

*AICTE Smart India Hackathon 2025 — Verification & Coverage Matrix*

---

| # | SIH Problem Statement Requirement | SENTRY Implementation & Engine | Automated Test / Verification Evidence | Status |
|---|---|---|---|---|
| **REQ-1** | Multi-hop Email Header Extraction & Analysis | [`HeaderForensicsService`](file:///E:/SENTRY/backend/app/services/header_forensics.py): parses all `Received` headers chronologically, flags RFC 1918 hops, detects timestamp clock-skews. | `tests/test_header_forensics.py` (3 tests), `check_d07_forensic_integrity.py` | :white_check_mark: 100% |
| **REQ-2** | RFC Email Authentication (SPF, DKIM, DMARC) | Full RFC 7208 (SPF), RFC 6376 (DKIM), RFC 7489 (DMARC) evaluation with penalty weighting. | `tests/test_header_forensics.py`, `verification_report.json` | :white_check_mark: 100% |
| **REQ-3** | Geo-Location & Anonymization Engine | [`GeoOriginService`](file:///E:/SENTRY/backend/app/services/geo_origin.py): Earliest reliable public hop extraction, Tor exit node lists, VPN subnets, ASN classification. | `tests/test_geo_origin.py` (2 tests), `check_d06_performance.py` | :white_check_mark: 100% |
| **REQ-4** | Domain Intelligence & Typosquatting Radar | [`DomainIntelService`](file:///E:/SENTRY/backend/app/services/domain_intel.py): Levenshtein distance, Cyrillic homoglyph mappings, IDN Punycode decoding (`xn--...`), brand profiling. | `tests/test_domain_intel.py` (3 tests), `check_d08_ml_rigor.py` | :white_check_mark: 100% |
| **REQ-5** | Content NLP & Linguistic Threat Scoring | [`ContentAnalysisService`](file:///E:/SENTRY/backend/app/services/content_analysis.py): Urgency vectors, authority lures (CEO/CFO), financial keywords, zero-width space stripping, RTLO detection. | `tests/test_content_analysis.py` (2 tests), `check_d08_ml_rigor.py` | :white_check_mark: 100% |
| **REQ-6** | Multi-Signal ML Classification Ensemble | [`ThreatClassifier`](file:///E:/SENTRY/backend/app/ml/classifier.py): 3-Layer ensemble (Deterministic Heuristics + 47-feature Calibrated GBDT + Transformer Attention). | `tests/test_ml_classifier.py` (3 tests), `tests/test_model_metrics.py` | :white_check_mark: 100% |
| **REQ-7** | Evidentiary Integrity & Chain of Custody | [`ReportingService`](file:///E:/SENTRY/backend/app/services/reporting.py): RFC 3227 append-only cryptographic hash chain ($H_0 \to H_n$) with mathematical verification API. | `tests/test_evidence_reporting.py` (2 tests), `check_d07_forensic_integrity.py` | :white_check_mark: 100% |
| **REQ-8** | Court-Admissible Forensic PDF Dossier | ReportLab PDF engine: case ID, cryptographic digests, full header dump, transmission hop table, authentication verdicts. | `tests/test_evidence_reporting.py`, `verification_report.json` | :white_check_mark: 100% |
| **REQ-9** | Campaign Correlation & Knowledge Graph | [`CorrelationEngine`](file:///E:/SENTRY/backend/app/services/correlation_engine.py): Neo4j / NetworkX graph linking emails, IPs, ASNs, domains, and syndicate campaigns. | `tests/test_correlation.py`, `tests/test_correlation_deep.py` | :white_check_mark: 100% |
| **REQ-10**| Real-Time Security Operations (SOC) UI | React / Vite Dark SOC Dashboard: live WebSocket threat stream, Leaflet relay map, interactive canvas graph, split-pane forensic analyzer. | `tools/verify_sentry.py` (15/15 checks), `check_d10_ux_frontend.py` | :white_check_mark: 100% |
| **REQ-11**| Enterprise Security & DDoS Hardening | Bleach HTML sanitization, OWASP headers, SlowAPI rate limiting, 25MB payload guard. | `tests/test_security_hardening.py` (4 tests), `check_d04_security.py` | :white_check_mark: 100% |
| **REQ-12**| Observability & SRE Instrumentation | Prometheus `/metrics` RED exporter, structured correlation IDs (`X-Correlation-ID`), `/health/deep` diagnostics. | `tests/test_observability.py` (4 tests), `check_d11_production.py` | :white_check_mark: 100% |
