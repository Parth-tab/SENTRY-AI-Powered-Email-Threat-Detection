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
   `verification_report_demo-freeze-v2.json`). Do not add daemon dependencies
   to the live path without an `eval-change:` commit and human sign-off.

## Change protocol
1. Small scope: <= 3 files per logical change, conventional commits
   (`fix`/`feat`/`docs`/`eval-change`), one commit per change.
2. Every fix references what it closes: a defect ID from
   `evaluation/defects.json`, an issue number, or a check name from the harness.
   A commit that improves behavior without a reference is suspect.
3. Before commit: pytest (`backend/tests`) AND `tools/verify_sentry.py --start`
   must pass. CI runs both plus the full GAUNTLET battery — do not push red.
4. Fix the app, never the test. Battery/evaluation changes require an
   `eval-change:` commit with written rationale, and may only be made MORE
   strict, never less.
5. State lives on disk (`evaluation/defects.json`, `verification_report_*.json`,
   `git log`), not in conversation memory. After compaction, restore context
   from disk — do not re-probe the running system in loops.

## Sealed release
`demo-freeze-v2` (`01f8fb4`) is the certified SIH 2025 release with a full
archived Gate-0. Treat it as immutable history. Post-release work happens on
`main`: normal protocol applies, and if you touch the forensic hash-chain or
ingestion path, run the FULL battery, not just the golden harness.
