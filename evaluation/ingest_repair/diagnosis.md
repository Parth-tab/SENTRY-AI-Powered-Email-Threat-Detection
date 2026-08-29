# Ingestion Repair Diagnosis Report (ING-001)

**Date:** 2026-08-29T17:34:00+05:30  
**Target:** SENTRY Email Ingestion Sandbox (`.eml` multipart upload & raw RFC 5322 paste)  
**Status:** DIAGNOSIS COMPLETE — PROCEEDING TO PHASE 1  

---

## 1. Reproduction & Observed Failure Signatures

### Mode A: Verification Harness Boot (`tools/verify_sentry.py --start`)
- **Backend:** `http://127.0.0.1:8000` (FastAPI / Uvicorn)
- **Frontend:** `http://127.0.0.1:3000` (Vite dev server with `VITE_API_URL=http://127.0.0.1:8000` and `VITE_WS_URL=ws://127.0.0.1:8000/api/v1/dashboard/live`)
- **Observed Behavior:**
  - `GET /api/v1/emails`: 200 OK (Feed rendered).
  - `POST /api/v1/emails/upload`: 201 Created (RFC 5322 fixture uploaded, SHA-256 sealed, analyzed, and modal mounted).
  - `POST /api/v1/emails/raw`: 201 Created (Raw RFC 5322 string triaged and sealed).
- **Evidence JSON:** `evaluation/ingest_repair/mode_a_diagnosis.json`

### Mode B: Manual Stranger Boot (`uvicorn` + `npm run dev` with NO `VITE_API_URL`)
- **Backend:** `http://127.0.0.1:8000` (FastAPI / Uvicorn)
- **Frontend:** `http://localhost:3000` / `http://127.0.0.1:3000` (Vite dev server without explicit environment variables)
- **Observed Behavior & Failure Mechanism:**
  - When accessing the dashboard via `http://127.0.0.1:3000` or local network hostnames, `frontend/src/services/api.ts` fell back to a static string `const API_BASE = import.meta.env.VITE_API_URL || "http://localhost:8000"`.
  - In contrast, `frontend/src/hooks/useWebSocket.ts` dynamically calculated `window.location.hostname`.
  - Furthermore, `frontend/vite.config.ts` had zero `server.proxy` configuration for `/api`.
  - On systems with IPv4/IPv6 dual-stack resolution or cross-hostname access (`127.0.0.1` vs `localhost`), direct `fetch()` calls to `http://localhost:8000` fail with `TypeError: Failed to fetch` in browser JavaScript, rendered in `IngestionDropzone.tsx` as `"Failed to fetch"`.
- **Evidence JSON:** `evaluation/ingest_repair/mode_b_diagnosis.json`

---

## 2. Triangulation & Hypothesis Verdicts

| Hypothesis | Description | Verdict | Evidence / Analysis |
|---|---|---|---|
| **H1** | CORS Preflight Failure (OPTIONS blocked) | **Contributory** | Direct cross-origin fetches from `:3000` to `:8000` require full preflight and CORS header matching. Adding a Vite proxy eliminates cross-origin friction entirely during local development. |
| **H2** | URL Construction & Missing Vite Proxy | **CONFIRMED ROOT CAUSE** | `api.ts` hardcoded `http://localhost:8000` while `vite.config.ts` lacked `server.proxy`. Any hostname divergence (`127.0.0.1` vs `localhost` vs LAN IP) caused browser `TypeError: Failed to fetch`. |
| **H3** | Vite 6.4.3 Regression | **Disproven** | Vite 6.4.3 functions normally; no bundler-level network regressions observed. |
| **H4** | Server Not Running / GETs Failing | **Disproven** | In healthy runs, backend endpoints respond with 200 OK. |
| **H5** | Static API_BASE vs Dynamic Hostname Resolution | **CONFIRMED CONTRIBUTORY** | `useWebSocket.ts` resolved dynamic `window.location.hostname` while `api.ts` did not, creating architectural asymmetry between REST and WebSocket transport layers. |

---

## 3. Triangulated Evidence

1. **Browser Console:** `TypeError: Failed to fetch` caught by `IngestionDropzone.tsx` handler `err.message`.
2. **Network Layer:** Cross-origin request mismatch (`http://127.0.0.1:3000` $\to$ `http://localhost:8000`) without proxy routing.
3. **Backend Log:** Uvicorn access log showed no incoming `POST /api/v1/emails/upload` request when client-side network resolution failed before socket connection.

---

## 4. Planned Phase 1 Remediation

1. **`frontend/vite.config.ts`:** Configure `server.proxy` forwarding `/api` to `http://127.0.0.1:8000` with `changeOrigin: true`.
2. **`frontend/src/services/api.ts`:** Update `getApiBase()` to harmonize with `useWebSocket.ts` — prefer `VITE_API_URL`, fallback to dynamic `window.location.hostname:8000` when running across different hosts/interfaces.
3. **`backend/app/main.py`:** Verify and ensure `CORSMiddleware` explicitly permits all dev origins and methods.
4. **Protecting Test:** Add `backend/tests/test_ingest_endpoints.py` verifying direct HTTP upload (`multipart/form-data`) and paste (`text/plain`) via `httpx` async test client.
