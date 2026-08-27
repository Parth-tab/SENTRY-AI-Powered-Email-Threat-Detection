# SENTRY Agent Rules — READ BEFORE RUNNING ANYTHING

## Prime directive
You are executing a bounded auto-fix loop against tools/verify_sentry.py.
The harness report is the sole source of truth about application state.
Your job is to reach exit code 0 by fixing the APP — never by weakening
the harness.

## Process discipline (a prior session was killed violating these)
1. ONE PORT POLICY: backend=8000, frontend=3000. NEVER start servers on new
   ports to dodge a conflict. Free the port: `powershell -File tools/cleanup.ps1`
2. NEVER run uvicorn/vite as foreground commands; never use --reload during
   verification. The harness owns all process lifecycle.
3. ALL browser interaction goes through the harness. No inline Playwright
   scripts, no heredocs, no exceptions.
4. After conversation compaction: restore state from the newest
   verification_report_*.json and git log. Do not re-probe or re-read files
   in a loop.
5. Commit after every fix. An uncommitted fix does not exist.

## The loop
Budget: 1 initial run + 3 fix cycles + 1 final run.
Labels: cycle-1, cycle-2, cycle-3, final.

    E:\SENTRY\.venv\Scripts\python tools/verify_sentry.py --start --label cycle-N

Each cycle, in order:
1. Read verification_report.json (latest run).
2. Triage every FAIL/TIMEOUT against the matrix below.
3. Apply AT MOST ONE substantive app-code fix — the highest-priority
   failing check that is in scope. Marker calibration (see bright line)
   is additionally allowed and does not count as your one fix.
4. Commit: `fix(<check-name>): <what changed>`
5. Re-run with the next label. Repeat until termination condition.

## Triage matrix
| Report evidence | Class | Action |
|---|---|---|
| setup.* FAIL — stack did not boot | Environment | STOP. Paste the report's log tails to the human. Do not attempt fixes. |
| api.seed FAIL but api.emails_list PASSes with items | Benign | Note it, skip it (seed idempotency mismatch; harmless). |
| api.* FAIL — 500s, or 200-with-zero-items | App bug | FIX in backend. Highest priority below setup. |
| ui.dashboard_renders FAIL, screenshot shows blank/error page | App bug | FIX (likely VITE_API_URL wiring, CORS, or base path). |
| ui.* FAIL but screenshot shows correct content on screen | Calibration | Adjust the marker regex in verify_sentry.py to match the real DOM. |
| ui.email_detail_opens FAIL — click does nothing | App bug | Check the emails API response shape FIRST (symptom vs cause). |
| ui.websocket_live_connected FAIL | App bug | FIX VITE_WS_URL wiring. |
| ui.console_clean / ui.no_http_errors FAIL | Hygiene | FIX only when nothing above is failing. Lowest priority. |
| Same check fails 2 consecutive cycles, same detail | Non-convergent | STOP fixing it. If it's the only remaining failure, end the loop. |
| Exit code 2 (watchdog fired) | System | STOP. Report. Never blind-retry. |

Priority when multiple fixes are candidates — fix the most upstream first,
because downstream failures are usually symptoms:
setup > api.* > ui.dashboard > feed/detail > map/graph > websocket > hygiene

## Calibration vs. gaming — the bright line
ALLOWED: changing a marker regex (DASHBOARD_MARKER, DETAIL_MARKER, nav
regexes) or a wait strategy so the check matches the real, visible DOM
shown in that run's screenshot.

FORBIDDEN — any of these means STOP and report instead of continuing:
- Removing, skipping, or commenting out a check.
- Loosening an assertion to accept the broken state (empty feed, ignored
  console errors, dropped canvas requirement).
- Editing app code to serve the harness rather than users.
- Touching screenshots or report files.

If you feel the urge to weaken a check, that is the signal to stop and
escalate — not to get creative.

## Scope limits per cycle
- One substantive fix = edits confined to <= 3 files. If a fix needs more,
  STOP and summarize instead.
- No refactors, no new dependencies, no drive-by changes.
- Never edit anything outside backend/, frontend/, tools/.

## Termination
End the loop when ANY of these fires:
- Exit code 0 -> run once more with `--label final`, then summarize.
- 3 fix cycles exhausted -> run `--label final` anyway, report what remains.
- Early-stop: setup failure, watchdog, non-convergence, or scope breach.

Final summary must include: per-cycle check table (pass/fail), commit list
(hashes + messages), remaining failures with evidence paths (screenshots,
log tails), and one recommended next action for the human.
