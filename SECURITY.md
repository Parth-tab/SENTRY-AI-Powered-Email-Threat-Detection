# Security Policy

## Reporting a Vulnerability
Do NOT open a public issue. To report a security vulnerability, please use **GitHub Security Advisories** on this repository via the "Security" -> "Report a vulnerability" tab.

Please include detailed reproduction steps, proof-of-concept payloads, and environment information. Reports against the synthetic demo corpus are appreciated for test suite expansion.

## Scope & Known Demo-Mode Posture
- This repository's certified default mode is a **demo appliance**: it intentionally
  ships a fixed `SECRET_KEY` for reproducible offline testing, unauthenticated `/metrics`
  and `/health/deep`, and CORS configured for local dev ports (`:3000`, `:8000`).
- **Production Mode Guard:** The system enforces that running in `ENVIRONMENT=production`
  fails fast on startup unless secure, high-entropy values for `SECRET_KEY`, `ADMIN_TOKEN`, and `SENTRY_API_TOKEN` are injected via environment variables.
- Out of scope: Denial of service on the local demonstration appliance, known dependency advisories already tracked by CI pip-audit, or attacks requiring physical machine access.

## Implemented Hardening Controls
- **DFIR Operator Bearer Authentication (`SENTRY_API_TOKEN`):** All 8 writable endpoints (`/upload`, `/batch`, `/raw`, `/samples/seed`, `/evidence/verify`, `/admin/reset-demo`) require `Authorization: Bearer <SENTRY_API_TOKEN>`. Constant-time comparison prevents timing attacks, while read-only telemetry (`/emails`, `/dashboard/stats`, `/campaigns`, `/health`) remains open for dashboard polling.
- **Input Sanitization:** Multi-pass `bleach.clean()` neutralization on all email HTML bodies with strict tag allowlist.
- **OWASP Headers:** `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, `X-XSS-Protection: 0`, `Strict-Transport-Security`, `Content-Security-Policy`.
- **Rate Limiting:** `SlowAPI` token-bucket rate limiting (120 req/min burst limits).
- **Payload Guard:** 25MB maximum request size limit.
- **RFC 3227 Chain-of-Custody:** Sequential SHA-256 hash chaining with automated tamper verification.
- **Administrative Endpoint Hardening (`/api/v1/admin/reset-demo`):** Privileged state reset requires an explicit `X-Sentry-Admin` header matching `ADMIN_TOKEN` alongside the operator bearer token. Non-safelisted custom headers trigger browser CORS preflights (`OPTIONS`), structurally neutralizing cross-origin drive-by form-POST exploits. All destruction events append a cryptographically attributed audit record to `logs/reset_audit.log` before database purging.
- **RFC Special-Use & Reserved Network Guard (RFC 5737 / 1918 / 6598):** Pre-compiled subnet boundary guarding 22 private, documentation, and CGNAT IP ranges (e.g. `192.0.2.0/24`, `198.51.100.0/24`, `100.64.0.0/10`) against external threat-intelligence feed or geolocation API leakage, guaranteeing internal IP addresses are never queried externally.
- **Incident Response Self-DoS Refusal:** When internal domain spoofing occurs (`from_domain == recipient_domain`), the IR recommendation engine structurally refuses to emit self-destructive domain blocks, routing instead to DNS DMARC `p=reject`, perimeter SEG anti-spoof drops, and external `Reply-To` channel blocks.
- **Authentication Severity Floor & Algorithmic Transparency:** Enforces an immutable 0.85 severity floor on hard DMARC+SPF cryptographic authentication failure while preserving underlying model scores (`score_pre_floor`) across all API payloads and PDF forensic dossiers.
- **Evidentiary Monospace Typography:** Full 64-character SHA-256 digests rendered in dedicated 220pt columns using Courier monospace to prevent optical transcription distortion in legal proceedings.
- **Machine-Verified Fact Gating:** Quantitative security claims and defect ledgers are verified continuously in CI via `tools/validate_facts.py` against `docs/PROJECT_FACTS.md`.

## Trademark & Non-Affiliation Notice
SENTRY (this repository) is an independent open-source cybersecurity research and forensic investigation platform. It is not affiliated with, sponsored by, or endorsed by Sentry / sentry.io (Functional Software, Inc.). Full project rebranding is a documented commercialization trigger.
