# SENTRY Batch Ingestion Architecture & Design Contract (Phase 1)

**Defect ID:** [`CORP-002`](file:///E:/SENTRY/evaluation/defects.json)  
**Related Defects:** [`CORP-001`](file:///E:/SENTRY/evaluation/defects.json), [`FEED-001`](file:///E:/SENTRY/evaluation/defects.json), [`GRAPH-001`](file:///E:/SENTRY/evaluation/defects.json)  

---

## 1. Executive Summary & Problem Formulation

Forensic email ingestion in SENTRY previously relied on strict file-extension matching (`.eml`, `.msg`, `.mbox`, `.txt`) and single-file payload structures. In real-world enterprise incident response and benchmark scenarios (such as SpamAssassin corpus processing with 6,951 extensionless files or Kaggle/Ling-Spam CSV imports), this caused total ingest failure (HTTP 400 Bad Request) and prohibited scalable batch analysis.

This document establishes the formal engineering design for SENTRY's unified batch-ingestion substrate supporting:
1. **Direct RFC 5322 Ingestion (Single / Paste / Extensionless):** Content-sniffed RFC 822 format validation.
2. **Tabular Dataset Ingestion (CSV / TSV):** Ground-truth label isolation, synthesis into verifiable MIME byte payloads, and strict D4 degradation tagging.
3. **Archive Corpus Ingestion (ZIP):** In-memory streaming, corpus-grade denial-of-service guards, and per-entry forensic tracking.
4. **Scale Guards & Observability:** Feed pagination and campaign graph 300-node canvas rendering caps.

```
                    ┌────────────────────────────────────────────────────────┐
                    │            Unified Batch Ingest Front-End              │
                    │  (Dropzone / Multipart API / Admin Ingestion Stream)   │
                    └───────────────────────────┬────────────────────────────┘
                                                │
                                      [ Content Sniffer ]
                        (First 4KB Inspection: RFC 822 vs ZIP vs CSV)
                                                │
                        ┌───────────────────────┼────────────────────────┐
                        ▼                       ▼                        ▼
                [ RFC 822 EML ]           [ ZIP Archive ]          [ CSV Dataset ]
              (Single / Batch List)      (Memory Streamer)       (Row Synthesizer)
                        │                       │                        │
                        │                       │ [Decompress & Iterate] │ [Synthesize RFC 822]
                        │                       │ (Caps: 250MB/10k/25MB) │ (D4 Degradation Tag)
                        │                       ▼                        ▼
                        └──────────────► ┌──────────────────────────────────────┐
                                         │  Shared Forensic Analysis Substrate  │
                                         │   - SHA-256 Byte-Identity Dedupe     │
                                         │   - 3-Layer ML Ensemble & Forensics  │
                                         │   - RFC 3227 Hash-Chain Vaulting     │
                                         │   - Throttled WS Batch Progress      │
                                         └──────────────────┬───────────────────┘
                                                            ▼
                                         ┌──────────────────────────────────────┐
                                         │  Storage, Feeds & Graph Projection   │
                                         │   - Ephemeral / Appliance SQLite     │
                                         │   - Paginated Feed (50/page)         │
                                         │   - Capped Graph Render (300 nodes)  │
                                         └──────────────────────────────────────┘
```

---

## 2. Formal Ingestion Contracts

### A. Content-Sniffing Contract (`sniffer.py`)
1. **Sniffing Rule:** Inspect the first 4,096 bytes ($4\text{ KB}$) of the payload.
   - **RFC 822 Text Grammar:** Payload is classified as RFC 822 if and only if:
     - It contains at least one line matching `^[A-Za-z0-9-]+:\s*.+` prior to encountering the first empty line (`\r\n\r\n` or `\n\n`), AND
     - The first 512 bytes contain no null bytes (`\x00`).
   - **ZIP Archive Grammar:** Payload is classified as ZIP if `zipfile.is_zipfile(BytesIO(first_bytes))` returns `True` or first 4 bytes match the local file header signature (`50 4B 03 04` / `PK\x03\x04`).
   - **CSV Grammar:** Payload is classified as CSV if the first line parses into $\ge 2$ comma- or tab-delimited columns matching known header tokens (`subject`, `body`, `text`, `content`, `message`, `label`, `sender`, `from`, `to`).
2. **Precedence:** Sniffing executes **BEFORE** filename extension checks. Extensions (`.eml`, `.csv`, `.zip`) serve strictly as routing hints and display metadata, never as absolute rejection gates for valid text/archive streams.

### B. Archive Corpus Contract (`archive_ingestion.py`)
1. **In-Memory Streaming:** All archive operations occur in-memory using `zipfile.ZipFile(io.BytesIO(archive_bytes))`. Zero archive bytes are extracted to disk, rendering Path Traversal / Zip-Slip (`../evil.eml`) structurally impossible.
2. **Corpus-Grade Safety Caps (Anti-Bomb & Anti-DoS):**
   - Maximum Compressed Archive Size: $\le 250\text{ MB}$.
   - Maximum Total Uncompressed Size: $\le 500\text{ MB}$ (calculated via `sum(info.file_size)` before decompression).
   - Maximum Total Entries: $\le 10,000$ files.
   - Maximum Per-Entry Uncompressed Size: $\le 25\text{ MB}$.
   - Nested Archives (an entry ending in `.zip` or containing a zip signature): Recorded as `skipped (nested_archive)`, never recursively expanded.
   - Encrypted / Corrupt Entries: Logged as `error (corrupted_or_encrypted)`, allowing remaining archive files to proceed uninterrupted.
3. **Per-Entry Result Tracking:** Every entry yields a deterministic disposition:
   - `ingested`: Successfully processed through forensic ML & vaulted.
   - `duplicate`: Matched identical SHA-256 byte hash in database (zero duplicate row creation).
   - `skipped`: Directory entry, OS artifact (`__MACOSX`, `.DS_Store`), or nested archive.
   - `error`: Failed decompression or malformed header structure (with reason string).

### C. Tabular Dataset (CSV) Contract (`csv_synthesizer.py`)
1. **Header Row Requirement:** First row must specify column names (case-insensitive).
2. **Field Resolution:**
   - `body`: Resolved from `body` | `text` | `content` | `message`.
   - `subject`: Optional; defaults to `[No Subject - CSV Import]`.
   - `sender`: Optional; defaults to `csv-import@unknown.local`.
   - `recipient`: Optional; defaults to `undisclosed-recipients@local`.
   - `date`: Optional; defaults to current ISO 8601 timestamp.
   - `message_id`: Optional; defaults to deterministic UUID `<hash@csv-import>`.
3. **Ground-Truth Label Handling:**
   - Recognized column names: `label`, `target`, `class`, `spam`, `is_phishing`.
   - Positive / Malicious Set: `1`, `true`, `yes`, `spam`, `phish`, `malicious`.
   - Negative / Ham Set: `0`, `false`, `no`, `ham`, `legitimate`, `clean`.
   - Metadata Quarantine: Ground-truth label is stored strictly as `ground_truth_label` in evidence metadata. It **never** influences the ML inference engine.
   - Byte Determinism: Two rows differing *only* in label synthesize identical RFC 822 byte streams, deduplicating to a single artifact under SHA-256 identity.
4. **D4 Degradation Rule:** Synthesized CSV items are flagged with `source_format = "csv"`. Because network headers and relay hops are absent:
   - Content Analysis (NLP, heuristics, keyword scoring) executes fully.
   - Network Authentication (SPF, DKIM, DMARC), Relay Path, Origin Assessment, and GeoIP return explicit `"unavailable — headerless source"` indicators.
   - **Zero Fabricated Hops:** The pipeline never synthesizes fake IP addresses, MX servers, or auth results.
5. **Encoding:** UTF-8 primary with automatic fallback to Latin-1 (ISO-8859-1).

### D. Shared Batch Substrate & Response Schema
Batch endpoints return a standardized job summary:
```json
{
  "status": "completed",
  "source_format": "archive | csv | batch_eml",
  "summary": {
    "total_entries": 6951,
    "ingested": 6951,
    "duplicates": 0,
    "skipped": 0,
    "errors_count": 0,
    "errors": [],
    "warnings": [],
    "encoding": "utf-8",
    "elapsed_seconds": 12.4
  }
}
```
- **Chunked Processing:** Ingest batches in chunks of 100 entries, yielding to the `asyncio` event loop to maintain WebSocket liveness and UI responsiveness.
- **Throttled WebSocket Telemetry:** WebSocket updates emit a single `BATCH_PROGRESS` frame every 100 entries or on completion (preventing UI message floods).

---

## 3. Scale Guards & Latent Defect Remediation

### A. Threat Feed Pagination ([`FEED-001`](file:///E:/SENTRY/evaluation/defects.json))
- **Finding:** Frontend `LiveThreatFeed.tsx` rendered the full email array without pagination controls, while backend defaulted `limit=50`.
- **Remediation:** Implement client-side pagination in `LiveThreatFeed.tsx` with selectable page size (25 / 50 / 100) and Next / Prev controls, displaying `"Page X of Y (Total Z items)"`.

### B. Campaign Graph 300-Node Cap ([`GRAPH-001`](file:///E:/SENTRY/evaluation/defects.json))
- **Finding:** `CampaignNetworkGraph.tsx` rendered uncapped nodes on canvas force-layout ($O(N^2)$ force loop).
- **Remediation:** Enforce a hard ceiling of $300$ active nodes on the canvas:
  ```typescript
  const MAX_GRAPH_NODES = 300;
  const nodesToRender = graphData.nodes.slice(0, MAX_GRAPH_NODES);
  ```
  Render a visible info badge: `"Showing 300 of {total} nodes (capped for browser performance)"`.

---

## 4. Appliance Demo Reset Contract

- **Endpoint:** `POST /api/v1/admin/reset-demo`
- **Security Guard:** Gated on `ENVIRONMENT=demo` or `ALLOW_DEMO_RESET=true`. In production mode, returns HTTP 403 Forbidden.
- **Operation:** Wipes database tables (`emails`, `analysis_results`, `evidence_vault`, `threat_alerts`) and immediately executes `seed_sample_emails()` to restore the pristine 18-email invariant.
