# SENTRY Security Architecture & Hardening Policy

## 1. Threat Model & Defense-in-Depth

SENTRY is an evidentiary forensic intelligence platform that intentionally ingests untrusted, hostile email artifacts (RFC 5322 payloads, phishing lures, weaponized HTML, spoofed headers, and lookalike domains). To guarantee zero exploitation of the analyzing infrastructure or the SOC analyst viewing the interface, SENTRY enforces a multi-layer defense-in-depth architecture.

---

## 2. Implemented Security Controls

### A. Input Sanitization & XSS Mitigation
- **Bleach HTML Engine**: All incoming email HTML content is parsed through `bleach.clean()` with strict allowlists (`p`, `b`, `i`, `a`, `span`, `table`, etc.).
- **Executable Script & Frame Stripping**: `<script>`, `<object>`, `<embed>`, `<iframe>`, and event handlers (`onerror`, `onload`, `onclick`) are neutralized prior to rendering.
- **Pseudo-Protocol Neutralization**: `javascript:`, `vbscript:`, and data URIs in link targets are stripped, neutralizing DOM-based stored XSS.

### B. HTTP Security Headers (OWASP Compliant)
Every API response from SENTRY includes mandatory security headers:
- `X-Content-Type-Options: nosniff`: Prevents MIME-type sniffing.
- `X-Frame-Options: DENY`: Prevents UI redressing / clickjacking attacks.
- `X-XSS-Protection: 0`: Disables deprecated/vulnerable browser XSS reflection filters in favor of strict CSP (OWASP ASVS guidance).
- `Strict-Transport-Security: max-age=31536000; includeSubDomains`: Mandates HTTPS transport.
- `Referrer-Policy: strict-origin-when-cross-origin`: Restricts cross-origin referrer leakage.
- `Content-Security-Policy`: Disallows untrusted external script sources.

### C. Secret Key & Environment Isolation
- **Demo Appliance Mode:** Uses fixed default keys to ensure deterministic offline execution and automated test reproducibility.
- **Production Mode Guard:** System validates `ENVIRONMENT == "production"` at startup and enforces that `SECRET_KEY` must be a high-entropy cryptographically random string injected via environment variables, failing fast on startup otherwise.

### D. Rate Limiting & Anti-DDoS Protection
- **Token Bucket Limiter (`SlowAPI`)**: Enforces rate limiting per IP address on public endpoints (120 req/min burst limits).
- **Request Size Guard**: Rejects incoming request payloads $>25\text{ MB}$ with `HTTP 413 Request Entity Too Large`.

### E. Cryptographic Evidence Integrity (RFC 3227)
- **Immutable SHA-256 Digest**: Computed upon initial raw byte receipt.
- **Sequential Hash-Chaining**: Every enrichment (Header Forensics, GeoIP, Domain Intel, Threat Feeds, Verdict) is linked sequentially via SHA-256 hashes. Any database tampering immediately invalidates verification checks.

### F. File Upload Validation
- Restricts multipart uploads strictly to RFC 5322 MIME formats (`.eml`, `.msg`, `.mbox`, `.txt`).
- Rejects binary executables (`.exe`, `.dll`, `.sh`, `.elf`) at the perimeter with `HTTP 400 Bad Request`.

---

## 3. Vulnerability Reporting
For any security questions or vulnerability reports, please reach out to `security@sentry-soc.io`.
