# SENTRY REST API & WebSocket Reference

Base URL: `http://localhost:8000/api/v1`  
OpenAPI Documentation: `http://localhost:8000/docs`  
OpenAPI Specification Export: [`docs/openapi.json`](openapi.json)

---

## 1. Authentication & Security Posture

- **Demo Appliance Mode (Default):** For frictionless evaluation and reproducibility, endpoints run unauthenticated on local ports (`:8000`).
- **Production Mode:** Enforces `ENVIRONMENT=production` validation, requiring bearer token authorization on API routes and network-isolated metrics interfaces (`:9090`).
- **Standard Enterprise Response Headers:**
  - `X-Correlation-ID`: Unique distributed tracing request identifier.
  - `X-Content-Type-Options: nosniff`
  - `X-Frame-Options: DENY`
  - `X-XSS-Protection: 0`
  - `Strict-Transport-Security: max-age=31536000; includeSubDomains`
  - `Content-Security-Policy: default-src 'self'`

---

## 2. Ingestion & Email Endpoints

### `POST /api/v1/emails/upload`
Universal content-sniffed ingestion gateway. Inspects file payload signatures to dynamically route between:
1. **RFC 822 / 5322 Emails (`.eml`, `.msg`, `.mbox`, extensionless):** Executes complete multi-hop, authentication, origin attribution, and evidence sealing pipeline.
2. **ZIP Archives (`.zip`):** Ingests multi-thousand email archives in-memory with strict Denial-of-Service safety caps (250MB compressed, 500MB uncompressed, 10k entries, 25MB per file).
3. **Tabular Datasets (`.csv`, `.tsv`):** Parses CSV datasets with flexible header mapping, synthesizes deterministic RFC 822 MIME streams, and applies the **D4 Degradation Contract** (quarantines labels, marks missing transport headers as unavailable, zero fabricated hops).
- **Request:** `multipart/form-data` with `file` binary attachment (up to 250MB for batch endpoints).

### `POST /api/v1/emails/batch/archive`
Direct batch ZIP archive ingestion endpoint. Streams entries in-memory with live WebSocket progress broadcasts.

### `POST /api/v1/emails/batch/csv`
Direct tabular dataset ingestion endpoint. Synthesizes RFC 822 MIME streams from `subject`, `body`, `label`, `sender`, `recipient`, `date` columns.

### `POST /api/v1/emails/batch/upload`
Multi-file upload endpoint accepting an array of individual files (`files`) simultaneously.

### `POST /api/v1/emails/raw`
Ingests raw RFC 5322 string content directly.
- **Request Body:** Plain-text raw email content.
- **Response `201 Created`:** Complete `EmailDetailResponse`.

### `GET /api/v1/emails`
Lists analyzed emails with pagination and search filters.
- **Query Parameters:**
  - `limit` (default: 50)
  - `offset` (default: 0)
  - `threat_level` (`CRITICAL`, `HIGH`, `MEDIUM`, `LOW`)
  - `sender` (substring search)

### `GET /api/v1/emails/{email_id}`
Returns full forensic deep-dive including extracted relay hops, SPF/DKIM/DMARC authentication, lookalike brand match, NLP attention tokens, and evidence vault metadata.

### `GET /api/v1/emails/{email_id}/report`
Returns structured JSON forensic intelligence report formatted for SIEM integration.

### `GET /api/v1/emails/{email_id}/report/pdf`
Generates and downloads the official court-admissible PDF forensic report with cryptographic hash signatures and RFC 3227 chain of custody log.

---

## 3. Administration & Reset

### `POST /api/v1/admin/reset-demo`
Gated to `ENVIRONMENT=demo` and authenticated via custom header `X-Sentry-Admin: <ADMIN_TOKEN>`. Non-simple custom header structurally forces CORS preflight (`OPTIONS`), preventing cross-origin drive-by form submissions. Appends an evidentiary destruction audit record (`logs/reset_audit.log`) containing timestamp, trigger, prior record count, and prior chain head hash before database table purging, in-memory graph reset (`CorrelationEngine.reset_graph()`), and re-seeding of the 18 demo email scenarios.

---

## 4. Campaign & Graph Intelligence

### `GET /api/v1/campaigns`
Lists all identified cybercrime campaigns and correlated attack clusters.

### `GET /api/v1/campaigns/{campaign_id}`
Returns granular telemetry, correlated infrastructure IPs, lookalike domains, and target brand profiles for a campaign.

### `GET /api/v1/campaigns/graph/all`
Exports the multi-entity graph network formatted for D3 / React Force Graph visualization (`{ nodes: [...], links: [...] }`).

---

## 5. Evidence Vault & RFC 3227 Verification

### `GET /api/v1/evidence/{email_id}`
Retrieves the immutable evidence vault record and sequence of chained forensic actions.

### `POST /api/v1/evidence/verify/{email_id}`
Cryptographically re-computes and verifies the sequential SHA-256 hash chain to guarantee zero database or evidence tampering.

---

## 6. Machine Learning & Model Transparency

### `GET /api/v1/model/metrics`
Returns formal multi-class model metrics (Accuracy: 0.961 [partially in-sample; Enron/CEAS 2008 baseline distribution], Macro-F1: 0.952, Macro OvR ROC-AUC: 0.988), $5\times 5$ confusion matrix, 10-bin probability calibration curve, and ranked top feature importances.

### `GET /api/v1/model/features`
Returns the 47-dimension feature vector taxonomy extracted by SENTRY.

---

## 7. Observability & Real-Time Telemetry

### `GET /metrics`
Prometheus plain-text telemetry endpoint exposing request rates, error counters, pipeline duration histograms, and active WebSocket connection gauges.

### `GET /health` & `GET /health/deep`
Liveness and deep subsystem readiness probes (Database, Filesystem Storage, ML Classifier, Threat Feeds, Process Uptime).

### `WebSocket /api/v1/dashboard/live`
Real-time bidirectional WebSocket stream broadcasting instant threat alerts (`NEW_ALERT`), parsed email events (`EMAIL_ANALYZED`), and batch ingestion progress (`BATCH_PROGRESS`) to SOC analyst dashboards.
