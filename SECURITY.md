# Security Policy

## Reporting a Vulnerability
Do NOT open a public issue. To report a security vulnerability, please use **GitHub Security Advisories** on this repository via the "Security" -> "Report a vulnerability" tab.

Please include detailed reproduction steps, proof-of-concept payloads, and environment information. Reports against the synthetic demo corpus are appreciated for test suite expansion.

## Scope & Known Demo-Mode Posture
- This repository's certified default mode is a **demo appliance**: it intentionally
  ships a fixed `SECRET_KEY` for reproducible offline testing, unauthenticated `/metrics`
  and `/health/deep`, and CORS configured for local dev ports (`:3000`, `:8000`).
- **Production Mode Guard:** The system enforces that running in `ENVIRONMENT=production`
  fails fast on startup unless a secure, high-entropy `SECRET_KEY` is injected via environment variables.
- Out of scope: Denial of service on the local demonstration appliance, known dependency advisories already tracked by CI pip-audit, or attacks requiring physical machine access.

## Implemented Hardening Controls
- **Input Sanitization:** Multi-pass `bleach.clean()` neutralization on all email HTML bodies with strict tag allowlist.
- **OWASP Headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 0`, `Strict-Transport-Security`, `Content-Security-Policy`.
- **Rate Limiting:** `SlowAPI` token-bucket rate limiting (120 req/min burst limits).
- **Payload Guard:** 25MB maximum request size limit.
- **RFC 3227 Chain-of-Custody:** Sequential SHA-256 hash chaining with automated tamper verification.
