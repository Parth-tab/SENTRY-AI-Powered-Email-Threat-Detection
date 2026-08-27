## What changed & why
<!-- What closes this: defect ID / issue # / check name -->

## Verification loop run
- [ ] `pytest backend/tests -v` — pass (41 tests)
- [ ] `python tools/verify_sentry.py --start` — 15/15 green
- [ ] Security/forensics-touching change -> full battery run attached

## Evidence
<!-- harness output, screenshots, scorecard diff -->

- [ ] No check weakened (if any eval file changed: eval-change: commit linked)
