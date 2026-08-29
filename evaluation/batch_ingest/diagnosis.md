# SENTRY Batch Ingestion Diagnostic Report (Phase 0)

**Date:** 2026-08-29  
**Session:** BATCH-INGESTION  
**Defect Filed:** [`CORP-001`](file:///E:/SENTRY/evaluation/defects.json)  

---

## 1. Experimental Evidence & Diagnostic Execution

Executed automated diagnostic test suite against the live appliance UI stack:
- **Test Target:** `http://127.0.0.1:3000` backed by `http://127.0.0.1:8000` (ephemeral scratch DB).
- **Execution Script:** [`evaluation/batch_ingest/scripts/diagnose_batch_ingest.py`](file:///E:/SENTRY/evaluation/batch_ingest/scripts/diagnose_batch_ingest.py).
- **Raw Trace Output:** [`evaluation/batch_ingest/diagnosis_raw.json`](file:///E:/SENTRY/evaluation/batch_ingest/diagnosis_raw.json).

### Diagnostic Results Matrix:

| Action | Target Input | Network Status | UI & Dropzone Reaction | Verdict |
| :--- | :--- | :--- | :--- | :--- |
| **(a) Drop 1 Extensionless Ham File** | `00001.1a31cc283af0060967a233d26548a6ce` (real SpamAssassin ham) | HTTP 400 Bad Request | Banner: `Unsupported file type '00001.1a31cc283af0060967a233d26548a6ce'. Supported formats: .eml, .msg, .mbox.` | **REJECTED (H-A Confirmed)** |
| **(b) Multi-select 10 Files** | 10 extensionless ham files | No request dispatched | Browser file picker rejects multiple selection (`<input type="file">` lacks `multiple` attribute). | **BLOCKED (H-B Confirmed)** |
| **(c) Drop Small ZIP Archive** | `small_sample.zip` (3 `.eml` files) | HTTP 400 Bad Request | Banner: `Unsupported file type 'small_sample.zip'. Supported formats: .eml, .msg, .mbox.` | **REJECTED (H-A Confirmed)** |
| **(d) Drop Ling.csv CSV File** | `ling_sample.csv` (subject, body, label) | HTTP 400 Bad Request | Banner: `Unsupported file type 'ling_sample.csv'. Supported formats: .eml, .msg, .mbox.` | **REJECTED (H-A Confirmed)** |

---

## 2. Hypothesis Verdicts & Line-Level Citations

### Hypothesis A: Extension Allowlist Rejection — **CONFIRMED**
1. **Frontend Accept List:**  
   [`frontend/src/components/dashboard/IngestionDropzone.tsx:129`](file:///E:/SENTRY/frontend/src/components/dashboard/IngestionDropzone.tsx#L129):
   ```tsx
   accept=".eml,.msg,.mbox,.txt"
   ```
   Extensionless files, `.csv`, and `.zip` files are filtered out of standard file pickers or flagged on drag-and-drop.
2. **Backend Hard Extension Validation:**  
   [`backend/app/api/v1/emails.py:253-260`](file:///E:/SENTRY/backend/app/api/v1/emails.py#L253-L260):
   ```python
   filename = file.filename or ""
   allowed_exts = (".eml", ".msg", ".mbox", ".txt")
   if not any(filename.lower().endswith(ext) for ext in allowed_exts) and filename != "":
       raise HTTPException(
           status_code=status.HTTP_400_BAD_REQUEST,
           detail=f"Unsupported file type '{filename}'. Supported formats: .eml, .msg, .mbox."
       )
   ```
   Any file lacking one of these 4 extensions (including all 6,951 SpamAssassin ham files, `.zip` archives, and `.csv` datasets) is rejected with HTTP 400 before inspection.

---

### Hypothesis B: No Bulk Ingestion Path — **CONFIRMED**
1. **Frontend Input Element:**  
   [`frontend/src/components/dashboard/IngestionDropzone.tsx:127-134`](file:///E:/SENTRY/frontend/src/components/dashboard/IngestionDropzone.tsx#L127-L134):
   `<input type="file">` does not contain the `multiple` attribute and `handleFileUpload` only reads `e.target.files?.[0]`.
2. **Backend Single-File Handler:**  
   [`backend/app/api/v1/emails.py:244-246`](file:///E:/SENTRY/backend/app/api/v1/emails.py#L244-L246):
   `upload_eml_file` accepts a single `UploadFile = File(...)` and directly returns `EmailDetailResponse` for a single record. There is no batch endpoint or multi-file stream handler.

---

### Hypothesis C: Size Cap Class Discrepancy — **CONFIRMED**
1. **Per-Request Middleware Cap:**  
   [`backend/app/main.py:59-64`](file:///E:/SENTRY/backend/app/main.py#L59-L64):
   ```python
   content_length = request.headers.get("content-length")
   if content_length and int(content_length) > 26_214_400:
       return JSONResponse(status_code=413, content={"detail": "Payload exceeds maximum allowed size of 25MB."})
   ```
   Enforces a strict 25MB cap per HTTP request.
2. **Per-File Ingest Cap:**  
   [`backend/app/api/v1/emails.py:264-265`](file:///E:/SENTRY/backend/app/api/v1/emails.py#L264-L265):
   ```python
   if len(content_bytes) > 20_971_520:
       raise HTTPException(status_code=413, detail="File exceeds maximum size limit of 20MB.")
   ```
3. **Corpus Scale Mismatch:**  
   Real-world email archives (e.g. 6,951 ham files = ~45MB compressed, or enterprise tarballs up to 250MB compressed) will immediately trigger HTTP 413 at the middleware layer unless a dedicated batch archive threshold (up to 250MB compressed / 500MB uncompressed) is supported.

---

### Hypothesis D: MIME / Content Sniffing Rejection — **CONFIRMED**
Neither the frontend nor backend performs content sniffing on the payload bytes. Files are routed or rejected purely based on the filename string suffix.
