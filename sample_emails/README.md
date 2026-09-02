# SENTRY Curated Demonstration Corpus

This directory contains 18 curated demonstration email files (`.eml`) spanning 3 realistic cybercrime campaign patterns for live demonstration and forensic evaluation.

## Important Disclaimer

**All email files in this corpus are completely synthetic.**
- All sender identities, victim organizations, bank names, domain references, executive names, and infrastructure identifiers (ASNs, IP ranges, Tor exit relays) were authored solely for educational, research, and live demonstration purposes.
- These files do not represent real individuals, live private communications, or active malicious operations.
- The samples serve as verified benchmark inputs for validating SENTRY's multi-hop header parser, domain lookalike entropy engine, RFC 3227 evidentiary hash chain, and campaign graph correlation.

## Campaign Breakdown (18 Emails)

1. **Operation GhostRelay (CMP-2024-0034) ? 8 Emails:**
   - Banking KYC update & fraud warning lures targeting Indian financial institutions.
   - Network transmission routes through bulletproof Tor exit node relay infrastructure (`185.220.101.34` under AS205100).
2. **Titan Executive BEC Syndicate (CMP-2024-0012) — 5 Emails:**
   - C-suite impersonation demanding out-of-band wire transfers, confidential escrow deposits, and payroll direct-deposit rerouting.
   - Originates from synthetic RFC 5737 TEST-NET-2 documentation addresses (`198.51.100.42`, `198.51.100.88`, `198.51.100.99`), which attribute honestly to `Reserved / Internal Test IP`.
3. **FinPhish Global Cloud Harvester (CMP-2024-0089) — 5 Emails:**
   - Cross-tenant DocuSign NDA signature requests, Microsoft 365 password expiry notifications, Google Workspace OAuth permission consent phishing, and RTLO executable attachments.
   - Uses reverse-proxy CDN shields (`104.21.45.12`, `172.67.182.90`).
