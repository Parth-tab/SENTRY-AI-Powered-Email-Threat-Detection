# SENTRY Architecture & System Design Blueprint

*AICTE Smart India Hackathon 2025 — Problem Statement ID 26106*  
*AI-Powered Email Threat Detection, GeoLocation & Forensic Intelligence Platform*

---

## 1. System Overview

SENTRY is an evidentiary-grade cyber forensic intelligence platform that treats every email communication as a forensic crime scene. Rather than relying solely on superficial body NLP or isolated header checks, SENTRY reconstructs the full physical transmission path, analyzes multi-hop network infrastructure, calculates lookalike brand domain entropy, and correlates threats across global cybercrime campaigns.

```mermaid
flowchart TD
    A[Raw Ingestion\nRFC 5322 EML / MSG / MBOX] --> B[Ingestion & Vault Engine\nSHA-256 Digest + Bleach Sanitization]
    B --> C[RFC 3227 Hash Chain\nGenesis Block Creation]
    
    subgraph "Forensic Deep Analysis Pipeline"
        C --> D1[Header Forensics Engine\nReceived Hop Chronology, SPF/DKIM/DMARC]
        C --> D2[Geo-Origin Engine\nEarliest Hop Trace, Tor/VPN/ASN Fingerprint]
        C --> D3[Domain Intelligence\nLevenshtein, Punycode, Homoglyphs]
        C --> D4[Content NLP & Attention\nUrgency, Credential & Financial Vectors]
        C --> D5[Threat Intel Feeds\nURLhaus, ThreatFox, OpenPhish]
    end

    D1 --> E[47-Dimension Feature Vector]
    D2 --> E
    D3 --> E
    D4 --> E
    D5 --> E

    subgraph "3-Layer ML Classifier Triangulation"
        E --> F1[Layer 1: Deterministic Heuristics]
        E --> F2[Layer 2: Calibrated XGBoost GBDT]
        E --> F3[Layer 3: Transformer Attention Score]
        F1 --> G[Ensemble Blending Engine]
        F2 --> G
        F3 --> G
    end

    G --> H[Threat Verdict\nScore: 0.0-1.0 | Level: CRITICAL/HIGH/MED/LOW]
    H --> I[Correlation & Knowledge Graph\nNeo4j & NetworkX Campaign Clustering]
    H --> J[Court-Admissible PDF Report\nReportLab RFC 3227 Cryptographic Proof]
    H --> K[Real-Time SOC Broadcast\nWebSocket Token-Bucket Telemetry]
```

---

## 2. Core Architectural Pillars

### A. Immutable Evidentiary Chain of Custody (RFC 3227)
Every analyzed artifact in SENTRY is cryptographically sealed from the millisecond of ingestion:
1. **Genesis Record ($H_0$):** `SHA256(Raw EML Bytes)` stored in immutable disk vault (`evidence_vault/`).
2. **Enrichment Logging ($H_n$):** Each analysis phase (Header Reconstruction, GeoIP, Domain Intel, Threat Intel, ML Verdict) creates an entry:
   $$H_n = \text{SHA256}(H_{n-1} \parallel \text{Action} \parallel \text{Actor} \parallel \text{Timestamp} \parallel \text{Details})$$
3. **Chain Verification:** Any offline modification or database tampering invalidates the hash chain, triggering instant tamper alerts.

### B. 3-Layer Triangulated ML Ensemble
- **Layer 1 (Deterministic Heuristic Rules):** 100% precision perimeter filters for known Tor exit nodes, SPF/DKIM hard fails, lookalike bank domains, and active IOC matches.
- **Layer 2 (Calibrated Gradient Boosted Trees):** 47 continuous and categorical dimensions (Linguistic, Structural, Header Forensics, Authentication, Domain Intel, Geo-Origin).
- **Layer 3 (Transformer Linguistic Attention):** Contextual intent extraction focusing on urgency manipulation, credential harvesting lures, and BEC wire transfer syntax.

### C. Multi-Entity Campaign Knowledge Graph
SENTRY correlates disparate emails into unified threat campaigns using graph clustering:
- **Nodes:** `Email`, `Domain`, `IPAddress`, `Infrastructure (ASN)`, `Campaign`, `BrandTarget`.
- **Edges:** `SENT_FROM`, `HOSTED_BY`, `LOOKALIKE_OF`, `PART_OF`, `USES_INFRASTRUCTURE`.

---

## 3. Database & Storage Architecture

| Store | Technology | Role |
| :--- | :--- | :--- |
| **Primary Relational** | PostgreSQL 16 / SQLite | Structured email metadata, forensic results, analysis timelines, alerts |
| **Graph Database** | Neo4j 5.18 / NetworkX | Multi-entity campaign link analysis and infrastructure correlation |
| **Cache & Real-Time**| Redis 7 / In-Memory | Live rate-limiting token buckets, threat feed caches, Celery broker |
| **Evidence Vault** | Filesystem (Immutable) | Raw `.eml` payloads keyed by their SHA-256 digest |

---

## 4. Security & Observability

- **Input Sanitization:** Multi-pass `bleach.clean()` neutralization for all email HTML bodies.
- **Rate Limiting:** `SlowAPI` token-bucket throttling on public API endpoints.
- **HTTP Security Headers:** Complete OWASP response header suite (`CSP`, `HSTS`, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`).
- **Telemetry:** Native Prometheus `/metrics` endpoint exposing RED counters, duration histograms, and WebSocket gauges.
- **Diagnostics:** Deep health check `/health/deep` monitoring database, filesystem storage, ML engine, and threat feeds.
