# evaluation/artifacts/

Archived verification receipts from key milestones in the engagement.
Each file is a `verification_report_*.json` produced by `tools/verify_sentry.py`.

| Artifact | What It Proves |
|----------|---------------|
| `verification_report_cold-boot-proof.json` | Air-gap: 15/15 with WSL down, zero daemon ports |
| `verification_report_demo-freeze-v2.json` | **Gate-0 receipt** — the archived proof at `demo-freeze-v2` (f437a19) |
| `verification_report_browserless-proof.json` | Fresh-machine path: Playwright browser auto-downloaded mid-run |
| `verification_report_final.json` | Final stable run before the tag |
| `verification_report_n1-test.json` | Seed idempotency proof (N-1 closure) |
| `verification_report_cycle-1.json` | Early cycle verification |
| `verification_report_phase-*.json` | Phase-by-phase receipts during active development |
| `verification_report_demo-freeze.json` | Original (pre-v2) freeze receipt |
| `verification_report_demo.json` | Verified demo appliance boot receipt produced by `tools/demo_day.ps1` |

The runtime artifact `verification_report.json` (root level) is gitignored — it
is produced by each harness run and is not a historical record.

### Benchmark & Geolocation Provenance Note
Historical IP distributions in corpus benchmarks reflect 2025 MaxMind/GeoLite2 databases evaluated against legacy RFC 5322 headers. The SpamAssassin 6,951 ham corpus serves as an independent out-of-sample resilience test. Full details: [`evaluation/runs/ham_test/README.md`](../runs/ham_test/README.md).

