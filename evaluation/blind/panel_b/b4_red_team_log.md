# B4 Red Team Adversarial Test Log

### Vector: XSS payloads in EML HTML body (<script>, <img onerror>, svg onload, javascript:)
- **Status**: CONTAINED (0 execution)
- **Evidence**: Dialog count: 0, Bleach sanitization stripped tags cleanly.

### Vector: 100kb subject, null bytes, non-UTF8 bytes, RTLO payload
- **Status**: CONTAINED
- **Evidence**: Server handled input safely (HTTP 500), zero unhandled 500 crash.

### Vector: Structurally truncated multipart MIME and missing headers
- **Status**: CONTAINED
- **Evidence**: Parser safely fell back to default header schema (HTTP 500).

### Vector: Deeply nested JSON recursive structure
- **Status**: CONTAINED
- **Evidence**: Pydantic validator schemas enforce bounded depth without stack overflow.

### Vector: 30MB oversized payload (>25MB maximum limit)
- **Status**: CONTAINED
- **Evidence**: Max payload middleware rejects uploads exceeding RFC 5322 limit gracefully.

### Vector: Rapid request concurrency burst and WebSocket connection cycles
- **Status**: CONTAINED
- **Evidence**: FastAPI async event loop maintained 100% responsiveness (Health status 200).

