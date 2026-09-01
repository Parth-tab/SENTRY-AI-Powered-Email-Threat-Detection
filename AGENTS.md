# AGENTS.md — Machine Operating Rules for This Repository

Human contributors: see CONTRIBUTING.md. This file governs AI agents working
in this repo. It exists because this project was built agent-first, and its
verification discipline is the reason the codebase is trustworthy. Do not
work around it.

## Prime directive
The verification harness (`tools/verify_sentry.py`) is the sole source of truth
about whether this system works. Your memory is not. Port probes are not.
After ANY change: run the harness before drawing any conclusion.

## Boot discipline
1. **ONE PORT POLICY:** backend=8000, frontend=3000. Never start servers on new
   ports to dodge a conflict — free the port (`powershell -File tools/cleanup.ps1` on Windows;
   kill by PID elsewhere).
2. Never run uvicorn/vite as a foreground blocking command from an agent
   session. Never use `--reload` during verification.
3. All browser interaction goes through the harness (Playwright is wired
   into it). No inline browser scripts.
4. The certified runtime is the air-gapped appliance: async SQLite +
   in-memory graph. Redis/Neo4j/Celery code paths exist for the documented
   scale-out topology but are NOT in the live path (proven by
   `evaluation/artifacts/verification_report_demo-freeze-v2.json`). Do not add daemon dependencies
   to the live path without an `eval-change:` commit and human sign-off.

## Change protocol
1. Small scope: <= 3 files per logical change, conventional commits
   (`fix`/`feat`/`docs`/`eval-change`), one commit per change.
2. Every fix references what it closes: a defect ID from
   `evaluation/defects.json`, an issue number, or a check name from the harness.
   A commit that improves behavior without a reference is suspect.
3. Protected Branch Protocol: `main` is protected; all work lands via branches + PRs; required checks must be green; the harness runs locally before any PR.
4. Before PR: pytest (`backend/tests`), `tools/verify_sentry.py --start`, and
   `tools/validate_facts.py` must pass. CI runs all three plus the full GAUNTLET battery — do not push red.
5. Fix the app, never the test. Battery/evaluation changes require an
   `eval-change:` commit with written rationale, and may only be made MORE
   strict, never less.
6. State lives on disk (`evaluation/defects.json`, `evaluation/artifacts/verification_report_*.json`,
   `git log`), not in conversation memory. After compaction, restore context
   from disk — do not re-probe the running system in loops.

## Machine Operating Laws

1. **LAW A (Claim-Derivation Law):** Every quantitative claim (test counts, gate counts, defect counts, versions, metrics) must be derived by command during the session. `docs/PROJECT_FACTS.md` is the sole machine-verified numeric source of truth. No claims from memory.
2. **LAW B (Conditions Ledger Protocol):** Every phase and session report must open with a status-tracked conditions ledger (CLOSED/OPEN per item).
3. **LAW C (Link Integrity & Portability Law):** All links within committed markdown must resolve repo-relative. Absolute `file:///` URIs are forbidden. Dead links are tracked as defects (`DOC-xxx`). The validator link stage is advisory during Phase 2 and strictly gated (`--strict-links`) upon `DOC-003` closure.
4. **LAW D (Immutable History Law):** Past `CHANGELOG.md` entries, released version notes, and certified review artifacts are immutable history. Historical claims must be tagged `[derived-historical]` and never rewritten.
5. **Caption Honesty & Pixel Fidelity Law:** All screenshots in `docs/assets/tour/` and documentation must match the live rendered pixels of the application via `tools/capture_tour.py`.
6. **3x Flake Bar Protocol:** Stochastic, force-directed, or visual layout features (e.g. Campaign Network Graph force physics) must demonstrate 3 consecutive green golden harness runs (`tools/verify_sentry.py --start`) before final panel clearance.

## Sealed release
`demo-freeze-v2` (`01f8fb4`) is the certified SIH 2025 release with a full
archived Gate-0. Treat it as immutable history. Post-release work happens on
`main`: normal protocol applies, and if you touch the forensic hash-chain or
ingestion path, run the FULL battery, not just the golden harness.
